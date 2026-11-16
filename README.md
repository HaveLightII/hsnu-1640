# 班級公告網站模板與管理資源

本專案提供可自行架設的班級公告網站模板，以及維護小考、作業、事項、常用連結與行事曆的管理工具。適合希望建立班級公告網站，並透過命令列或互動選單管理內容的使用者。  

目前 `main` 分支用於師大附中 1640 班的公告，內含該班的設定與網站識別。其他使用者可 clone 專案、初始化資料，再修改班級名稱與聯絡資訊，建立自己的公告網站。  

## 功能（Features）

- 依日期顯示小考、作業與事項；作業及事項可附相關連結。  
- 頁首顯示最近一筆未過期的重要事項。  
- 提供常用連結、選用 QR 圖片與嵌入式行事曆。  
- 使用單一 `config.json` 管理內容與自動清理模式。  
- 支援命令列引數與互動式管理，可新增、修改、列出及刪除資料。  
- 提供三種過期資料處理模式，以及備份後初始化功能。  
- 提供深色模式，標題列右側可切換，並記住使用者的主題偏好。  

## 技術組成（Tech Stack）

| 用途 | 技術 |
| --- | --- |
| 網頁 | HTML、CSS、原生 JavaScript |
| 資料儲存 | UTF-8 JSON |
| 管理工具 | Python 3.9 以上，僅使用標準函式庫 |
| 前端邏輯測試 | Node.js 18 以上；不影響網站或管理工具執行 |
| 網站託管 | GitHub Pages 或其他靜態網站服務 |

## 開始使用（Installation）

準備 Git 與 Python 3.9 以上。管理工具僅使用 Python 標準函式庫，不需要安裝額外 Python 套件。  

### 取得模板並初始化

```bash
git clone https://github.com/havelightii/hsnu-1640.git my-class-board
cd my-class-board
python3 manager.py init --yes
python3 manager.py project wizard
python3 manager.py
```

- 1：將專案複製至自己的 `my-class-board` 資料夾；可自行更改資料夾名稱。  
- 2：進入專案目錄。  
- 3：備份並清空複製過來的小考、作業、事項、常用連結與行事曆設定，將自動清理模式設為 `never`。  
- 4：設定自己的 App 名稱、網站標題、同步網址、聯絡資訊與 App 識別碼。  
- 5：開啟管理選單，加入自己班級的內容，完成後選擇「儲存並離開」。  

初始化只影響本機這份專案，不會修改來源儲存庫。請在新複製的模板中執行；已有自用資料時，初始化也會清空那些資料。  

### 修改班級識別與素材

初始化只處理公告；網站與 App 識別由獨立的 `project.json` 管理，可透過精靈或指令一次套用：  

```bash
python3 manager.py project show
python3 manager.py project wizard
python3 manager.py project set --app-name "我的班級" --title "班級公告" --subtitle "我的學校 123 班" --footer "聯絡：class@example.com" --app-id org.example.class123 --sync-url https://raw.githubusercontent.com/YOUR_NAME/YOUR_REPO/main/ --website-sync-url ./
python3 manager.py project apply
```

`show` 查看設定；`wizard` 逐項輸入，Enter 保留、`back` 取消；`set` 更新指定欄位並立即套用；手動編輯 `project.json` 後使用 `apply`。這些子指令不讀寫 `config.json`，也不會執行公告清理；一般互動選單第 10 項也提供同一精靈，但進入一般選單時仍依既有規則套用公告清理。  

`--sync-url` 是含 `config.json` 與 `qr/` 的 HTTPS 目錄網址，須以 `/` 結尾；預設同步更新 App 及網站來源。若網站要繼續讀同目錄公告，另加 `--website-sync-url ./`。精靈修改共同網址後，下一題也可將網站來源改回 `./`。跨網域來源必須允許 CORS；App CSP 的連線來源會同步更新。網址不可包含帳密、權杖查詢參數或 fragment。  

| 欄位 | 同步位置 |
| --- | --- |
| `appName` | Tauri productName、視窗名稱、Android launcher 名稱 |
| `pageTitle`、`subtitle`、`footer` | 網站與 App HTML 的標題、副標題及頁尾 |
| `syncUrl` | App 公告與相對圖片來源、Tauri 連線 CSP |
| `websiteSyncUrl` | 網站公告與相對圖片來源；`./` 表示同目錄 |
| `appIdentifier` | Tauri identifier、Android applicationId／namespace／MainActivity 套件與路徑 |

App 識別碼使用至少三段的小寫 Java 套件名稱，不可使用保留字。更換識別碼會成為另一個 App；保留 Rust crate 名稱可繼續沿用建置設定。舊套件下的 `generated` 程式碼會備份至 Android `.tauri/customization-backups/`，再遷移到新套件並更新套件名稱，避免殘留程式碼影響重建。設定套用前會先檢查全部目標，寫入失敗時嘗試復原；不會重設公告或重新初始化 Android 專案。請將設定與產生的檔案一起提交。App 變更需重建 APK；網站變更需重新部署靜態檔案。  

首次使用也請調整以下素材與內容：  

| 位置 | 要修改的內容 |
| --- | --- |
| `icon.jpg` | 更換 App 圖示來源，再用 Tauri CLI 產生原生圖示 |
| `qr/` | 更換或移除不屬於自己班級的 QR 圖片 |
| 管理工具的「常用連結」與「行事曆」 | 填入自己的網址、圖片路徑與行事曆嵌入網址 |

需要調整外觀時，可編輯兩份 HTML 中的 CSS；保留 `project-settings` 標記及標題、頁尾結構，供管理工具套用客製化。  

## 本機預覽（Run Locally）

在自己的專案目錄執行：  

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

- 1：啟動本機預覽伺服器；以 Ctrl+C 停止。  

瀏覽器開啟 [本機預覽](http://localhost:8000)，確認公告、班級名稱、聯絡資訊、連結及行事曆都符合自己的需求。請透過 HTTP 預覽，不要直接以檔案方式開啟 `index.html`。  

## 設定說明（Documentation）

| 檔案或資料夾 | 用途 |
| --- | --- |
| `index.html` | 公告頁面、樣式及資料載入邏輯 |
| `config.json` | 公告內容、常用連結、行事曆及清理設定 |
| `manager.py` | 命令列與互動式管理工具 |
| `qr/` | 常用連結使用的 QR 圖片 |
| `tests/` | Python 與前端邏輯測試 |

`config.json` 包含以下設定；建議透過管理工具維護，避免手動輸入格式錯誤。  

| 設定鍵 | 欄位或內容 |
| --- | --- |
| `exams` | 小考陣列：`date`、`subject`、`range` |
| `homework` | 作業陣列：`date`、`item`、`link` |
| `matters` | 事項陣列：`date`、`item`、`link` |
| `links` | 常用連結陣列：`label`、`url`、`image`、`hint` |
| `calendar` | 行事曆物件：`url` |
| `cleanupPolicy` | `never`、`beforeToday` 或 `throughToday` |

儲存日期使用 `yyyy-mm-dd`。網址須為完整 HTTP／HTTPS 網址；選用欄位無內容時儲存為空字串。  

## 使用方式（Usage / Examples）

### 互動模式

```bash
python3 manager.py
```

- 1：開啟主選單，可管理小考、作業、事項、常用連結、行事曆、自動清理設定及初始化。  

新增、修改、刪除會先保留在記憶體；選「儲存並離開」才寫入。修改欄位按 Enter 保留原值，輸入 `-` 清空選用欄位。必填欄位不允許清空。日期接受 `yyyy-mm-dd`、`yyyy/mm/dd`、`mm/dd` 或 `dd`；省略年、月時以執行電腦的當日年月補齊。  

輸入 `back` 或 `/back` 會取消當次操作；欄位尚未全部驗證成功前不會套用部分修改。Ctrl+C 或輸入結束會離開並放棄尚未儲存的互動修改。  

**例外：啟動時的自動清理與已確認的初始化會立即寫入；之後選「不儲存離開」或中斷不會還原這兩類操作。** 初始化前未儲存的互動修改會被放棄；備份保存的是磁碟上原有的設定。  

互動輸入支援 BS／DEL 兩種 Backspace 鍵碼。Python 若未提供 Readline，退格顯示能力取決於終端機。  

### 命令列操作

以下日期、內容及網址為操作範例，請換成自己班級的資料。指令會實際修改設定，依需求選擇執行即可。引數模式的成功修改會立即儲存。編號從 1 開始，依設定檔順序排列；刪除或自動清理後可能改變，請先重新列出。網頁顯示則會依日期排序。  

### 小考

```bash
python3 manager.py exams list
python3 manager.py exams add --date 2026-12-01 --subject "英文" --range "第五課"
python3 manager.py exams edit 1 --range "第五課與習作"
python3 manager.py exams delete 1
```

- 1：列出小考及管理編號。  
- 2：新增小考。  
- 3：修改第 1 筆範圍，其餘欄位保留。  
- 4：刪除第 1 筆。  

### 作業與事項

```bash
python3 manager.py homework list
python3 manager.py homework add --date 2026-12-02 --item "國文作文" --link "https://example.com/homework"
python3 manager.py homework edit 1 --date 2026-12-03 --link ""
python3 manager.py homework delete 1
python3 manager.py matters list
python3 manager.py matters add --date 2026-12-04 --item "繳交回條"
```

- 1：列出作業。  
- 2：新增含連結的作業；`--link` 可省略。  
- 3：修改日期並清空連結。  
- 4：刪除第 1 筆作業。  
- 5：列出事項。  
- 6：新增事項；修改、刪除語法與作業相同，將 `homework` 改為 `matters`。  

### 常用連結

```bash
python3 manager.py links list
python3 manager.py links add --label "學校首頁" --url "https://example.com/" --hint "開啟學校網站"
python3 manager.py links edit 1 --label "積分查詢" --image "qr/points.png"
python3 manager.py links delete 1
```

- 1：列出常用連結。  
- 2：新增連結；圖片與提示文字可省略。  
- 3：修改名稱與圖片路徑。  
- 4：刪除第 1 筆連結設定。  

圖片接受 `qr/檔名` 的相對路徑（檔名限英數字、底線、連字號及句點）或完整 HTTP／HTTPS 網址。程式管理圖片路徑，不產生 QR code；若變更目標網址，請同步更新 QR 圖片，或以 `--image ""` 移除圖片。  

### 行事曆

```bash
python3 manager.py calendar show
python3 manager.py calendar set "https://calendar.google.com/calendar/embed?src=YOUR_CALENDAR_ID&ctz=Asia%2FTaipei"
python3 manager.py calendar clear
```

- 1：顯示目前行事曆嵌入網址。  
- 2：設定網址；將 `YOUR_CALENDAR_ID` 換成實際行事曆 ID，或直接使用原行事曆的完整嵌入網址。整段網址需加引號。  
- 3：清空行事曆設定。  

此功能管理頁面上的嵌入網址，不會新增或刪除 Google 行事曆內的活動。行事曆本身須允許目標訪客查看；外部網站也可能禁止 iframe 嵌入。  

## 自動清理設定

設定存於 `config.json` 的 `cleanupPolicy`。  

| 設定值 | 選項 | 啟動時刪除條件 |
| --- | --- | --- |
| `never` | 不自動刪除（預設） | 不刪除 |
| `beforeToday` | 自動刪除（不含當日） | 日期早於今天 |
| `throughToday` | 自動刪除（包含當日） | 日期早於或等於今天 |

```bash
python3 manager.py cleanup show
python3 manager.py cleanup set never
python3 manager.py cleanup set beforeToday
python3 manager.py cleanup set throughToday
```

- 1：查看目前模式。  
- 2：設定不自動刪除。  
- 3：設定自動刪除但保留今天。  
- 4：設定自動刪除且包含今天。  

以上三個 `set` 指令是互斥選項，選一個即可。新的模式儲存後在**下次啟動**生效。互動模式透過主選單第 9 項選擇，仍需選「儲存並離開」。  

每次正常啟動，包括列出資料、查看清理模式或變更模式，都會先按磁碟上既有模式清理小考、作業、事項並立即存檔。`--help`、引數解析錯誤及 `init` 不會先執行自動清理。執行「改成不自動刪除」的指令時，這一次仍會先按舊模式清理；若要保留現有資料，請先在程式外備份 `config.json`，或在啟動前直接把檔案中的模式改成 `never`。  

「今天」採執行電腦的本機日期；Termux、Ubuntu 或 WSL2 請確認時區設定符合預期。自動清理只在管理程式啟動時執行，靜態網頁不會修改設定檔。常用連結及行事曆不會被清理；自動清理不另行建立備份。  

若要單次清除今天以前的某類資料，不變更自動模式：  

```bash
python3 manager.py exams prune
python3 manager.py homework prune
python3 manager.py matters prune
```

- 1：清除過期小考。  
- 2：清除過期作業。  
- 3：清除過期事項。  

這三個指令本身都保留當日；但若啟動模式已是 `throughToday`，當日資料會在執行指令前就被自動清除。  

網頁顯示規則：小考保留過期資料並淡化，作業與事項只顯示今天及未來；公告列顯示最近一筆未過期事項。網頁日期依訪客裝置本機日期計算。  

## 初始化與復原

```bash
python3 manager.py init --yes
```

- 1：備份現有設定後立即清空五類內容，並重設清理模式為 `never`；省略 `--yes` 會拒絕執行。  

備份名稱類似 `config.json.20261116-153000-123456.bak`，位於設定檔同一資料夾。初始化不刪除 HTML、程式、QR 圖片或備份檔，也不會填入範例資料。若設定檔不存在，則直接建立空設定；若設定檔損毀，也能先備份再初始化。  

復原時請把實際備份檔名代入：  

```bash
cp config.json.20261116-153000-123456.bak config.json
```

- 1：恢復備份設定；若備份中啟用了自動清理，下一次啟動仍會按該模式清理，必要時先將 `cleanupPolicy` 改成 `never`。  

## 執行測試（Running Tests）

在專案根目錄執行：  

```bash
python3 -m unittest discover -s tests -v
node tests/test_frontend.cjs
node tests/test_theme.cjs
```

- 1：執行 Python 測試，涵蓋資料操作、行事曆、輸入驗證、互動取消、初始化備份與自動清理；測試使用暫存設定，不會修改正式資料。  
- 2：執行前端邏輯測試，涵蓋區塊順序、資料渲染、連結、文字跳脫、空資料及載入錯誤；需要 Node.js 18 以上。  

- 3：驗證主題初始選擇、切換、偏好儲存、系統變更與儲存受限時的操作。  

前端測試使用固定資料及 DOM 替身，不會讀寫正式公告；不包含實際瀏覽器排版、QR 圖片內容或外部行事曆的可用性檢查。這些項目請透過本機預覽確認。  

## Android App

`src-tauri/` 提供 Tauri 2 Android App，前端僅內建 `src-tauri/index.html`，`frontendDist` 使用 `["index.html"]`。預設公告設定與相對 `qr/` 圖片讀取 `https://raw.githubusercontent.com/havelightii/hsnu-1640/main/`，可用 `manager.py project` 客製化；本機 `config.json` 與 `project.json` 不會打包進 App。一般公告更新推送到來源 main 後，可在 App 重新整理，仍可能受遠端快取傳播時間影響。  

App 會在開啟、回到前景、網路恢復及按下重新整理時更新；請求逾時為 15 秒，失敗時清除畫面上的前次公告，不持久儲存公告。外部連結交由 Opener 開啟，行事曆另提供瀏覽器入口。網站與 App 各自維護 HTML，介面修改後需要重建 APK。App 與 Android launcher 圖示由根目錄 `icon.jpg` 產生，保留原圖比例並補齊為正方形；Android launcher 使用高解析度 WebP，Tauri 內嵌視窗圖示縮至 64×64，避免多帶一份大型 RGBA 點陣資料。重新產生 PNG 圖示後，可安裝 libwebp 並執行 `sh scripts/optimize-android-icons.sh`，同時完成品質 85 的 WebP 轉換與視窗圖示縮小。  

### 建置精簡 ARM64-v8a APK

發布下載只提供 ARM64-v8a。使用 release 模式，Rust 啟用 `opt-level = "z"`、LTO、單一 codegen unit、panic abort 及移除符號；Tauri 移除未授權的原生命令，Android 啟用 R8、資源縮減與原生程式庫壓縮，套件原生語系保留預設、英文與繁體中文。若客製化其他語言，可調整 Android `localeFilters`；網頁文字不受這個設定影響。前端仍只內建一個 HTML，沒有打包 WebView 引擎。設定依據：Tauri. (n.d.). [App size](https://v2.tauri.app/concept/size/). Android Developers. (n.d.). [Reduce your app size](https://developer.android.com/topic/performance/reduce-apk-size).  

```bash
cargo tauri android build --apk --target aarch64 --split-per-abi
```

原生專案與工具鏈設定同下方 debug 建置說明。此命令產生 `src-tauri/gen/android/app/build/outputs/apk/arm64/release/app-arm64-release-unsigned.apk`，不建置其他 ABI，也不產生 AAB。未簽章的 APK 須先簽章才能安裝；release 編譯模式與簽章身分是兩件事。此專案的 GitHub 測試下載沿用既有 Android debug 簽章，未建立正式上架身分。  

若本機已有 Android debug keystore，可使用既有工具簽署：  

```bash
java -jar ~/bin/uber-apk-signer.jar --apks src-tauri/gen/android/app/build/outputs/apk/arm64/release/app-arm64-release-unsigned.apk --ksDebug ~/.android/debug.keystore --out /tmp/hsnu-signed
```

正式發佈到商店時，需另行管理此 App 的正式簽章；不要將正式金鑰、密碼或 keystore 設定提交到 Git。  

### 建置 debug APK

沿用既有 JDK 17、Android SDK 與單一版本 NDK，設定 `JAVA_HOME`、`ANDROID_HOME`、`NDK_HOME`。目前原生專案使用 Android SDK 37、Gradle 9.6.1、Android Gradle Plugin 9.3.1；最低 Android API 為 24。Cargo CLI 須在 PATH 中，讓 Gradle 能呼叫 `cargo tauri`。  

```bash
cargo install tauri-cli --version 2.12.1 --locked
rustup target add aarch64-linux-android
cargo tauri android build --debug --apk --target aarch64
```

Android 原生專案已納入 `src-tauri/gen/android/`，不需再次初始化。ARM64 debug APK 位於 `src-tauri/gen/android/app/build/outputs/apk/universal/debug/app-universal-debug.apk`，使用 Android debug 簽章，供測試安裝。不要將 debug APK 作為正式上架版本，也不要提交簽章金鑰或本機 SDK 設定。  

```bash
node tests/test_tauri.cjs
node tests/test_theme.cjs src-tauri/index.html
adb install -r src-tauri/gen/android/app/build/outputs/apk/universal/debug/app-universal-debug.apk
```

安裝前先確認裝置；若已有相同識別碼但不同簽章的 App，保留原 App 並處理簽章來源，避免直接移除造成資料損失。改供其他班級使用時，以 `manager.py project wizard` 同步調整來源、班級文字與 App 識別碼，再重建 APK。  

設定與命令參考：Tauri. (n.d.). [Configuration](https://v2.tauri.app/reference/config/). Tauri. (n.d.). [Command line interface](https://tauri.app/reference/cli/).  

## 發佈自己的網站（Deployment）

此專案不需要建置程序，可由靜態網站服務提供 `index.html`、`config.json` 與 `qr/`。請將客製化結果放在自己的儲存庫，並依所選服務設定網站發佈來源。  

### 設定自己的遠端儲存庫

clone 後的 `origin` 仍指向來源專案。請先在自己的 GitHub 帳號建立空白儲存庫，再將下列 `YOUR_ACCOUNT` 與 `YOUR_REPOSITORY` 換成自己的帳號及儲存庫名稱：  

```bash
git remote set-url origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git remote -v
git add index.html config.json qr/
git commit -m "設定班級公告網站"
git push -u origin HEAD
```

- 1：將推送目的地改為自己的儲存庫。  
- 2：確認遠端網址已指向自己的帳號與專案。  
- 3：加入已客製化的頁面、設定及 QR 圖片變更。  
- 4：建立提交；Git 需已設定提交者姓名與電子郵件。  
- 5：將目前分支推送至自己的遠端儲存庫，並設定追蹤關係；需要該儲存庫的寫入權限。  

若使用 GitHub Pages，請在自己的儲存庫啟用 Pages，選擇實際推送的分支與包含 `index.html` 的根目錄作為發佈來源。發佈完成後，以服務提供的網址檢查網站。  

### 日常內容更新

透過 `manager.py` 儲存內容後，在自己的專案目錄執行：  

```bash
git diff -- config.json
git add config.json
git commit -m "更新班級公告"
git push
```

- 1：檢查設定差異。  
- 2：加入設定檔。  
- 3：建立提交。  
- 4：推送至自己的儲存庫；確認發佈完成後，再重新整理網站。  

若更換 QR 圖片或修改頁面，也需提交對應檔案。管理程式只修改本機檔案，不會自行提交 Git 或推送遠端。  

## 常見問題（FAQ）

### 如何切換深色模式？

點選標題列右側的「深色模式」按鈕。首次開啟時依裝置的深淺色偏好顯示；手動切換後，會在目前瀏覽器記住選擇。若瀏覽器不允許儲存，仍可切換，但重新載入後不保留選擇。主題偏好不會修改 `config.json`。  

QR 圖片保留原色，Google 行事曆等外部嵌入內容不受本站主題控制。  


### 為什麼 clone 後仍看到師大附中 1640 班的內容？

來源專案的 `main` 分支正在用於該班公告。請在自己的 clone 中初始化公告，再執行 `python3 manager.py project wizard`，同步修改網站與 App 的文字、來源及識別碼，並更換 QR 圖片與連結。初始化公告不會重設 `project.json`。  


### 如何查看完整指令或指定其他設定檔？

```bash
python3 manager.py --help
python3 manager.py homework add --help
python3 manager.py --config ./test-config.json cleanup show
```

- 1：查看所有子指令。  
- 2：查看新增作業的可用引數。  
- 3：使用另一份已存在且格式有效的設定檔；`--config` 必須放在子指令之前。  

預設設定檔位於 `manager.py` 所在資料夾，不受目前工作目錄影響。  

### 為什麼網站顯示讀取設定失敗？

確認使用 HTTP／HTTPS 開啟網頁、`config.json` 位於 `index.html` 同一目錄，且 JSON 格式及必要欄位完整。  

### 為什麼已修改公告，網站卻沒有更新？

確認已儲存設定、提交並推送至網站的發佈來源，且發佈流程完成，再重新整理頁面。  

### 為什麼選擇不儲存離開，資料仍然減少？

啟動時的自動清理會立即寫入磁碟。「不儲存離開」僅放棄尚未儲存的互動修改，不會還原自動清理或已確認的初始化。  

### 清空行事曆會刪除 Google 行事曆活動嗎？

不會。程式只管理網站的行事曆嵌入網址，不操作 Google 行事曆活動。  

## 聯絡與回饋（Feedback / Support）

模板或管理工具的問題，可透過[來源專案](https://github.com/havelightii/hsnu-1640)回報，並附上操作步驟、錯誤訊息及使用環境。  

各班公告的內容問題，請聯絡該網站的維護者；公告仍以所屬學校的正式公告為準。架站時請將頁尾聯絡資訊換成自己的聯絡方式。  
