import os
import pytest
from filelock import FileLock, Timeout
from services.tracker_service import TrackerService


class TestTrackerService:
    """Pruebas unitarias y de concurrencia para el servicio FSaaDB TrackerService."""

    def test_ReadTracker_CuandoArchivoNoExiste_DebeRetornarStringVacio(self, tmp_path):
        # Arrange
        non_existent_file = tmp_path / "tracker_inexistente.md"
        service = TrackerService(str(non_existent_file))

        # Act
        content = service.read_tracker()

        # Assert
        assert content == ""

    def test_AppendDecision_ConArchivoNuevo_DebeCrearArchivoYGuardarDecision(self, tmp_path):
        # Arrange
        tracker_file = tmp_path / "tracker_bmad.md"
        service = TrackerService(str(tracker_file))
        decision_entry = "### [02-10-2026] HUMANO\n- **Estado:** APPROVE"

        # Act
        service.append_decision(decision_entry)

        # Assert
        assert os.path.exists(tracker_file)
        saved_content = service.read_tracker()
        assert decision_entry in saved_content

    def test_AppendDecision_MultipleVeces_DebePreservarHistorialInmutableAppendOnly(self, tmp_path):
        # Arrange
        tracker_file = tmp_path / "tracker_bmad.md"
        service = TrackerService(str(tracker_file))
        initial_history = "### [30-09-2026] Product Analyst\n- **Estado:** Especificación lista\n"
        service.replace_tracker_content(initial_history)
        decision_1 = "DECISION [001]: REJECT\nFeedback: Corregir criterios"
        decision_2 = "### [02-10-2026] HUMANO\n- **Estado:** APPROVE"

        # Act
        service.append_decision(decision_1)
        service.append_decision(decision_2)

        # Assert
        final_content = service.read_tracker()
        assert initial_history in final_content
        assert decision_1 in final_content
        assert decision_2 in final_content
        # Verificar secuencia cronológica append-only
        pos_initial = final_content.find("Product Analyst")
        pos_decision_1 = final_content.find(decision_1)
        pos_decision_2 = final_content.find(decision_2)
        assert pos_initial < pos_decision_1 < pos_decision_2

    def test_ReplaceTrackerContent_ConNuevoContenido_DebeReemplazarContenidoBajoLock(self, tmp_path):
        # Arrange
        tracker_file = tmp_path / "tracker_bmad.md"
        service = TrackerService(str(tracker_file))
        initial_text = "Contenido inicial obsoleto"
        new_text = "Contenido canónico actualizado 100%"
        service.append_decision(initial_text)

        # Act
        service.replace_tracker_content(new_text)

        # Assert
        result = service.read_tracker()
        assert result == new_text
        assert initial_text not in result

    def test_TrackerService_ConBloqueoConcurrenteExpirado_DebeLanzarTimeoutException(self, tmp_path):
        # Arrange
        tracker_file = tmp_path / "tracker_locked.md"
        lock_file = f"{str(tracker_file)}.lock"
        # Servicio configurado con timeout muy corto para la prueba de contención
        service = TrackerService(str(tracker_file))
        service.lock = FileLock(lock_file, timeout=0.1)

        # Bloqueamos el archivo deliberadamente con otro cerrojo externo
        external_lock = FileLock(lock_file, timeout=1)
        external_lock.acquire()

        try:
            # Act & Assert
            with pytest.raises(Timeout):
                service.append_decision("DECISION [999]: REJECT")
        finally:
            external_lock.release()
