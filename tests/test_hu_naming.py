"""Contrato único de nombres de HU (NNN-nombre-en-kebab-case) en todos los consumidores del flujo."""
import json
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import watcher_bmad as workflow
from bmad_runtime.errors import ReconciliationRequired
from bmad_runtime.hu_naming import (find_hu_file, hu_id_from_delegation, hu_name_error, invalid_hu_reference,
                                    is_feature_branch, is_hu_id, last_hu_candidate)

ROOT = Path(__file__).resolve().parents[1]
VALIDOS = ['001-login-usuario.md', '002-recuperar-contrasena.md', '003-gestion-clientes.md',
           '010-registrar-cliente-v2.md']
INVALIDOS = {
    '001-HU_login.md': 'guiones bajos',
    '002-HU_recuperar_contrasena.md': 'guiones bajos',
    '003-gestion_clientes.md': 'guiones bajos',
    '004-HU Gestion Clientes.md': 'espacios',
    '005-Gestion-clientes.md': 'mayúsculas',
    '006-HU-login-usuario.md': 'mayúsculas',
    '007-gestión-clientes.md': 'tildes',
    '008-recuperar-contraseña.md': 'tildes',
    '009_login-usuario.md': 'guion',
    '010--login.md': 'único guion',
    '011-login-.md': 'único guion',
    '012-login.usuario.md': 'caracteres especiales',
    '01-login.md': '3 dígitos',
    '0001-login.md': '3 dígitos',
    'login-usuario.md': '3 dígitos',
    '013-.md': 'descripción',
    '014.md': 'guion',
    '015-login-usuario.txt': '.md',
}


class ContratoTests(unittest.TestCase):
    def test_validos(self):
        for nombre in VALIDOS:
            self.assertIsNone(hu_name_error(nombre), nombre)
            self.assertTrue(is_hu_id(nombre[:-3]))
            self.assertTrue(is_feature_branch(f'feat/{nombre[:-3]}'))

    def test_invalidos_con_motivo(self):
        for nombre, motivo in INVALIDOS.items():
            error = hu_name_error(nombre)
            self.assertIsNotNone(error, nombre)
            self.assertIn(motivo, error, nombre)
            self.assertIn('NNN-nombre-en-kebab-case.md', error)

    def test_reconocimiento_en_texto(self):
        self.assertEqual(find_hu_file('ver docs/business-analyst/003-gestion-clientes.md ahora'), '003-gestion-clientes.md')
        self.assertIsNone(find_hu_file('docs/business-analyst/003-HU_gestion.md'))
        self.assertIsNone(find_hu_file('x0003-gestion.md'))
        self.assertIn('espacios', invalid_hu_reference('aprobada docs/business-analyst/004-HU Gestion Clientes.md'))
        self.assertIn('guiones bajos', invalid_hu_reference('aprobada 001-HU_login.md'))
        self.assertIsNone(invalid_hu_reference('aprobada docs/business-analyst/003-gestion-clientes.md'))
        self.assertEqual(last_hu_candidate('001-a.md y luego docs/business-analyst/002-b_c.md'), '002-b_c.md')
        self.assertEqual(hu_id_from_delegation('La HU a delegar es 003-gestion-clientes.'), '003-gestion-clientes')
        self.assertIsNone(hu_id_from_delegation('La HU a delegar es 003-HU_gestion'))
        self.assertFalse(is_feature_branch('feat/001-epic_generica'))
        self.assertFalse(is_feature_branch('feat/test'))
        self.assertFalse(is_feature_branch('001-login'))


class GeneracionTests(unittest.TestCase):
    """Los perfiles que generan HU (PM/BA/UX) solo documentan ejemplos válidos y ninguno pide snake_case."""

    def test_perfiles_y_plantillas(self):
        fuentes = [p for rol in ('business-analyst', 'product-manager', 'designer-ux', 'qa-documental')
                   for p in (ROOT / rol).rglob('*.md')]
        fuentes += [ROOT / 'constitution.md', ROOT / 'GUIDE.md', ROOT / 'ARCHITECTURE.md']
        self.assertTrue(fuentes)
        for ruta in fuentes:
            texto = ruta.read_text(encoding='utf-8')
            self.assertNotRegex(texto, r'\d{3}-HU_|XXX-HU_|NNN-HU_|feat/HU_', str(ruta))
            for ejemplo in re.findall(r'`(?:[\w./-]*/)?(\d{3}-[^`/\s]+?)(?:\.md)?/?`', texto):
                self.assertIsNone(hu_name_error(f'{ejemplo}.md'), f'{ruta}: {ejemplo}')


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.tracker = self.root / 'tracker.md'
        self.tracker.write_text('', encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def _aprobacion_qa(self, nombre):
        return f'- **Handoff:** @SA: La HU docs/business-analyst/{nombre} fue aprobada por QA. Procede.'

    def test_gatekeeper_valido_inicia_fase_de_negocio(self):
        with patch.object(workflow, 'is_tracker_paused_for_human', return_value=False), \
                patch.object(workflow, 'ejecutar_sdd_fase_negocio', return_value=True) as negocio:
            self.assertEqual(workflow.extraer_instrucciones(self._aprobacion_qa('003-gestion-clientes.md')), [])
        negocio.assert_called_once_with('docs/business-analyst/003-gestion-clientes.md')

    def test_gatekeeper_invalido_informa_y_detiene_solo_ese_paso(self):
        for nombre in ('003-HU_gestion.md', '003-gestion_clientes.md', '003-Gestion.md'):
            with patch.object(workflow, 'TRACKER_PATH', str(self.tracker)), \
                    patch.object(workflow, 'is_tracker_paused_for_human', return_value=False), \
                    patch.object(workflow, 'ejecutar_sdd_fase_negocio') as negocio, \
                    patch.object(workflow, 'ejecutar_speckit') as speckit:
                self.assertEqual(workflow.extraer_instrucciones(self._aprobacion_qa(nombre)), [])
            negocio.assert_not_called()
            speckit.assert_not_called()
            texto = self.tracker.read_text(encoding='utf-8')
            self.assertIn(f"nombre de historia inválido: '{nombre}'", texto)
            self.assertNotIn('@SA:', texto)
            self.assertNotIn('@UX:', texto)

    def test_carpeta_spec_exacta(self):
        self.assertEqual(workflow.carpeta_spec_para_hu('docs\\business-analyst\\003-gestion-clientes.md'),
                         'specs/003-gestion-clientes')
        for nombre in INVALIDOS:
            self.assertIsNone(workflow.carpeta_spec_para_hu(f'docs/business-analyst/{nombre}'), nombre)

    def test_fase_negocio_no_deja_que_speckit_elija_carpeta(self):
        with patch.object(workflow, 'TRACKER_PATH', str(self.tracker)), \
                patch.object(workflow, 'ejecutar_speckit') as speckit:
            self.assertFalse(workflow.ejecutar_sdd_fase_negocio('docs/business-analyst/003-gestion_clientes.md'))
        speckit.assert_not_called()
        self.assertIn('guiones bajos', self.tracker.read_text(encoding='utf-8'))

    def test_fase_negocio_fija_la_carpeta_de_la_hu(self):
        (self.root / '.specify').mkdir()
        (self.root / 'specs' / '003-gestion-clientes').mkdir(parents=True)
        (self.root / 'specs' / '003-gestion-clientes' / 'spec.md').write_text('# spec', encoding='utf-8')
        (self.root / '.specify' / 'feature.json').write_text(
            json.dumps({'feature_directory': 'specs/003-gestion-clientes'}), encoding='utf-8')
        ok = SimpleNamespace(returncode=0, stdout='sin dudas')
        with patch.object(workflow, 'TRACKER_PATH', str(self.tracker)), \
                patch.object(workflow, 'DIRECTORIO_RAIZ', self.root), \
                patch.object(workflow, 'ejecutar_speckit', return_value=ok) as speckit, \
                patch.object(workflow, 'registrar_traspaso_fase_a', return_value=('@SA:', True)):
            self.assertTrue(workflow.ejecutar_sdd_fase_negocio('docs/business-analyst/003-gestion-clientes.md'))
        primera = speckit.call_args_list[0]
        self.assertEqual(primera.args[0], 'specify')
        self.assertEqual(primera.kwargs['entorno'], {'SPECIFY_FEATURE_DIRECTORY': 'specs/003-gestion-clientes'})

    def test_rama_invalida_no_se_crea(self):
        for rama in ('feat/003-HU_gestion', 'feat/003-gestion_clientes', 'feat/001-Epic', 'feat/test', '003-gestion'):
            with patch.object(workflow, 'auto_commit_security') as autosave, patch.object(workflow, 'run_git') as git:
                with self.assertRaisesRegex(ReconciliationRequired, 'feat/NNN-nombre-en-kebab-case'):
                    workflow.gitops_branch_create(rama)
            autosave.assert_not_called()
            git.assert_not_called()

    def test_rama_valida_se_crea(self):
        git = Mock(return_value=SimpleNamespace(stdout=''))
        with patch.object(workflow, 'auto_commit_security'), patch.object(workflow, 'run_git', git), \
                patch.object(workflow, 'resetear_retrabajo'), patch.object(workflow, 'get_base_branch', return_value='main'), \
                patch.object(workflow, 'get_current_branch', return_value='main'):
            workflow.gitops_branch_create('feat/003-gestion-clientes')
        self.assertIn(['git', 'checkout', '-b', 'feat/003-gestion-clientes'], [c.args[0] for c in git.call_args_list])

    def test_reanudacion_recupera_la_rama_abierta(self):
        self.tracker.write_text('@WATCHER: GITOPS-BRANCH-CREATE feat/001-login-usuario\n'
                                '@WATCHER: GITOPS-MERGE-CLOSE feat/001-login-usuario\n'
                                '- **Handoff:** @WATCHER: GITOPS-BRANCH-CREATE feat/002-recuperar-contrasena\n',
                                encoding='utf-8')
        with patch.object(workflow, 'TRACKER_PATH', str(self.tracker)):
            self.assertEqual(workflow.hydration_gitops(), 'feat/002-recuperar-contrasena')

    def test_aislamiento_multiworkspace(self):
        otro = self.root / 'otro-workspace'
        for raiz in (self.root, otro):
            (raiz / '.specify').mkdir(parents=True)
        (self.root / 'specs' / '001-login-usuario').mkdir(parents=True)
        (self.root / 'specs' / '001-login-usuario' / 'spec.md').write_text('# spec', encoding='utf-8')
        for raiz in (self.root, otro):
            (raiz / '.specify' / 'feature.json').write_text(
                json.dumps({'feature_directory': 'specs/001-login-usuario'}), encoding='utf-8')
        carpeta = workflow.carpeta_spec_para_hu('docs/business-analyst/001-login-usuario.md')
        with patch.object(workflow, 'DIRECTORIO_RAIZ', self.root):
            self.assertEqual(workflow.verificar_carpeta_spec(carpeta), (True, ''))
        with patch.object(workflow, 'DIRECTORIO_RAIZ', otro):
            self.assertEqual(workflow.verificar_carpeta_spec(carpeta), (False, 'la carpeta no contiene spec.md'))
        self.assertFalse((otro / 'specs').exists())


class ApproveStepTests(unittest.TestCase):
    def setUp(self):
        from utils import approve_step
        self.approve = approve_step
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.tracker = self.root / 'docs' / 'tracker_bmad.md'
        self.tracker.parent.mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def _main(self, respuestas):
        contexto = SimpleNamespace(workspace_root=self.root, tracker_path=self.tracker, project_id='legacy',
                                   engine_root=Path(self.approve.__file__).resolve().parents[1])
        config = {clave: dict(valor) for clave, valor in self.approve.APPROVAL_CONFIG.items()}
        with patch('bmad_runtime.context.resolve_context', return_value=contexto), \
                patch.object(self.approve, 'APPROVAL_CONFIG', config), \
                patch.object(self.approve, 'DIRECTORIO_RAIZ', self.approve.DIRECTORIO_RAIZ), \
                patch.object(self.approve, 'TRACKER_PATH', self.approve.TRACKER_PATH), \
                patch.object(self.approve, 'abrir_archivo_en_so'), \
                patch('builtins.input', side_effect=respuestas):
            self.approve.main([])

    def test_aprueba_hu_valida(self):
        self.tracker.write_text('- **Artefacto generado:** `docs/business-analyst/003-gestion-clientes.md`\n', encoding='utf-8')
        self._main(['4', 's'])
        texto = self.tracker.read_text(encoding='utf-8')
        self.assertIn('@QA: La Historia de Usuario ha sido revisada en el archivo 003-gestion-clientes.md', texto)

    def test_rechaza_hu_reciente_invalida_sin_aprobar_una_anterior(self):
        original = ('`docs/business-analyst/002-recuperar-contrasena.md`\n'
                    '- **Artefacto generado:** `docs/business-analyst/003-gestion_clientes.md`\n')
        self.tracker.write_text(original, encoding='utf-8')
        with self.assertRaises(SystemExit) as salida:
            self._main(['4'])
        self.assertEqual(salida.exception.code, 1)
        self.assertEqual(self.tracker.read_text(encoding='utf-8'), original)

    def test_rechaza_hu_manual_invalida(self):
        self.tracker.write_text('sin artefactos\n', encoding='utf-8')
        with self.assertRaises(SystemExit):
            self._main(['4', '003-HU Gestion.md'])
        self.assertEqual(self.tracker.read_text(encoding='utf-8'), 'sin artefactos\n')

    def test_rama_desde_delegacion_valida(self):
        self.tracker.write_text('`docs/product-manager/mvp-reserva-citas.md` La HU a delegar es 003-gestion-clientes.\n',
                                encoding='utf-8')
        self._main(['3', 's'])
        texto = self.tracker.read_text(encoding='utf-8')
        self.assertIn('@WATCHER: GITOPS-BRANCH-CREATE feat/003-gestion-clientes\n', texto)
        self.assertNotIn('epic-generica', texto)

    def test_sin_identificador_valido_no_crea_rama_generica(self):
        original = '`docs/product-manager/mvp-reserva-citas.md` La HU a delegar es 003-HU_gestion.\n'
        self.tracker.write_text(original, encoding='utf-8')
        with self.assertRaises(SystemExit) as salida:
            self._main(['3', '003-HU_gestion'])
        self.assertEqual(salida.exception.code, 1)
        self.assertEqual(self.tracker.read_text(encoding='utf-8'), original)


if __name__ == '__main__':
    unittest.main()
