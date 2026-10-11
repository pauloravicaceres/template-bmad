import pytest
from fastapi.testclient import TestClient
from main import app
import api.routes as routes
from services.tracker_service import TrackerService


@pytest.fixture
def cliente(tmp_path):
    ruta = tmp_path / "tracker_bmad.md"
    servicio = TrackerService(str(ruta))
    routes.tracker_service = servicio
    return TestClient(app), servicio, ruta


def _bloque_pm(handoff):
    return ("### [10-10-2026] Product Manager\n- **Hora:** 10:00:00\n"
            "- **Artefacto generado:** `docs/product-manager/mvp-reserva-citas.md`\n- **Estado:** APROBADO\n"
            f"- **Handoff:** @HUMANO: {handoff}")


def test_aprobacion_del_pm_abre_la_rama_de_la_hu_en_kebab_case(cliente):
    client, servicio, ruta = cliente
    servicio.append_decision(_bloque_pm("Revisa el MVP. La HU a delegar es 003-gestion-clientes."))

    r = client.post("/api/v1/gates/123/decision", json={"action": "APPROVE"})

    assert r.status_code == 200
    texto = ruta.read_text(encoding="utf-8")
    assert "@WATCHER: GITOPS-BRANCH-CREATE feat/003-gestion-clientes" in texto
    assert "epic-generica" not in texto


@pytest.mark.parametrize("handoff", [
    "Revisa el MVP. La HU a delegar es 003-HU_gestion_clientes.",
    "Revisa el MVP. La HU a delegar es 003-Gestion-Clientes.",
    "Revisa el MVP sin indicar la HU.",
])
def test_sin_identificador_valido_no_crea_rama_generica(cliente, handoff):
    client, servicio, ruta = cliente
    servicio.append_decision(_bloque_pm(handoff))
    antes = ruta.read_text(encoding="utf-8")

    r = client.post("/api/v1/gates/123/decision", json={"action": "APPROVE"})

    assert r.status_code == 422
    assert "NNN-nombre-en-kebab-case" in r.json()["detail"]
    assert ruta.read_text(encoding="utf-8") == antes


@pytest.mark.parametrize("epic_id, estado", [("004-registrar-cliente", 200), ("004-registrar_cliente", 422),
                                             ("004 registrar cliente", 422)])
def test_epic_id_explicito_se_valida(cliente, epic_id, estado):
    client, servicio, ruta = cliente
    servicio.append_decision(_bloque_pm("Revisa el MVP. La HU a delegar es 003-gestion-clientes."))

    r = client.post("/api/v1/gates/123/decision", json={"action": "APPROVE", "epic_id": epic_id})

    assert r.status_code == estado
    texto = ruta.read_text(encoding="utf-8")
    assert ("GITOPS-BRANCH-CREATE feat/004-registrar-cliente" in texto) == (estado == 200)


def _bloque_ba(artefacto):
    linea = f"- **Artefacto generado:** `{artefacto}`\n" if artefacto is not None else ""
    return ("### [10-10-2026] Business Analyst\n- **Hora:** 11:00:00\n" + linea +
            "- **Estado:** HU redactada\n- **Handoff:** @HUMANO: revisa la historia de usuario")


@pytest.mark.parametrize("artefacto", ["docs/business-analyst/003-gestion-clientes.md",
                                       r"docs\business-analyst\003-gestion-clientes.md"])
def test_aprobacion_del_ba_entrega_la_hu_valida_a_qa(cliente, artefacto):
    client, servicio, ruta = cliente
    servicio.append_decision(_bloque_ba(artefacto))

    r = client.post("/api/v1/gates/123/decision", json={"action": "APPROVE"})

    assert r.status_code == 200
    assert "@QA: La Historia de Usuario ha sido revisada en el archivo 003-gestion-clientes.md." in \
        ruta.read_text(encoding="utf-8")


@pytest.mark.parametrize("artefacto, motivo", [
    ("docs/business-analyst/003-HU_gestion_clientes.md", "guiones bajos"),
    ("docs/business-analyst/3-gestion-clientes.md", "3 dígitos"),
    ("docs/business-analyst/003-Gestion-Clientes.md", "mayúsculas"),
    ("docs/business-analyst/003-gestion-clientes.txt", "extensión .md"),
    (None, "no declara 'Artefacto generado'"),
])
def test_aprobacion_del_ba_rechaza_hu_ausente_o_invalida_sin_tocar_el_tracker(cliente, artefacto, motivo):
    client, servicio, ruta = cliente
    servicio.append_decision(_bloque_ba(artefacto))
    antes = ruta.read_text(encoding="utf-8")

    r = client.post("/api/v1/gates/123/decision", json={"action": "APPROVE"})

    assert r.status_code == 422
    assert motivo in r.json()["detail"]
    assert "NNN-nombre-en-kebab-case" in r.json()["detail"]
    assert "artefacto.md" not in r.json()["detail"]
    assert ruta.read_text(encoding="utf-8") == antes
