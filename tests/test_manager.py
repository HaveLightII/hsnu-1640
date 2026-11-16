import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

projectPath = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('manager', projectPath / 'manager.py')
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


class ManagerTests(unittest.TestCase):
    def setUp(self):
        self.tempDir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempDir.cleanup)
        self.path = Path(self.tempDir.name) / 'config.json'
        manager.saveConfig(self.path, manager.emptyConfig())

    def runCommand(self, *args, expected=0):
        result = subprocess.run([sys.executable, str(projectPath / 'manager.py'),
                                 '--config', str(self.path), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stderr)
        return result

    def testAllSectionsAndCalendar(self):
        examples = {
            'exams': ['--date', '2026/12/01', '--subject', '英文', '--range', '第一課'],
            'homework': ['--date', '2026-12-02', '--item', '作文'],
            'matters': ['--date', '2026-12-03', '--item', '繳費'],
            'links': ['--label', '學校', '--url', 'https://example.com'],
        }
        for section, args in examples.items():
            self.runCommand(section, 'add', *args)
            self.assertIn('1.', self.runCommand(section, 'list').stdout)
            field = 'subject' if section == 'exams' else ('label' if section == 'links' else 'item')
            self.runCommand(section, 'edit', '1', '--' + field, '修改內容')
            self.assertIn('修改內容', self.runCommand(section, 'list').stdout)
            self.runCommand(section, 'delete', '1')
            self.assertEqual(manager.loadConfig(self.path)[section], [])
        self.runCommand('calendar', 'set', 'https://calendar.google.com/calendar/embed?src=test')
        self.assertIn('embed', self.runCommand('calendar', 'show').stdout)
        self.runCommand('calendar', 'clear')
        self.assertEqual(manager.loadConfig(self.path)['calendar']['url'], '')

    def testInvalidEditIsAtomic(self):
        self.runCommand('matters', 'add', '--date', '2026-12-01', '--item', '原內容')
        original = self.path.read_bytes()
        self.runCommand('matters', 'edit', '1', '--item', '新內容', '--link', 'javascript:alert(1)', expected=1)
        self.runCommand('matters', 'edit', '1', '--date', '2026-02-30', expected=1)
        self.runCommand('matters', 'delete', '0', expected=1)
        self.assertEqual(original, self.path.read_bytes())

    def testInitBackupAndConfirmation(self):
        self.runCommand('links', 'add', '--label', '網站', '--url', 'https://example.com')
        original = self.path.read_bytes()
        self.runCommand('init', expected=2)
        self.assertEqual(original, self.path.read_bytes())
        self.runCommand('init', '--yes')
        self.assertEqual(manager.loadConfig(self.path), manager.emptyConfig())
        backups = list(self.path.parent.glob('*.bak'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)

    def testPruneAndExplicitEmpty(self):
        self.runCommand('homework', 'add', '--date', '2000-01-01', '--item', '舊作業', '--link', 'https://example.com')
        self.runCommand('homework', 'edit', '1', '--link', '')
        self.assertEqual(manager.loadConfig(self.path)['homework'][0]['link'], '')
        self.runCommand('homework', 'list')
        self.assertEqual(len(manager.loadConfig(self.path)['homework']), 1)
        self.runCommand('homework', 'prune')
        self.assertEqual(manager.loadConfig(self.path)['homework'], [])

    def testInteractiveCancelAndDiscard(self):
        original = self.path.read_bytes()
        with patch('builtins.input', side_effect=['2', '2', '2026-12-01', 'back', '6']), contextlib.redirect_stdout(io.StringIO()):
            manager.interactive(self.path)
        self.assertEqual(original, self.path.read_bytes())
        with patch('builtins.input', side_effect=['2', '2', '2026-12-01', '作文', '', '7']), contextlib.redirect_stdout(io.StringIO()):
            manager.interactive(self.path)
        self.assertEqual(original, self.path.read_bytes())

    def testStartupCleanupPolicies(self):
        today = manager.date.today()
        from datetime import timedelta
        dates = [(today + timedelta(days=offset)).isoformat() for offset in (-1, 0, 1)]
        for policy, expectedDates in [('never', dates), ('beforeToday', dates[1:]), ('throughToday', dates[2:])]:
            config = manager.emptyConfig()
            config['cleanupPolicy'] = policy
            for section in ('homework', 'matters'):
                config[section] = [dict(date=value, item='內容', link='') for value in dates]
            config['exams'] = [dict(date=value, subject='國文', range='課文') for value in dates]
            config['links'] = [dict(label='學校', url='https://example.com', image='', hint='')]
            config['calendar']['url'] = 'https://calendar.google.com/'
            manager.saveConfig(self.path, config)
            self.runCommand('cleanup', 'show')
            updated = manager.loadConfig(self.path)
            for section in ('exams', 'homework', 'matters'):
                self.assertEqual([row['date'] for row in updated[section]], expectedDates)
            self.assertEqual(updated['links'], config['links'])
            self.assertEqual(updated['calendar'], config['calendar'])

    def testCleanupSetAndInteractiveDiscard(self):
        self.runCommand('cleanup', 'set', 'beforeToday')
        config = manager.loadConfig(self.path)
        self.assertEqual(config['cleanupPolicy'], 'beforeToday')
        config['homework'] = [dict(date='2000-01-01', item='舊作業', link='')]
        manager.saveConfig(self.path, config)
        with patch('builtins.input', side_effect=['9', '3', '7']), contextlib.redirect_stdout(io.StringIO()):
            manager.interactive(self.path)
        updated = manager.loadConfig(self.path)
        self.assertEqual(updated['homework'], [])
        self.assertEqual(updated['cleanupPolicy'], 'beforeToday')
        with patch('builtins.input', side_effect=['9', '3', '6']), contextlib.redirect_stdout(io.StringIO()):
            manager.interactive(self.path)
        self.assertEqual(manager.loadConfig(self.path)['cleanupPolicy'], 'throughToday')

    def testMissingAndBrokenConfig(self):
        self.path.write_text('{broken', encoding='utf-8')
        self.runCommand('exams', 'list', expected=1)
        self.runCommand('init', '--yes')
        self.path.unlink()
        self.runCommand('exams', 'list', expected=1)
        self.runCommand('init', '--yes')
        self.assertEqual(manager.loadConfig(self.path), manager.emptyConfig())


if __name__ == '__main__':
    unittest.main()
