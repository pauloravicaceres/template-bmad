import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ux_routing
import watcher_bmad as watcher
from utils import start_agents


class CharacterizationTests(unittest.TestCase):
    def test_layout_and_exclusions(self):
        self.assertEqual([len(v) for v in start_agents.TABS_CONFIG.values()], [6, 4, 3])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'config_bmad.json').write_text('{"project_type":"headless","ux_phase":"on"}')
            self.assertEqual(ux_routing.agentes_omitidos(root), {'designer-ux'})
            self.assertEqual(ux_routing.decidir_ruta_ux(root).destino, 'SA')

    def test_ux_hu_and_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(ux_routing.decidir_ruta_ux(root).destino, 'UX')
            hu = root / 'hu.md'
            hu.write_text('- **Requiere interfaz:** No', encoding='utf-8')
            self.assertEqual(ux_routing.decidir_ruta_ux(root, hu).destino, 'SA')

    def test_git_macros_are_commands_not_mentions(self):
        self.assertEqual(watcher.macro_gitops('@WATCHER: GITOPS-BRANCH-CREATE feat/001', 'BRANCH-CREATE'), 'feat/001')
        self.assertIsNone(watcher.macro_gitops('Decide si usar @WATCHER: GITOPS-MERGE-CLOSE feat/001', 'MERGE-CLOSE'))

    def test_tokens_aliases_and_human_gate(self):
        with patch.object(watcher, 'is_tracker_paused_for_human', return_value=False), patch.dict(watcher.contexto_bloque, autor='HUMANO'):
            tasks = watcher.extraer_instrucciones('@BA: redacta @CR: revisa')
            self.assertEqual([t['agente'] for t in tasks], ['business-analyst', 'code-review'])
            self.assertEqual(watcher.extraer_instrucciones('@HUMANO: decide @BA: mencionado'), [])

    def test_duplicate_dev_authors_suppressed(self):
        with patch.dict(watcher.contexto_bloque, autor='DEV-FRONT'):
            self.assertEqual(watcher.extraer_instrucciones('@QA-AUTO: valida'), [])

    def test_rework_layer_segments(self):
        self.assertEqual(watcher.MAX_ITERACIONES_RETRABAJO, 2)
        parts = watcher.extraer_segmentos_handoff('**Handoff:** @DEV-BACK: API @DEV-FRONT: UI @QA-AUTO: verifica')
        self.assertEqual(parts, {'backend': 'API', 'frontend': 'UI', 'qa': 'verifica'})

    def test_documentation_scope(self):
        text = watcher.instruccion_doc_viva('doc.md', 'backend', 'app/backend/README.md')
        self.assertIn('SOLO BACKEND', text)
        self.assertIn('NO escribas en documents/tracker_bmad.md', text)
        self.assertIn('app/backend/README.md', text)

    def test_exact_feature_folder(self):
        self.assertEqual(watcher.carpeta_spec_para_hu('documents/business-analyst/016-HU_ficha.md'), 'specs/016-HU_ficha')


if __name__ == '__main__':
    unittest.main()
