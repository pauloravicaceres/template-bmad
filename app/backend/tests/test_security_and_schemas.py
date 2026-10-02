import pytest
from pydantic import ValidationError
from app.backend.models.schemas import DecisionPayload, ActionEnum
from app.backend.core.security import sanitize_feedback


class TestDecisionPayloadValidation:
    """Pruebas unitarias de validación para el esquema DecisionPayload (Pydantic v2)."""

    def test_DecisionPayload_ConAccionApproveSinFeedback_DebeSerValido(self):
        # Arrange
        data = {"action": "APPROVE"}

        # Act
        payload = DecisionPayload(**data)

        # Assert
        assert payload.action == ActionEnum.APPROVE
        assert payload.feedback is None

    def test_DecisionPayload_ConAccionApproveConFeedbackOpcional_DebeSerValido(self):
        # Arrange
        data = {"action": "APPROVE", "feedback": "Aprobación formal del Tech Lead"}

        # Act
        payload = DecisionPayload(**data)

        # Assert
        assert payload.action == ActionEnum.APPROVE
        assert payload.feedback == "Aprobación formal del Tech Lead"

    def test_DecisionPayload_ConAccionRejectYFeedbackValido_DebeSerValido(self):
        # Arrange
        data = {"action": "REJECT", "feedback": "Subsanar criterios de aceptación BDD"}

        # Act
        payload = DecisionPayload(**data)

        # Assert
        assert payload.action == ActionEnum.REJECT
        assert payload.feedback == "Subsanar criterios de aceptación BDD"

    def test_DecisionPayload_ConAccionRejectYSinFeedback_DebeLanzarValidationError(self):
        # Arrange
        data = {"action": "REJECT"}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DecisionPayload(**data)
        
        errors = str(exc_info.value)
        assert "Feedback is required when action is REJECT" in errors

    def test_DecisionPayload_ConAccionRejectYFeedbackVacio_DebeLanzarValidationError(self):
        # Arrange
        data = {"action": "REJECT", "feedback": ""}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DecisionPayload(**data)

        errors = str(exc_info.value)
        assert "Feedback is required when action is REJECT" in errors

    def test_DecisionPayload_ConAccionRejectYFeedbackSoloEspacios_DebeLanzarValidationError(self):
        # Arrange
        data = {"action": "REJECT", "feedback": "     \t \n "}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DecisionPayload(**data)

        errors = str(exc_info.value)
        assert "Feedback is required when action is REJECT" in errors

    def test_DecisionPayload_ConAccionInvalida_DebeLanzarValidationError(self):
        # Arrange
        data = {"action": "INVALID_ACTION", "feedback": "Algún texto"}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            DecisionPayload(**data)

        errors = str(exc_info.value)
        assert "Input should be 'APPROVE' or 'REJECT'" in errors or "value is not a valid enumeration member" in errors


class TestSecurityTokenGuard:
    """Pruebas unitarias para el módulo Security Token Guard (sanitización anti-inyección)."""

    def test_SanitizeFeedback_ConTextoSinTokens_DebeRetornarTextoSinModificar(self):
        # Arrange
        original_text = "El diseño visual requiere mayor contraste en los botones."

        # Act
        result = sanitize_feedback(original_text)

        # Assert
        assert result == original_text

    def test_SanitizeFeedback_ConTokenPm_DebeEscaparToken(self):
        # Arrange
        text = "Por favor notificar a @PM: para que revise el backlog."

        # Act
        result = sanitize_feedback(text)

        # Assert
        assert "[@PM:_ESCAPED]" in result
        assert "@PM:" not in result.replace("[@PM:_ESCAPED]", "")

    def test_SanitizeFeedback_ConMultiplesTokensAgentes_DebeEscaparTodosLosTokens(self):
        # Arrange
        text = "Reasignar a @BA: y coordinar con @QA-TECH: y @HUMANO: urgentemente."

        # Act
        result = sanitize_feedback(text)

        # Assert
        assert "[@BA:_ESCAPED]" in result
        assert "[@QA-TECH:_ESCAPED]" in result
        assert "[@HUMANO:_ESCAPED]" in result
        assert "@BA:" not in result.replace("[@BA:_ESCAPED]", "")
        assert "@QA-TECH:" not in result.replace("[@QA-TECH:_ESCAPED]", "")
        assert "@HUMANO:" not in result.replace("[@HUMANO:_ESCAPED]", "")

    def test_SanitizeFeedback_ConTextoVacio_DebeRetornarVacioSinErrores(self):
        # Arrange
        empty_text = ""

        # Act
        result = sanitize_feedback(empty_text)

        # Assert
        assert result == ""

    def test_SanitizeFeedback_ConNone_DebeRetornarNoneSinErrores(self):
        # Arrange
        none_value = None

        # Act
        result = sanitize_feedback(none_value)

        # Assert
        assert result is None
