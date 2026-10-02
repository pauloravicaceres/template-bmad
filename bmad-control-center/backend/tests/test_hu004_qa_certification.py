import asyncio
import os
import time
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from main import app
from core.config import settings
from services.git_service import GitService, GitRepoNotFoundError, git_service
from models.git import (
    GitStatusResponse,
    GitCommitListResponse,
    GitBranchListResponse,
    GitWorkingTree,
)


@pytest.fixture
def qa_client():
    """Cliente de pruebas para endpoints HTTP de telemetría Git."""
    return TestClient(app)


class TestHU004GitStatusTelemetriaCertification:
    """
    Certificación de Criterios de Aceptación para estado del repositorio Git y working directory (SC-01, SC-03, SC-04 / CB-01, CB-02, CB-03).
    """

    def test_GetGitStatus_ConRepositorioValido_DebeRetornarEstadoCompletoYTelemetriaSoloLectura(self, qa_client):
        # Arrange
        endpoint = "/api/v1/git/status"

        # Act
        response = qa_client.get(endpoint)

        # Assert
        assert response.status_code == 200, f"Error en endpoint status: {response.text}"
        data = response.json()
        assert "current_branch" in data
        assert isinstance(data["current_branch"], (str, type(None)))
        assert len(data["head_commit_hash"]) == 40
        assert len(data["head_commit_short"]) == 7
        assert data["head_commit_hash"].startswith(data["head_commit_short"])
        assert "head_commit_message" in data
        assert "head_commit_author" in data
        assert data["is_syncing"] is False
        assert isinstance(data["is_detached"], bool)
        assert isinstance(data["is_conflicted"], bool)

        # Verificación de estructura del Working Tree tripartito (SC-01)
        working_tree = data["working_tree"]
        assert isinstance(working_tree["staged"], list)
        assert isinstance(working_tree["unstaged"], list)
        assert isinstance(working_tree["untracked"], list)
        assert isinstance(working_tree["conflicts"], list)
        assert data["staged_count"] == len(working_tree["staged"])
        assert data["unstaged_count"] == len(working_tree["unstaged"])
        assert data["untracked_count"] == len(working_tree["untracked"])
        assert data["total_modified_files"] >= 0

    @pytest.mark.asyncio
    async def test_GetGitStatus_BajoContencionPorIndexLock_DebeRetornarSnapshotCacheadoConIsSyncingTrueSinFallar(self, qa_client):
        # Arrange: Sembrar snapshot inicial válido en memoria
        seed_response = qa_client.get("/api/v1/git/status")
        assert seed_response.status_code == 200
        seed_data = seed_response.json()
        assert seed_data["is_syncing"] is False

        lock_path = settings.WORKSPACE_ROOT / ".git" / "index.lock"
        try:
            # Crear lockfile simulando transacción concurrente
            lock_path.write_text("lock-simulation-bmad", encoding="utf-8")

            # Act: Solicitar estado mientras persiste el bloqueo
            lock_response = qa_client.get("/api/v1/git/status")

            # Assert: Resiliencia (0% 5xx, HTTP 200 con is_syncing=True)
            assert lock_response.status_code == 200
            lock_data = lock_response.json()
            assert lock_data["is_syncing"] is True
            assert lock_data["current_branch"] == seed_data["current_branch"]
            assert lock_data["head_commit_hash"] == seed_data["head_commit_hash"]
        finally:
            if lock_path.exists():
                lock_path.unlink()

        # Assert de recuperación: Tras liberar el lock, is_syncing debe volver a False
        recovery_response = qa_client.get("/api/v1/git/status")
        assert recovery_response.status_code == 200
        recovery_data = recovery_response.json()
        assert recovery_data["is_syncing"] is False

    @pytest.mark.asyncio
    async def test_GetGitStatus_EnDirectorioSinRepositorioGit_DebeRetornar404ConCodigoGitRepoNotFound(self, tmp_path):
        # Arrange: Crear servicio apuntando a directorio vacío (sin .git/)
        empty_service = GitService(workspace_root=tmp_path)

        # Act & Assert
        with pytest.raises(GitRepoNotFoundError) as exc_info:
            await empty_service.get_git_status()

        assert exc_info.value.status_code == 404
        assert exc_info.value.error_code == "GIT_REPO_NOT_FOUND"
        assert "git init" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_GetGitStatus_CuandoHeadEstaEnEstadoDetached_DebeDetectarEstadoDetachedYBranchNone(self):
        # Arrange: Simular salida de git status con branch.head (detached)
        simulated_porcelain = (
            "# branch.oid 0123456789abcdef0123456789abcdef01234567\n"
            "# branch.head (detached)\n"
            "? uncommitted.txt\n"
        )
        simulated_log = (
            "0123456789abcdef0123456789abcdef01234567\x1f0123456\x1fAgent\x1f2026-10-01T12:00:00Z\x1fDetached commit"
        )

        service = GitService(workspace_root=settings.WORKSPACE_ROOT)

        with patch.object(service, "_run_git_command") as mock_git:
            mock_git.side_effect = [
                (simulated_porcelain, "", 0),  # status --porcelain=v2
                (simulated_log, "", 0),  # log
            ]

            # Act
            status = await service.get_git_status()

            # Assert
            assert status.is_detached is True
            assert status.current_branch is None
            assert status.head_commit_hash == "0123456789abcdef0123456789abcdef01234567"
            assert status.head_commit_short == "0123456"

    @pytest.mark.asyncio
    async def test_GetGitStatus_ConArchivosEnConflicto_DebeDetectarIsConflictedTrueYClasificarEnWorkingTree(self):
        # Arrange: Simular salida porcelain v2 con entrada tipo 'u' (unmerged conflict)
        simulated_porcelain = (
            "# branch.oid 0123456789abcdef0123456789abcdef01234567\n"
            "# branch.head main\n"
            "u UU N... 100644 100644 100644 100644 hash1 hash2 hash3 files/conflict_file.md\n"
        )
        simulated_log = (
            "0123456789abcdef0123456789abcdef01234567\x1f0123456\x1fAgent\x1f2026-10-01T12:00:00Z\x1fConflict commit"
        )

        service = GitService(workspace_root=settings.WORKSPACE_ROOT)

        with patch.object(service, "_run_git_command") as mock_git:
            mock_git.side_effect = [
                (simulated_porcelain, "", 0),
                (simulated_log, "", 0),
            ]

            # Act
            status = await service.get_git_status()

            # Assert
            assert status.is_conflicted is True
            assert len(status.working_tree.conflicts) == 1
            assert status.working_tree.conflicts[0].path == "files/conflict_file.md"
            assert status.working_tree.conflicts[0].category == "conflict"


class TestHU004GitCommitsHistorialCertification:
    """
    Certificación de Criterios de Aceptación para historial de commits, paginación y SLA < 300ms (SC-02, SC-05 / CB-04, CB-05).
    """

    def test_GetGitCommits_ConParametrosPorDefecto_DebeRetornarHasta50CommitsConSlaMenorA300ms(self, qa_client):
        # Arrange
        endpoint = "/api/v1/git/commits"

        # Act
        start_time = time.perf_counter()
        response = qa_client.get(endpoint)
        client_duration_ms = (time.perf_counter() - start_time) * 1000

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "commits" in data
        assert len(data["commits"]) <= 50
        assert data["limit"] == 50
        assert data["offset"] == 0
        assert data["total_count"] > 0
        assert isinstance(data["has_more"], bool)

        # SLA de rendimiento: ejecución backend < 300ms (SC-05)
        assert data["execution_time_ms"] < 300, f"Backend superó SLA de 300ms: {data['execution_time_ms']}ms"

        # Inspección del primer commit retornado
        if data["commits"]:
            first_commit = data["commits"][0]
            assert len(first_commit["commit_hash"]) == 40
            assert len(first_commit["short_hash"]) == 7
            assert first_commit["commit_hash"].startswith(first_commit["short_hash"])
            assert "author_name" in first_commit
            assert "author_email" in first_commit
            assert "message" in first_commit
            assert "files" in first_commit
            assert isinstance(first_commit["files"], list)

    def test_GetGitCommits_ConPaginacionValida_DebeRespetarLimitYOffsetRetornandoSubconjuntoCorrecto(self, qa_client):
        # Arrange: Solicitar primeros 2 commits y luego el siguiente con offset 1
        page1_res = qa_client.get("/api/v1/git/commits?limit=2&offset=0")
        assert page1_res.status_code == 200
        page1 = page1_res.json()

        # Act: Solicitar segunda página con offset=1, limit=1
        page2_res = qa_client.get("/api/v1/git/commits?limit=1&offset=1")
        assert page2_res.status_code == 200
        page2 = page2_res.json()

        # Assert: Si existen al menos 2 commits, el commit en offset 1 debe coincidir
        if len(page1["commits"]) >= 2:
            assert page2["commits"][0]["commit_hash"] == page1["commits"][1]["commit_hash"]
            assert page2["offset"] == 1
            assert page2["limit"] == 1

    def test_GetGitCommits_ConLimitInvalidoMenorAUno_DebeRetornarHTTP422(self, qa_client):
        # Arrange & Act: Probar limit 0 y negativo (Sad Path 1)
        res_zero = qa_client.get("/api/v1/git/commits?limit=0")
        res_neg = qa_client.get("/api/v1/git/commits?limit=-5")

        # Assert
        assert res_zero.status_code == 422
        assert res_neg.status_code == 422

    def test_GetGitCommits_ConOffsetNegativo_DebeRetornarHTTP422(self, qa_client):
        # Arrange & Act: Probar offset negativo (Sad Path 2)
        res = qa_client.get("/api/v1/git/commits?offset=-1")

        # Assert
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_GetGitCommits_EnDirectorioSinGit_DebeLanzarGitRepoNotFound404(self, tmp_path):
        # Arrange
        empty_service = GitService(workspace_root=tmp_path)

        # Act & Assert
        with pytest.raises(GitRepoNotFoundError) as exc_info:
            await empty_service.get_commits()

        assert exc_info.value.status_code == 404
        assert exc_info.value.error_code == "GIT_REPO_NOT_FOUND"


class TestHU004GitBranchesCertification:
    """
    Certificación de Criterios de Aceptación para listado de ramas y rama activa (SC-01 / CB-02).
    """

    def test_GetGitBranches_ConRepositorioValido_DebeListarRamasIdentificandoRamaActiva(self, qa_client):
        # Arrange
        endpoint = "/api/v1/git/branches"

        # Act
        response = qa_client.get(endpoint)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "branches" in data
        assert "current_branch" in data
        assert data["total_branches"] >= 1
        assert len(data["branches"]) == data["total_branches"]

        # Debe existir exactamente una rama activa marcada como is_current
        current_branches = [b for b in data["branches"] if b["is_current"]]
        assert len(current_branches) == 1
        assert current_branches[0]["name"] == data["current_branch"]
        assert len(current_branches[0]["target_commit_hash"]) == 40
        assert len(current_branches[0]["short_hash"]) == 7

    @pytest.mark.asyncio
    async def test_GetGitBranches_EnDirectorioSinGit_DebeLanzarGitRepoNotFound404(self, tmp_path):
        # Arrange
        empty_service = GitService(workspace_root=tmp_path)

        # Act & Assert
        with pytest.raises(GitRepoNotFoundError) as exc_info:
            await empty_service.get_branches()

        assert exc_info.value.status_code == 404
        assert exc_info.value.error_code == "GIT_REPO_NOT_FOUND"


class TestHU004GitSanitizationAndBinaryDiffCertification:
    """
    Certificación de robustez ante datos malformados, sanitización de autor y elisión binaria (CB-04, CB-05 / ADR-014).
    """

    def test_SanitizeString_ConBytesNulosYEspacios_DebeLimpiarCadenaSinCorromperPayload(self):
        # Arrange
        dirty_input = "feat(git): commit message con \x00 byte nulo \x00 y espacios  \n"

        # Act
        clean_result = git_service._sanitize_string(dirty_input)

        # Assert
        assert "\x00" not in clean_result
        assert clean_result == "feat(git): commit message con  byte nulo  y espacios"

    def test_InferAgentRole_ConConvencionesBMADYAutor_DebeInferirRolEstructurado(self):
        # Arrange & Act & Assert
        assert git_service._infer_agent_role("Agent", "feat(auth): [TASK-001-BE-01] login") == "Senior Backend Developer"
        assert git_service._infer_agent_role("Agent", "feat(ui): [TASK-001-FE-01] component") == "Senior Frontend Developer"
        assert git_service._infer_agent_role("Agent", "test(api): [TASK-001-QA-01] tests") == "QA Automation"
        assert git_service._infer_agent_role("Business Analyst", "feat: specs") == "Business Analyst"
        assert git_service._infer_agent_role("Designer UX", "wireframe") == "Designer UX"
        assert git_service._infer_agent_role("Watcher", "auto commit") == "Watcher BMAD"
        assert git_service._infer_agent_role("Desconocido", "random message") is None

    @pytest.mark.asyncio
    async def test_InspectCommits_ConArchivosBinariosOMasivos_DebeOmitirDiffCrudoYMarcarDiffOmitted(self):
        # Arrange
        commits_resp = await git_service.get_commits(limit=50)

        # Act & Assert
        assert commits_resp.total_count > 0
        for commit in commits_resp.commits:
            for file_change in commit.files:
                if file_change.is_binary:
                    # CB-05 / ADR-014: Para archivos binarios, el diff debe estar marcado como omitido
                    assert file_change.is_diff_omitted is True


class TestHU004GitReadOnlyGuaranteeCertification:
    """
    Certificación de Garantía de Solo Lectura (ADR-013 / Postcondición 4.2).
    """

    def test_TelemetryEndpoints_BajoInvocacionRepetida_NoDebeModificarGitHeadNiWorkingTree(self, qa_client):
        # Arrange: Obtener estado inicial de Git
        initial_status_res = qa_client.get("/api/v1/git/status")
        assert initial_status_res.status_code == 200
        initial_status = initial_status_res.json()
        initial_head = initial_status["head_commit_hash"]
        initial_branch = initial_status["current_branch"]
        initial_total_files = initial_status["total_modified_files"]

        # Act: Ejecutar ráfaga de consultas a los tres endpoints de telemetría
        for _ in range(5):
            qa_client.get("/api/v1/git/status")
            qa_client.get("/api/v1/git/commits?limit=10")
            qa_client.get("/api/v1/git/branches")

        # Assert: Verificar invariancia absoluta del repositorio
        final_status_res = qa_client.get("/api/v1/git/status")
        assert final_status_res.status_code == 200
        final_status = final_status_res.json()

        assert final_status["head_commit_hash"] == initial_head, "HEAD fue modificado por llamadas a la API"
        assert final_status["current_branch"] == initial_branch, "Branch fue modificada por llamadas a la API"
        assert final_status["total_modified_files"] == initial_total_files, "Working tree fue mutado por la API"
