"""班級公告統一管理工具，僅使用 Python 標準函式庫。"""
import argparse
from html import escape
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from datetime import date, datetime
from urllib.parse import urlparse

configPath = Path(__file__).resolve().with_name("config.json")
projectPath = Path(__file__).resolve().parent
projectFields = {"appName": "App 名稱", "pageTitle": "頁面標題", "subtitle": "副標題",
                 "footer": "頁尾與聯絡資訊", "syncUrl": "App／共同同步基底網址",
                 "websiteSyncUrl": "網站同步基底網址（./ 表示同目錄）", "appIdentifier": "Android App 識別碼"}
sectionFields = {
    "exams": ("date", "subject", "range"),
    "homework": ("date", "item", "link"),
    "matters": ("date", "item", "link"),
    "links": ("label", "url", "image", "hint"),
}
cleanupPolicies = {"never": "不自動刪除", "beforeToday": "自動刪除（不含當日）",
                   "throughToday": "自動刪除（包含當日）"}
fieldLabels = {"date": "日期", "subject": "科目", "range": "範圍", "item": "內容",
               "link": "相關連結", "label": "名稱", "url": "網址", "image": "圖片路徑", "hint": "提示文字"}


class CancelInput(Exception):
    pass


def emptyConfig():
    return {**{key: [] for key in sectionFields}, "calendar": {"url": ""}, "cleanupPolicy": "never"}


def parseDate(text):
    today = date.today()
    parts = text.strip().replace("-", "/").split("/")
    if len(parts) == 1:
        parts = [str(today.year), str(today.month), *parts]
    elif len(parts) == 2:
        parts = [str(today.year), *parts]
    if len(parts) != 3:
        raise ValueError("日期請使用 yyyy-mm-dd、yyyy/mm/dd、mm/dd 或 dd")
    return date(*map(int, parts)).isoformat()


def validateUrl(value):
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or any(c.isspace() for c in value):
        raise ValueError("網址必須是完整的 http:// 或 https:// 網址")


def validateRow(section, row):
    fields = sectionFields[section]
    if set(row) != set(fields) or any(not isinstance(row[key], str) for key in fields):
        raise ValueError(f"{section} 欄位不完整或不是字串")
    required = {"exams": ("date", "subject", "range"), "homework": ("date", "item"),
                "matters": ("date", "item"), "links": ("label", "url")}[section]
    for key in required:
        if not row[key].strip():
            raise ValueError(f"{fieldLabels[key]}不可空白")
    if "date" in row:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["date"]):
            raise ValueError("設定檔日期必須為 yyyy-mm-dd")
        date.fromisoformat(row["date"])
    for key in ("link", "url"):
        if row.get(key):
            validateUrl(row[key])
    if row.get("image") and not re.fullmatch(r"qr/[a-zA-Z0-9_.-]+", row["image"]):
        validateUrl(row["image"])


def loadConfig(path):
    with path.open(encoding="utf-8-sig") as source:
        config = json.load(source)
    if not isinstance(config, dict) or set(config) != set(emptyConfig()):
        raise ValueError("設定檔必須包含 exams、homework、matters、links、calendar、cleanupPolicy")
    for section in sectionFields:
        if not isinstance(config[section], list):
            raise ValueError(f"{section} 必須是陣列")
        for row in config[section]:
            validateRow(section, row)
    if not isinstance(config["cleanupPolicy"], str) or config["cleanupPolicy"] not in cleanupPolicies:
        raise ValueError("cleanupPolicy 必須是 never、beforeToday 或 throughToday")
    calendar = config["calendar"]
    if not isinstance(calendar, dict) or set(calendar) != {"url"} or not isinstance(calendar["url"], str):
        raise ValueError("calendar 必須包含 url 字串")
    if calendar["url"]:
        validateUrl(calendar["url"])
    return config


def saveConfig(path, config):
    # 同目錄暫存後原子替換，避免寫入中斷造成半份 JSON。
    tempPath = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".config-", delete=False) as target:
            tempPath = Path(target.name)
            json.dump(config, target, ensure_ascii=False, indent=2)
            target.write("\n")
            target.flush()
            os.fsync(target.fileno())
        os.replace(tempPath, path)
    finally:
        if tempPath and tempPath.exists():
            tempPath.unlink()


def applyCleanup(path, config):
    policy = config["cleanupPolicy"]
    if policy == "never":
        return
    today = date.today().isoformat()
    removed = 0
    for section in ("exams", "homework", "matters"):
        oldRows = config[section]
        config[section] = [row for row in oldRows
                           if row["date"] > today or (policy == "beforeToday" and row["date"] == today)]
        removed += len(oldRows) - len(config[section])
    if removed:
        saveConfig(path, config)
        print(f"已依 {cleanupPolicies[policy]} 清理 {removed} 筆資料並立即儲存")


def initialize(path):
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backupPath = path.with_name(f"{path.name}.{stamp}.bak")
        shutil.copy2(path, backupPath)
        print(f"已備份：{backupPath}")
    saveConfig(path, emptyConfig())
    print("已初始化：小考、作業、事項、常用連結及行事曆設定均已清空")


def validateProject(settings):
    if not isinstance(settings, dict) or set(settings) != set(projectFields):
        raise ValueError("project.json 欄位不完整")
    for key, value in settings.items():
        if not isinstance(value, str) or (key != "footer" and not value.strip()):
            raise ValueError(f"{projectFields[key]}必須是字串且不可空白")
        if any(ord(char) < 32 for char in value):
            raise ValueError(f"{projectFields[key]}不可包含換行或控制字元")
    if re.search(r'[\\/:*?"<>|]', settings["appName"]):
        raise ValueError('App 名稱不可包含 Tauri 不支援的字元：\\ / : * ? " < > |')
    for key in ("syncUrl", "websiteSyncUrl"):
        if key == "websiteSyncUrl" and settings[key] == "./":
            continue
        url = urlparse(settings[key])
        if (url.scheme != "https" or not url.hostname or url.username or url.password
                or url.query or url.fragment or not settings[key].endswith("/")
                or any(char in settings[key] for char in "\"'<>\\")):
            raise ValueError(f"{projectFields[key]}須為無帳密、查詢參數的 HTTPS 目錄網址，並以 / 結尾")
        validateUrl(settings[key])
        try:
            url.port
        except ValueError as error:
            raise ValueError("同步網址的連接埠無效") from error
    identifier = settings["appIdentifier"]
    reserved = set("""abstract as assert boolean break byte case catch char class const continue
        default do double else enum extends false final finally float for fun goto if implements
        import in instanceof int interface is long native new null object package private protected
        public return short static strictfp super switch synchronized this throw throws transient
        true try typealias typeof val var void volatile when while""".split())
    if (not re.fullmatch(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*){2,}", identifier)
            or reserved.intersection(identifier.split("."))):
        raise ValueError("App 識別碼須為至少三段的小寫 Java 套件名稱，例如 org.example.class1640")


def loadProject(root):
    settings = json.loads((root / "project.json").read_text(encoding="utf-8"))
    validateProject(settings)
    return settings


def replaceProjectText(text, pattern, replacement):
    updated, count = re.subn(pattern, lambda _: replacement, text, flags=re.DOTALL)
    if count != 1:
        raise ValueError(f"客製化標記不唯一或不存在：{pattern}")
    return updated


def saveProject(root, settings):
    validateProject(settings)
    tauriPath = root / "src-tauri/tauri.conf.json"
    tauri = json.loads(tauriPath.read_text(encoding="utf-8"))
    oldIdentifier = tauri["identifier"]
    changes = {}
    for name, baseKey in (("index.html", "websiteSyncUrl"), ("src-tauri/index.html", "syncUrl")):
        path = root / name
        text = path.read_text(encoding="utf-8")
        oldBase = re.search(r'const resourceBase = new URL\((".*?"), window.location.href\).href;', text)
        if name.startswith("src-tauri"):
            if not oldBase:
                raise ValueError("App 同步網址標記不存在")
            oldUrl = urlparse(json.loads(oldBase[1]))
        for pattern, replacement in (
            (r"<title>.*?</title>", f"<title>{escape(settings['pageTitle'])}</title>"),
            (r"<h1>.*?</h1>", f"<h1>{escape(settings['pageTitle'])}</h1>"),
            (r'<p class="subtitle">.*?</p>', f'<p class="subtitle">{escape(settings["subtitle"])}</p>'),
            (r"<footer>.*?</footer>", f"<footer>{escape(settings['footer'])}</footer>"),
        ):
            text = replaceProjectText(text, pattern, replacement)
        baseJson = json.dumps(settings[baseKey], ensure_ascii=True).replace("<", "\\u003c")
        text = replaceProjectText(text, r"// project-settings:start.*?// project-settings:end",
                                  f"// project-settings:start\n  const resourceBase = new URL({baseJson}, window.location.href).href;\n  // project-settings:end")
        changes[path] = text.encode("utf-8")
    newUrl = urlparse(settings["syncUrl"])
    csp = tauri["app"]["security"]["csp"]
    oldOrigin = f"{oldUrl.scheme}://{oldUrl.netloc}"
    newOrigin = f"{newUrl.scheme}://{newUrl.netloc}"
    sources = [source for source in csp["connect-src"].split() if source != oldOrigin]
    csp["connect-src"] = " ".join(dict.fromkeys([*sources, newOrigin]))
    tauri["productName"] = settings["appName"]
    tauri["identifier"] = settings["appIdentifier"]
    tauri["app"]["windows"][0]["title"] = settings["appName"]
    changes[tauriPath] = (json.dumps(tauri, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    androidPath = root / "src-tauri/gen/android"
    if androidPath.exists():
        gradlePath = androidPath / "app/build.gradle.kts"
        gradle = gradlePath.read_text(encoding="utf-8")
        for field in ("namespace", "applicationId"):
            gradle = replaceProjectText(gradle, rf'{field} = "[^"]+"',
                                        f'{field} = "{settings["appIdentifier"]}"')
        changes[gradlePath] = gradle.encode("utf-8")
        stringsPath = androidPath / "app/src/main/res/values/strings.xml"
        strings = stringsPath.read_text(encoding="utf-8")
        androidName = escape(json.dumps(settings["appName"], ensure_ascii=False), quote=False)
        for key in ("app_name", "main_activity_title"):
            strings = replaceProjectText(strings, rf'<string name="{key}"[^>]*>.*?</string>',
                                          f'<string name="{key}" formatted="false">{androidName}</string>')
        changes[stringsPath] = strings.encode("utf-8")
        oldPackage = Path(*oldIdentifier.split("."))
        newPackage = Path(*settings["appIdentifier"].split("."))
        activityPath = androidPath / "app/src/main/java" / oldPackage / "MainActivity.kt"
        activity = activityPath.read_text(encoding="utf-8")
        activity = replaceProjectText(activity, r"package [a-z0-9_.]+", f'package {settings["appIdentifier"]}')
        newActivityPath = androidPath / "app/src/main/java" / newPackage / "MainActivity.kt"
        if newActivityPath != activityPath:
            if newActivityPath.exists():
                raise ValueError("新 App 識別碼的 MainActivity.kt 已存在，請先處理衝突")
            changes[activityPath] = None
            generatedPath = activityPath.parent / "generated"
            backupPath = androidPath / ".tauri/customization-backups" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            for generatedFile in generatedPath.rglob("*"):
                if generatedFile.is_file():
                    original = generatedFile.read_bytes()
                    changes[backupPath / generatedFile.relative_to(androidPath)] = original
                    migratedPath = newActivityPath.parent / "generated" / generatedFile.relative_to(generatedPath)
                    if migratedPath.exists():
                        raise ValueError("新套件下已有 generated 程式碼，請先處理衝突")
                    changes[migratedPath] = original.replace(oldIdentifier.encode(), settings["appIdentifier"].encode())
                    changes[generatedFile] = None
        changes[newActivityPath] = activity.encode("utf-8")
    changes[root / "project.json"] = (json.dumps(settings, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    originals = {path: path.read_bytes() if path.exists() else None for path in changes}

    def writeFile(path, content):
        if content is None:
            path.unlink(missing_ok=True)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        tempPath = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".config-", delete=False) as target:
                tempPath = Path(target.name)
                target.write(content)
                target.flush()
                os.fsync(target.fileno())
            tempPath.chmod(path.stat().st_mode if path.exists() else 0o644)
            os.replace(tempPath, path)
        finally:
            if tempPath and tempPath.exists():
                tempPath.unlink()

    try:
        for path, content in changes.items():
            writeFile(path, content)
    except OSError:
        for path, content in originals.items():
            writeFile(path, content)
        raise
    print("已同步網站、App 與原生專案設定；公告資料未變更。App 設定需重建 APK 才會生效。")


def customizeProject(root):
    settings = loadProject(root)
    print("修改網站與 App 客製化設定；輸入 back 可取消，Enter 保留目前值。")
    for key, label in projectFields.items():
        value = readInput(f"{label} [{settings[key]}]：")
        if value:
            settings[key] = value
            if key == "syncUrl":
                settings["websiteSyncUrl"] = value
    validateProject(settings)
    saveProject(root, settings)


def showRows(config, section):
    rows = config[section]
    if section == "calendar":
        print(rows["url"] or "尚未設定行事曆")
    elif not rows:
        print("目前沒有資料")
    else:
        for index, row in enumerate(rows, 1):
            print(f"{index}. " + " | ".join(row[key] for key in sectionFields[section]))


def rowIndex(rows, value):
    index = int(value) - 1
    if not 0 <= index < len(rows):
        raise ValueError("編號超出範圍，請先用 list 查看目前編號")
    return index


def changeRow(config, section, action, values, index=None):
    rows = config[section]
    if action == "add":
        row = {key: values.get(key) or "" for key in sectionFields[section]}
    else:
        index = rowIndex(rows, index)
        row = {**rows[index], **{key: value for key, value in values.items() if value is not None}}
    if "date" in row:
        row["date"] = parseDate(row["date"])
    validateRow(section, row)
    if action == "add":
        rows.append(row)
    else:
        rows[index] = row


def setupInput():
    # GNU Readline 同時接受 BS 與 DEL；不自行實作 Unicode 刪字或游標寬度。
    try:
        import readline
    except ImportError:
        return
    if "libedit" in (readline.__doc__ or ""):
        readline.parse_and_bind("bind ^H ed-delete-prev-char")
        readline.parse_and_bind("bind ^? ed-delete-prev-char")
    else:
        readline.parse_and_bind('"\\C-h": backward-delete-char')
        readline.parse_and_bind('"\\C-?": backward-delete-char')


def readInput(prompt):
    value = input(prompt).strip()
    if value.lower() in ("back", "/back"):
        raise CancelInput()
    return value


def interactive(path):
    setupInput()
    config = loadConfig(path) if path.exists() else emptyConfig()
    applyCleanup(path, config)
    sections = {"1": "exams", "2": "homework", "3": "matters", "4": "links", "5": "calendar"}
    while True:
        print("\n1. 小考  2. 作業  3. 事項  4. 常用連結  5. 行事曆")
        print("6. 儲存並離開  7. 不儲存離開  8. 初始化（立即儲存）  9. 自動清理設定")
        print("10. 網站／App 客製化設定（立即套用）")
        print(f"目前清理模式：{cleanupPolicies[config['cleanupPolicy']]}")
        try:
            choice = readInput("請選擇（輸入 back 取消當次操作）：")
            if choice == "6":
                saveConfig(path, config)
                print(f"已儲存至 {path}")
                return
            if choice == "7":
                return
            if choice == "8":
                if readInput("將清空全部設定及未儲存修改；輸入 RESET 確認：") == "RESET":
                    initialize(path)
                    config = emptyConfig()
                else:
                    print("已取消初始化")
                continue
            if choice == "9":
                print("1. 不自動刪除  2. 自動刪除（不含當日）  3. 自動刪除（包含當日）")
                policyChoice = readInput("請選擇：")
                policies = {"1": "never", "2": "beforeToday", "3": "throughToday"}
                if policyChoice not in policies:
                    raise ValueError("無效選項")
                config["cleanupPolicy"] = policies[policyChoice]
                print("設定已修改；儲存後於下次啟動時套用")
                continue
            if choice == "10":
                customizeProject(projectPath)
                continue
            if choice not in sections:
                raise ValueError("無效選項")
            section = sections[choice]
            showRows(config, section)
            if section == "calendar":
                value = readInput("嵌入網址（Enter 保留，- 清空）：")
                if value:
                    value = "" if value == "-" else value
                    if value:
                        validateUrl(value)
                    config[section]["url"] = value
                continue
            action = readInput("1. 列出  2. 新增  3. 修改  4. 刪除：")
            if action == "1":
                continue
            if action not in ("2", "3", "4"):
                raise ValueError("無效選項")
            index = None
            if action in ("3", "4"):
                index = rowIndex(config[section], readInput("編號："))
            if action == "4":
                config[section].pop(index)
                print("已刪除（尚未儲存）")
                continue
            values = {}
            for key in sectionFields[section]:
                old = config[section][index][key] if index is not None else ""
                value = readInput(f"{fieldLabels[key]} [{old}]（Enter 保留／留空，- 清空）：")
                values[key] = "" if value == "-" else (value or old)
            changeRow(config, section, "add" if action == "2" else "edit", values,
                      index + 1 if index is not None else None)
            print("已更新（尚未儲存）")
        except CancelInput:
            print("已取消，返回主選單")
        except ValueError as error:
            print(f"輸入錯誤：{error}")


def buildParser():
    parser = argparse.ArgumentParser(description="班級公告管理；無子指令時進入互動模式")
    parser.add_argument("--config", type=Path, default=configPath, help="設定檔路徑")
    commands = parser.add_subparsers(dest="command")
    projectParser = commands.add_parser("project", help="客製化網站與 App；不讀寫或清理公告")
    projectParser.add_argument("--root", type=Path, default=projectPath, help="專案根目錄")
    projectActions = projectParser.add_subparsers(dest="action", required=True)
    for action in ("show", "apply", "wizard"):
        projectActions.add_parser(action)
    projectSet = projectActions.add_parser("set")
    for option, key in (("app-name", "appName"), ("title", "pageTitle"), ("subtitle", "subtitle"),
                        ("footer", "footer"), ("sync-url", "syncUrl"),
                        ("website-sync-url", "websiteSyncUrl"), ("app-id", "appIdentifier")):
        projectSet.add_argument(f"--{option}", dest=key)
    initParser = commands.add_parser("init", help="備份後清空所有設定")
    initParser.add_argument("--yes", action="store_true", help="確認初始化")
    for section, fields in sectionFields.items():
        sectionParser = commands.add_parser(section)
        actions = sectionParser.add_subparsers(dest="action", required=True)
        actions.add_parser("list")
        for action in ("add", "edit"):
            actionParser = actions.add_parser(action)
            if action == "edit":
                actionParser.add_argument("index", type=int)
            for key in fields:
                actionParser.add_argument(f"--{key}")
        deleteParser = actions.add_parser("delete")
        deleteParser.add_argument("index", type=int)
        if section != "links":
            actions.add_parser("prune", help="刪除今天以前的資料")
    cleanupParser = commands.add_parser("cleanup", help="管理啟動時自動清理模式")
    cleanupActions = cleanupParser.add_subparsers(dest="action", required=True)
    cleanupActions.add_parser("show")
    cleanupActions.add_parser("set").add_argument("policy", choices=cleanupPolicies)
    calendarParser = commands.add_parser("calendar")
    actions = calendarParser.add_subparsers(dest="action", required=True)
    actions.add_parser("show")
    actions.add_parser("clear")
    actions.add_parser("set").add_argument("url")
    return parser


def main(argv=None):
    parser = buildParser()
    args = parser.parse_args(argv)
    path = args.config.resolve()
    try:
        if args.command == "project":
            root = args.root.resolve()
            if args.action == "wizard":
                setupInput()
                try:
                    customizeProject(root)
                except CancelInput:
                    print("已取消客製化；所有檔案均未變更")
                return 0
            settings = loadProject(root)
            if args.action == "show":
                print(json.dumps(settings, ensure_ascii=False, indent=2))
                return 0
            if args.action == "set":
                values = {key: getattr(args, key) for key in projectFields if getattr(args, key) is not None}
                if not values:
                    raise ValueError("請指定至少一個客製化欄位，或使用 project wizard")
                if "syncUrl" in values and "websiteSyncUrl" not in values:
                    values["websiteSyncUrl"] = values["syncUrl"]
                settings.update(values)
            saveProject(root, settings)
            return 0
        if args.command is None:
            interactive(path)
            return 0
        if args.command == "init":
            if not args.yes:
                parser.error("初始化會清空全部設定；請加上 --yes 確認，或使用互動模式")
            initialize(path)
            return 0
        config = loadConfig(path)
        applyCleanup(path, config)
        section = args.command
        if section == "cleanup":
            if args.action == "show":
                print(f"{config['cleanupPolicy']}：{cleanupPolicies[config['cleanupPolicy']]}")
            else:
                config["cleanupPolicy"] = args.policy
                saveConfig(path, config)
                print("已儲存清理模式；於下次啟動時套用")
            return 0
        if args.action in ("list", "show"):
            showRows(config, section)
            return 0
        if section == "calendar":
            value = args.url if args.action == "set" else ""
            if value:
                validateUrl(value)
            config[section]["url"] = value
        elif args.action == "delete":
            config[section].pop(rowIndex(config[section], args.index))
        elif args.action == "prune":
            config[section] = [row for row in config[section] if row["date"] >= date.today().isoformat()]
        else:
            values = {key: getattr(args, key) for key in sectionFields[section]}
            changeRow(config, section, args.action, values, getattr(args, "index", None))
        saveConfig(path, config)
        print(f"已儲存至 {path}")
        return 0
    except (EOFError, KeyboardInterrupt):
        print("\n已離開；未儲存的修改已放棄")
        return 130
    except (OSError, ValueError, TypeError) as error:
        print(f"錯誤：{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
