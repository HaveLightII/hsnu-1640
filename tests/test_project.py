import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

projectPath = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('projectManager', projectPath / 'manager.py')
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.tempDir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempDir.cleanup)
        self.root = Path(self.tempDir.name)
        for name in ('project.json', 'index.html', 'config.json', 'src-tauri/index.html',
                     'src-tauri/tauri.conf.json', 'src-tauri/capabilities/default.json', 'src-tauri/gen/android/app/build.gradle.kts',
                     'src-tauri/gen/android/app/src/main/res/values/strings.xml',
                     'src-tauri/gen/android/app/src/main/java/io/github/havelightii/hsnu1640/MainActivity.kt'):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(projectPath / name, target)

    def runCommand(self, *args, expected=0):
        result = subprocess.run([sys.executable, str(projectPath / 'manager.py'),
                                 'project', '--root', str(self.root), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stderr)
        return result

    def snapshot(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob('*') if path.is_file()}

    def testNameUrlAndHtmlEscaping(self):
        original = (self.root / 'config.json').read_bytes()
        title = '新班級 <script>alert("x")</script> & 公告'
        self.runCommand('set', '--app-name', 'Example & 班級 100%', '--title', title,
                        '--subtitle', '測試副標題', '--footer', '聯絡 test@example.com',
                        '--sync-url', 'https://example.com/classes/123/')
        settings = manager.loadProject(self.root)
        self.assertEqual(settings['websiteSyncUrl'], settings['syncUrl'])
        for name in ('index.html', 'src-tauri/index.html'):
            html = (self.root / name).read_text()
            self.assertIn('https://example.com/classes/123/', html)
            self.assertIn('&lt;script&gt;', html)
            self.assertNotIn(title, html)
            self.assertIn('聯絡 test@example.com', html)
        tauri = json.loads((self.root / 'src-tauri/tauri.conf.json').read_text())
        self.assertEqual(tauri['productName'], 'Example & 班級 100%')
        self.assertEqual(tauri['build']['frontendDist'], ['index.html'])
        connect = tauri['app']['security']['csp']['connect-src']
        self.assertIn('https://example.com', connect)
        self.assertNotIn('raw.githubusercontent.com', connect)
        self.assertIn('&amp;', (self.root / 'src-tauri/gen/android/app/src/main/res/values/strings.xml').read_text())
        self.assertEqual((self.root / 'config.json').read_bytes(), original)
        for script in ('test_frontend.cjs', 'test_tauri.cjs'):
            result = subprocess.run(['node', str(projectPath / 'tests' / script), str(self.root)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        before = self.snapshot()
        self.runCommand('apply')
        self.assertEqual(self.snapshot(), before)

    def testWebsiteLocalOverrideAndIdentifier(self):
        generated = self.root / 'src-tauri/gen/android/app/src/main/java/io/github/havelightii/hsnu1640/generated/Legacy.kt'
        generated.parent.mkdir()
        generated.write_text('package io.github.havelightii.hsnu1640\n// old generated source')
        self.runCommand('set', '--sync-url', 'https://example.com/new/', '--website-sync-url', './',
                        '--app-id', 'org.example.class123')
        self.assertIn('new URL("./",', (self.root / 'index.html').read_text())
        activity = self.root / 'src-tauri/gen/android/app/src/main/java/org/example/class123/MainActivity.kt'
        self.assertIn('package org.example.class123', activity.read_text())
        self.assertFalse((self.root / 'src-tauri/gen/android/app/src/main/java/io/github/havelightii/hsnu1640/MainActivity.kt').exists())
        gradle = (self.root / 'src-tauri/gen/android/app/build.gradle.kts').read_text()
        self.assertIn('namespace = "org.example.class123"', gradle)
        self.assertIn('applicationId = "org.example.class123"', gradle)
        self.assertFalse(generated.exists())
        backups = list((self.root / 'src-tauri/gen/android/.tauri/customization-backups').rglob('Legacy.kt'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), 'package io.github.havelightii.hsnu1640\n// old generated source')
        migrated = activity.parent / 'generated/Legacy.kt'
        self.assertEqual(migrated.read_text(), 'package org.example.class123\n// old generated source')
        before = self.snapshot()
        self.runCommand('apply')
        self.assertEqual(before, self.snapshot())

    def testInvalidValuesDoNotChangeFiles(self):
        before = self.snapshot()
        for option, value in [('--sync-url', 'http://example.com/'),
                              ('--sync-url', 'https://user:secret@example.com/'),
                              ('--sync-url', 'https://example.com/config.json'),
                              ('--sync-url', 'https://example.com/?token=secret'),
                              ('--sync-url', 'https://example.com:invalid/'),
                              ('--sync-url', 'https://example.com/"/'),
                              ('--website-sync-url', '../'), ('--app-id', 'org.example.class'),
                              ('--app-id', 'bad-id'), ('--app-name', ''), ('--app-name', 'line\nbreak'),
                              ('--app-name', 'name "quote"'), ('--app-name', 'name:invalid')]:
            with self.subTest(option=option, value=value):
                self.runCommand('set', option, value, expected=1)
                self.assertEqual(before, self.snapshot())

    def testPreflightFailureAndPackageConflict(self):
        htmlPath = self.root / 'src-tauri/index.html'
        htmlPath.write_text(htmlPath.read_text().replace('// project-settings:end', '// removed'))
        before = self.snapshot()
        self.runCommand('set', '--title', '不應寫入', expected=1)
        self.assertEqual(before, self.snapshot())
        shutil.copy2(projectPath / 'src-tauri/index.html', htmlPath)
        conflict = self.root / 'src-tauri/gen/android/app/src/main/java/org/example/class123/MainActivity.kt'
        conflict.parent.mkdir(parents=True)
        conflict.write_text('existing user work')
        before = self.snapshot()
        self.runCommand('set', '--app-id', 'org.example.class123', expected=1)
        self.assertEqual(before, self.snapshot())

    def testWriteFailureRollsBack(self):
        before = self.snapshot()
        settings = manager.loadProject(self.root)
        settings['appName'] = '測試'
        settings['appIdentifier'] = 'org.example.class123'
        originalReplace = manager.os.replace
        calls = 0

        def replaceOnce(source, target):
            nonlocal calls
            calls += 1
            if calls == 4:
                raise OSError('simulated write failure')
            originalReplace(source, target)

        with patch.object(manager.os, 'replace', side_effect=replaceOnce):
            with self.assertRaises(OSError):
                manager.saveProject(self.root, settings)
        self.assertEqual(before, self.snapshot())

    def testBrokenAnnouncementsAreNotReadOrCleaned(self):
        configPath = self.root / 'config.json'
        for content in ('{broken', json.dumps({'cleanupPolicy':'throughToday'})):
            configPath.write_text(content)
            self.runCommand('show')
            self.runCommand('set', '--app-name', '不清理公告')
            self.assertEqual(configPath.read_text(), content)

    def testWizardCancelAndApply(self):
        before = self.snapshot()
        with patch('builtins.input', side_effect=['新名稱', 'back']), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(manager.main(['project', '--root', str(self.root), 'wizard']), 0)
        self.assertEqual(before, self.snapshot())
        with patch('builtins.input', side_effect=['新名稱', '新標題', '', '', 'https://example.com/data/', './', '']), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(manager.main(['project', '--root', str(self.root), 'wizard']), 0)
        settings = manager.loadProject(self.root)
        self.assertEqual(settings['appName'], '新名稱')
        self.assertEqual(settings['pageTitle'], '新標題')
        self.assertEqual(settings['websiteSyncUrl'], './')


if __name__ == '__main__':
    unittest.main()
