"""Verify the launcher's backups without compiling or starting training."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('verify_and_run.sh')

class RunnerPathsTests(unittest.TestCase):
    def run_fixture(self, arguments, files):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'verify_and_run.sh').write_bytes(SCRIPT.read_bytes())
            bindir = root/'bin'
            bindir.mkdir()
            for name in ('nim', 'python3'):
                p = bindir/name
                p.write_text('#!/bin/sh\nexit 0\n')
                p.chmod(0o755)
            binary = root/'at_jev_checked'
            binary.write_text('#!/bin/sh\ncase "$1" in *-test) exit 0;; esac\nprintf "%s\\n" "$@" > launched.txt\n')
            binary.chmod(0o755)
            for name, contents in files.items():
                target = root/name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(contents)
            env = dict(os.environ, PATH=str(bindir)+os.pathsep+os.environ['PATH'])
            result = subprocess.run(['bash', 'verify_and_run.sh', *arguments], cwd=root,
                                    env=env, text=True, capture_output=True)
            backed_up = {str(p.relative_to(d)):p.read_text()
                         for d in root.glob('pre_run_backup.*') for p in d.rglob('*') if p.is_file()}
            return result.returncode, backed_up, (root/'launched.txt').exists()

    def test_separate_input_output_same_basename_and_option_order(self):
        for args in (['--load=a/state.bin', '--save=b/state.bin'],
                     ['--save=b/state.bin', '--load=a/state.bin']):
            rc, backups, launched = self.run_fixture(args, {'a/state.bin':'input', 'b/state.bin':'output'})
            self.assertEqual(rc, 0)
            self.assertTrue(launched)
            self.assertEqual(backups, {'input/state.bin':'input', 'output/state.bin':'output'})

    def test_backup_only_recovery(self):
        rc, backups, launched = self.run_fixture(['--load=x.bin'], {'x.bin.bak':'recover'})
        self.assertEqual(rc, 0)
        self.assertTrue(launched)
        self.assertEqual(backups['input/x.bin.bak'], 'recover')

    def test_missing_input_does_not_start_or_touch_output(self):
        rc, backups, launched = self.run_fixture(['--load=missing.bin','--save=x.bin'], {'x.bin':'keep'})
        self.assertNotEqual(rc, 0)
        self.assertFalse(launched)
        self.assertEqual(backups, {})

    def test_fresh_run_preserves_existing_output(self):
        rc, backups, launched = self.run_fixture(['--save=x.bin'], {'x.bin':'old','x.bin.model':'model'})
        self.assertEqual(rc, 0)
        self.assertTrue(launched)
        self.assertEqual(backups, {'output/x.bin':'old','output/x.bin.model':'model'})

if __name__ == '__main__': unittest.main()
