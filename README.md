# 師大附中 1640 班公告網頁

提供師大附中 1640 班查看近期小考、作業、事項、常用連結與行事曆的靜態網站。管理者可透過 Python 程式維護公告內容，並以 GitHub Pages 發佈。  

## 功能（Features）

- 依日期顯示小考、作業與事項；作業及事項可附相關連結。  
- 頁首顯示最近一筆未過期的重要事項。  
- 提供常用連結、選用 QR 圖片與嵌入式行事曆。  
- 使用單一 `config.json` 管理內容與自動清理模式。  
- 支援命令列引數與互動式管理，可新增、修改、列出及刪除資料。  
- 提供三種過期資料處理模式，以及備份後初始化功能。  

## 技術組成（Tech Stack）

| 用途 | 技術 |
| --- | --- |
| 網頁 | HTML、CSS、原生 JavaScript |
| 資料儲存 | UTF-8 JSON |
| 管理工具 | Python 3.9 以上，僅使用標準函式庫 |
| 前端邏輯測試 | Node.js 18 以上；不影響網站或管理工具執行 |
| 網站託管 | GitHub Pages 或其他靜態網站服務 |

## 本機執行（Run Locally）

準備 Git 與 Python 3.9 以上，取得專案後啟動本機預覽：  

```bash
git clone https://github.com/havelightii/hsnu-1640.git
cd hsnu-1640
python3 -m http.server 8000 --bind 127.0.0.1
```

- 1：複製專案。  
- 2：進入專案資料夾。  
- 3：啟動預覽伺服器；以 Ctrl+C 停止。  

瀏覽器開啟 [本機預覽](http://localhost:8000)。請透過 HTTP 預覽，不要直接以檔案方式開啟 `index.html`。已有專案者直接在專案目錄啟動伺服器即可。  

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

以下範例會實際修改設定；請依需求選擇執行，不必全部執行。引數模式的成功修改會立即儲存。編號從 1 開始，依設定檔順序排列；刪除或自動清理後可能改變，請先重新列出。網頁顯示則會依日期排序。  

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
python3 manager.py links add --label "學校首頁" --url "https://www.hs.ntnu.edu.tw/" --hint "開啟學校網站"
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
```

- 1：執行 Python 測試，涵蓋資料操作、行事曆、輸入驗證、互動取消、初始化備份與自動清理；測試使用暫存設定，不會修改正式資料。  
- 2：執行前端邏輯測試，涵蓋區塊順序、資料渲染、連結、文字跳脫、空資料及載入錯誤；需要 Node.js 18 以上。  

前端測試使用 DOM 替身，不包含實際瀏覽器排版、QR 圖片內容或外部行事曆的可用性檢查。這些項目請透過本機預覽確認。  

## 發佈（Deployment）

此專案不需要建置程序，可由靜態網站服務提供 `index.html`、`config.json` 與 `qr/`。GitHub Pages 請使用儲存庫實際設定的發佈來源。  

日常管理完成後，將設定提交並推送：  

```bash
git diff -- config.json
git add config.json
git commit -m "更新班級公告"
git push
```

- 1：檢查設定差異。  
- 2：加入設定檔。  
- 3：建立提交。  
- 4：推送目前分支；確認網站發佈流程成功後，再重新整理頁面。  

若更換 QR 圖片，也需提交對應圖片。管理程式只修改本機檔案，不會自行提交 Git 或推送遠端。  

## 常見問題（FAQ）

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

公告內容以學校正式公告為準。日程如有缺漏，可聯絡 [310394@gs.hs.ntnu.edu.tw](mailto:310394@gs.hs.ntnu.edu.tw)。  
