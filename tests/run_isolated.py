"""Optional local pytest harness using inherited-ACL temporary directories.

For Windows sandboxes where tempfile's private mode=0o700 directories cannot be
reopened. Does not chmod or modify ACLs. Creates unique directories under .test-tmp.
Normal environments can simply use python -m pytest instead.
"""
import os
from pathlib import Path
import secrets
import sys
import tempfile
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TEMP_ROOT = ROOT / '.test-tmp'
TEMP_ROOT.mkdir(exist_ok=True)


def inherited_temp(suffix=None, prefix=None, dir=None):
    base = Path(dir) if dir else TEMP_ROOT
    path = base / ((prefix or 'tmp') + secrets.token_hex(12) + (suffix or ''))
    path.mkdir(parents=True)
    return str(path)


class RetainedDirectory:
    """Keep isolated fixtures accessible under Windows inherited ACLs."""

    def __init__(self, suffix=None, prefix=None, dir=None, **kwargs):
        self.name = inherited_temp(suffix, prefix, dir)

    def __enter__(self):
        return self.name

    def __exit__(self, *args):
        return False

    def cleanup(self):
        pass


if __name__ == '__main__':
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    os.environ['BMAD_TEST_REAL_CLI'] = '0'
    for key in ('BMAD_PROJECT', 'BMAD_WORKSPACE', 'SPECIFY_INIT_DIR',
                'SPECIFY_FEATURE_DIRECTORY', 'SPECIFY_FEATURE'):
        os.environ.pop(key, None)
    tempfile.mkdtemp = inherited_temp
    tempfile.TemporaryDirectory = RetainedDirectory
    tempfile.tempdir = str(TEMP_ROOT)
    import pytest

    class TemporaryFixtures:
        @pytest.fixture
        def tmp_path(self):
            # Preserve test evidence; never change permissions to clean it up.
            return Path(inherited_temp(prefix='pytest-'))

    raise SystemExit(pytest.main(sys.argv[1:] or ['tests', '-q', '-p', 'no:cacheprovider'],
                                plugins=[TemporaryFixtures()]))
