"""Compuertas de aprobación con efectos (handoff, rama): sin artefacto declarado fallan sin tocar el tracker."""
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


def _bloque(autor, artefacto, handoff="@HUMANO: revisa el entregable"):
    linea = f"- **Artefacto generado:** `{artefacto}`\n" if artefacto is not None else ""
    return (f"### [10-10-2026] {autor}\n- **Hora:** 12:00:00\n" + linea +
            f"- **Estado:** listo para revisión\n- **Handoff:** {handoff}")


# (autor, artefacto válido, token del handoff, handoff del bloque). Los entregables que no son HU no siguen su formato.
COMPUERTAS = [
    ("Business Storyteller", "docs/business-storyteller/idea-reservas.md", "@PA:", None),
    ("Product Analyst", "docs/product-analyst/pb-reservas.md", "@PM:", None),
    ("Product Manager", "docs/product-manager/mvp-reservas.md", "@BA:",
     "@HUMANO: Revisa el MVP. La HU a delegar es 003-gestion-clientes."),
    ("QA Documental", "docs/qa-documental/qa_003.md", "@UX:", None),
    ("Designer UX", "docs/designer-ux/ux_wireframes.md", "@SA:", None),
    ("Solutions Architect", "docs/architecture/tech_guidelines.md", "@DA:", None),
    ("QA-Tech", "docs/qa-tech/tech-design_003.md", "@DEV-BACK:", None),
]


@pytest.mark.parametrize("autor, artefacto, token, handoff", COMPUERTAS)
def test_aprobacion_con_artefacto_emite_el_handoff_que_lo_cita(cliente, autor, artefacto, token, handoff):
    client, servicio, ruta = cliente
    servicio.append_decision(_bloque(autor, artefacto, handoff or "@HUMANO: revisa el entregable"))

    r = client.post("/api/v1/gates/123/decision", json={"action": "APPROVE"})

    assert r.status_code == 200
    texto = ruta.read_text(encoding="utf-8")
    assert token in texto and artefacto.split("/")[-1] in texto
    assert "artefacto.md" not in texto


@pytest.mark.parametrize("valor", [None, "ninguno", "N/A", "-"])
@pytest.mark.parametrize("autor, _artefacto, _token, handoff", COMPUERTAS)
def test_aprobacion_sin_artefacto_falla_sin_handoff_ni_rama(cliente, autor, _artefacto, _token, handoff, valor):
    client, servicio, ruta = cliente
    servicio.append_decision(_bloque(autor, valor, handoff or "@HUMANO: revisa el entregable"))
    antes = ruta.read_text(encoding="utf-8")

    r = client.post("/api/v1/gates/123/decision", json={"action": "APPROVE"})

    assert r.status_code == 422
    assert "Artefacto generado" in r.json()["detail"]
    assert ruta.read_text(encoding="utf-8") == antes
    assert "GITOPS-BRANCH-CREATE" not in ruta.read_text(encoding="utf-8")


def test_cierre_final_del_pm_no_necesita_artefacto(cliente):
    client, servicio, ruta = cliente
    servicio.append_decision(_bloque("Product Manager", None, "@HUMANO: El proyecto está 100% concluido."))

    r = client.post("/api/v1/gates/123/decision", json={"action": "APPROVE"})

    assert r.status_code == 200
    assert "Proyecto completado exitosamente" in ruta.read_text(encoding="utf-8")


def test_rechazo_sin_artefacto_solo_registra_la_decision(cliente):
    client, servicio, ruta = cliente
    servicio.append_decision(_bloque("Product Analyst", None))

    r = client.post("/api/v1/gates/123/decision", json={"action": "REJECT", "feedback": "falta el alcance"})

    assert r.status_code == 200
    texto = ruta.read_text(encoding="utf-8")
    assert "- **Estado:** REJECT" in texto and "@PM:" not in texto
