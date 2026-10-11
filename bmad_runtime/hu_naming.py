"""Contrato único del identificador universal de historias de usuario (HU).

Una HU se nombra `NNN-nombre-en-kebab-case.md`: correlativo de tres dígitos, guion y descripción en
minúsculas ASCII con palabras separadas por un único guion. El mismo identificador (sin `.md`) nombra
la carpeta `specs/NNN-nombre/` y la rama `feat/NNN-nombre`. No hay compatibilidad con snake_case ni con
el formato `NNN-HU_nombre`: un nombre inválido se rechaza con su motivo, nunca se corrige ni se renombra.
"""
import re

HU_ID = r"\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*"
HU_FILE_IN_TEXT = rf"(?<![\w-])({HU_ID}\.md)"
HU_ID_IN_DELEGATION = rf"delegar es\s+({HU_ID})(?![\w-])"
# Candidatos con aspecto de HU (válidos o no) para explicar un rechazo en lugar de ignorarlo en silencio.
_CANDIDATE_IN_BA = r"docs[/\\]business-analyst[/\\]([^\n`'\"<>|*?:/\\]+?\.md)"
_CANDIDATE_BARE = r"(?<![\w./\\-])(\d+[-_][\w.-]*\.md)"


def is_hu_id(value):
    """True si `value` es un identificador universal `NNN-nombre-en-kebab-case` (sin extensión)."""
    return isinstance(value, str) and re.fullmatch(HU_ID, value) is not None


def is_hu_filename(value):
    return isinstance(value, str) and re.fullmatch(rf"{HU_ID}\.md", value) is not None


def hu_name_error(filename):
    """Motivo por el que `filename` no cumple el contrato, o None si es válido."""
    name = str(filename or "")
    if is_hu_filename(name):
        return None
    contract = "se espera NNN-nombre-en-kebab-case.md (p. ej. 001-registrar-cliente.md)"
    if not name.endswith(".md"):
        return f"'{name}' no tiene extensión .md; {contract}"
    stem = name[:-3]
    prefix = re.match(r"(\d*)([-_ ]?)", stem)
    digits, separator = prefix.group(1), prefix.group(2)
    if len(digits) != 3:
        return f"'{name}' debe empezar por un correlativo de exactamente 3 dígitos; {contract}"
    if separator != "-":
        return f"'{name}' debe separar el correlativo con un guion; {contract}"
    description = stem[4:]
    if not description:
        return f"'{name}' no tiene descripción tras el correlativo; {contract}"
    if " " in description:
        return f"'{name}' contiene espacios; {contract}"
    if "_" in description:
        return f"'{name}' usa guiones bajos (snake_case no admitido); {contract}"
    if not description.isascii():
        return f"'{name}' contiene tildes o caracteres no ASCII; {contract}"
    if description != description.lower():
        return f"'{name}' contiene mayúsculas; {contract}"
    if re.search(r"[^a-z0-9-]", description):
        return f"'{name}' contiene caracteres especiales; {contract}"
    return f"'{name}' debe separar las palabras con un único guion, sin guiones al inicio o al final; {contract}"


def find_hu_file(text):
    """Primera HU válida citada en `text`, o None."""
    match = re.search(HU_FILE_IN_TEXT, text or "")
    return match.group(1) if match else None


def invalid_hu_reference(text):
    """Motivo del primer nombre con aspecto de HU que incumple el contrato en `text`, o None."""
    for pattern in (_CANDIDATE_IN_BA, _CANDIDATE_BARE):
        for candidate in re.findall(pattern, text or ""):
            error = hu_name_error(candidate.strip())
            if error:
                return error
    return None


def last_hu_candidate(text):
    """Último nombre con aspecto de HU citado en `text` (válido o no), o None."""
    found = [(match.start(1), match.group(1).strip())
             for pattern in (_CANDIDATE_IN_BA, _CANDIDATE_BARE) for match in re.finditer(pattern, text or "")]
    return max(found)[1] if found else None


def hu_id_from_delegation(text):
    """Identificador que el PM delega ('... delegar es NNN-nombre'), o None si falta o es inválido."""
    match = re.search(HU_ID_IN_DELEGATION, text or "")
    return match.group(1) if match else None


def is_feature_branch(branch):
    """True si `branch` es `feat/NNN-nombre-en-kebab-case`."""
    return isinstance(branch, str) and branch.startswith("feat/") and is_hu_id(branch[5:])
