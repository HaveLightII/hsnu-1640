# 師大附中 1640 班公告網頁：更新與操作步驟

本次更新以提供的 `hsnu-1640.tar.gz` 快照為基準；其 Git HEAD 為 `8ee62227d7cfbcefffdb89f56080869b4fa64f82`。補丁保留 9 筆小考、7 筆事項、4 個常用連結及原 Google 行事曆網址，新增的作業清單為空。  

## 1. 更新內容

- 在「近期小考」與「近期事項」之間加入「近期作業」，共用事項的日期、內容與選用連結版型。  
- 將兩份 CSV 和 HTML 中的連結、行事曆設定整合至 UTF-8 `config.json`。使用 JSON 是為了在單一檔案中保留不同類型資料的欄位及清理模式。  
- 用 `manager.py` 取代 `calenderManager.py`、`importantManager.py`；支援命令列引數及無引數互動模式，僅使用 Python 標準函式庫。  
- 支援 BS、DEL 兩種 Backspace 鍵碼，使用 Readline 處理中文刪字；輸入 `back` 或 `/back` 可取消當次操作並回主選單。  
- 初始化會先備份現有設定，再清空小考、作業、事項、常用連結、行事曆，並將自動清理模式重設為「不自動刪除」。  
- 新增可管理的啟動清理模式。更新套用時預設不刪除任何資料，包含原有過期事項。  

## 2. 套用補丁

需要 Python 3.9 以上與 Git。以下命令適用於 Ubuntu 或 WSL2 的 Bash。將壓縮檔及 `hsnu-1640-unified.patch` 放在同一個工作目錄，且確認該處尚無同名 `hsnu-1640` 資料夾：  

```bash
tar --exclude="hsnu-1640/.git" -xzf hsnu-1640.tar.gz
cp -a hsnu-1640 hsnu-1640-before-update
cd hsnu-1640
git init
git apply --check ../hsnu-1640-unified.patch
git apply ../hsnu-1640-unified.patch
python3 -m unittest discover -s tests -v
python3 manager.py cleanup show
```

- 1：解壓縮原始快照，但排除不完整的 Git 資料。  
- 2：建立完整備份；若已存在此備份名稱，請改用另一個名稱。  
- 3：進入專案目錄。  
- 4：建立本機測試用 Git 工作目錄，供補丁操作使用；此目錄不含原儲存庫歷史，不要直接推送。  
- 5：先檢查補丁是否可完整套用；若失敗，停止，不要繼續套用。  
- 6：套用更新，包含已移轉的設定資料。  
- 7：執行八項 Python 測試；測試使用暫存設定，不改動實際資料。  
- 8：確認初始模式為 `never`。  

快照內部分 Git 物件是指向原 Termux／proot 環境的失效符號連結，因此上述步驟排除 `.git`。補丁以快照的實際檔案為基準，不依賴那些物件。  

若要更新另一份已經變動過的專案，請先備份並比對其內容；此補丁只保證適用於提供的快照。不要使用強制覆蓋方式處理衝突。  

`README.pdf` 是快照中的舊版說明，本次保留但未更新；以此 `README.md` 為準。  

## 3. 互動模式

```bash
python3 manager.py
```

- 1：開啟主選單，可管理小考、作業、事項、常用連結、行事曆、自動清理設定及初始化。  

新增、修改、刪除會先保留在記憶體；選「儲存並離開」才寫入。修改欄位按 Enter 保留原值，輸入 `-` 清空選用欄位。必填欄位不允許清空。日期接受 `yyyy-mm-dd`、`yyyy/mm/dd`、`mm/dd` 或 `dd`；省略年、月時以執行電腦的當日年月補齊。  

輸入 `back` 或 `/back` 會取消當次操作；欄位尚未全部驗證成功前不會套用部分修改。Ctrl+C 或輸入結束會離開並放棄尚未儲存的互動修改。  

**例外：啟動時的自動清理與已確認的初始化會立即寫入；之後選「不儲存離開」或中斷不會還原這兩類操作。** 初始化前未儲存的互動修改會被放棄；備份保存的是磁碟上原有的設定。  

退格修正針對 Backspace（BS／DEL），並非瀏覽器或手機的系統返回鍵。Python 若未提供 Readline，程式仍可使用標準輸入，但退格顯示能力取決於終端機。  

## 4. 命令列操作

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

## 5. 自動清理模式

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

「今天」採執行電腦的本機日期；Ubuntu／WSL2 請確認時區設定符合預期。自動清理只在管理程式啟動時執行，靜態網頁不會修改設定檔。常用連結及行事曆不會被清理；自動清理不另行建立備份。  

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

網頁維持原有行為：小考保留過期資料並淡化，作業與事項只顯示今天及未來；公告列顯示最近一筆未過期事項。網頁日期依訪客裝置本機日期計算。  

## 6. 初始化與復原

```bash
python3 manager.py init --yes
```

- 1：備份現有設定後立即清空五類內容，並重設清理模式為 `never`；省略 `--yes` 會拒絕執行。  

備份名稱類似 `config.json.20261116-153000-123456.bak`，位於設定檔同一資料夾。初始化不刪除 HTML、程式、QR 圖片或備份檔，也不會重建原範例內容。若設定檔不存在，則直接建立空設定；若設定檔損毀，也能先備份再初始化。  

復原時請把實際備份檔名代入：  

```bash
cp config.json.20261116-153000-123456.bak config.json
```

- 1：恢復備份設定；若備份中啟用了自動清理，下一次啟動仍會按該模式清理，必要時先將 `cleanupPolicy` 改成 `never`。  

## 7. 預覽、測試與發佈

```bash
python3 -m unittest discover -s tests -v
node tests/test_frontend.cjs
python3 -m http.server 8000 --bind 127.0.0.1
```

- 1：執行八項 Python 測試，包含四類資料操作、行事曆、錯誤輸入、取消操作、初始化備份及三種清理模式。  
- 2：執行前端邏輯測試，需要 Node.js 18 以上；管理工具及網頁執行本身不需要 Node.js。  
- 3：啟動本機預覽伺服器；以 Ctrl+C 停止。  

瀏覽器開啟 <http://localhost:8000>。請透過 HTTP 預覽，不要直接雙擊 HTML，以免 `fetch` 受到本機檔案存取限制。  

請檢查桌面及手機寬度下的五個區塊順序，新增測試作業後確認日期／內容／連結樣式與事項一致，並確認原有常用連結、QR 圖片和 Google 行事曆可用。初始化驗證請使用設定副本，避免清除正式內容：  

```bash
cp config.json /tmp/hsnu-config-test.json
python3 manager.py --config /tmp/hsnu-config-test.json init --yes
python3 manager.py --config /tmp/hsnu-config-test.json
```

- 1：建立測試用設定。  
- 2：初始化測試副本，不改正式設定。  
- 3：使用測試副本進入互動模式。  

交付前已通過八項 Python 測試、前端 DOM 替身邏輯測試，以及 PTY 下 BS／DEL 兩種鍵碼的中文退格與存檔測試。前端邏輯驗證涵蓋區塊順序、資料渲染、作業連結、文字跳脫、空設定及載入錯誤。實際 Chromium 啟動受執行環境限制而失敗，因此尚未完成真實瀏覽器視覺排版、手機顯示或外部行事曆服務驗證；DOM 替身測試不代表已完成上述檢查。  

確認預覽後，請在原本可正常使用的 Git 儲存庫套用補丁並提交。若沒有完整的本機儲存庫，可在壓縮檔與補丁所在目錄另行複製遠端專案；以下網址取自快照中的 origin 設定：  

```bash
git clone https://github.com/havelightii/hsnu-1640.git hsnu-1640-publish
cd hsnu-1640-publish
git apply --check ../hsnu-1640-unified.patch
git apply ../hsnu-1640-unified.patch
python3 -m unittest discover -s tests -v
git diff --stat
git status --short
git add index.html config.json manager.py README.md .gitignore tests calender.csv important.csv calenderManager.py importantManager.py
git commit -m "Unify class notice configuration and management"
git push
```

- 1：取得具有完整歷史的獨立儲存庫；需能存取該遠端專案。  
- 2：進入發佈工作目錄。  
- 3：檢查遠端目前內容是否仍符合補丁；若失敗，停止並比對衝突，不要強制套用。  
- 4：套用更新。  
- 5：重新驗證 Python 功能。  
- 6：查看已追蹤檔案差異摘要。  
- 7：確認新增檔案及舊檔刪除均符合預期。  
- 8：加入本次修改；初始化備份與 Python 快取已排除。  
- 9：建立提交；Git 使用者姓名與信箱需已設定。  
- 10：以具有寫入權限的帳號推送目前分支；沿用原專案既有 Pages 發佈方式。  

若預覽期間已新增正式資料，提交前將測試工作目錄的 `config.json` 複製到發佈工作目錄，先比對確認沒有覆蓋遠端較新的資料。不要把已初始化的測試副本當成正式設定。  

日常更新通常只需提交 `config.json`；若更換 QR 圖片，也一併提交對應圖片。確認遠端 Pages 發佈成功後重新整理網站。  

## 8. 其他操作與還原補丁

```bash
python3 manager.py --help
python3 manager.py homework add --help
python3 manager.py --config /tmp/hsnu-config-test.json cleanup show
```

- 1：查看全部命令。  
- 2：查看單一操作引數。  
- 3：指定另一份設定檔；全域 `--config` 需放在子指令之前，預設則使用 `manager.py` 所在資料夾的 `config.json`，不受目前工作目錄影響。  

若套用後尚未修改任何檔案，可在專案根目錄檢查並反向套用：  

```bash
git apply --reverse --check ../hsnu-1640-unified.patch
git apply --reverse ../hsnu-1640-unified.patch
```

- 1：確認目前檔案仍可完整反向套用。  
- 2：還原至快照內容。  

若已經用管理程式修改設定，請先另存新的 `config.json`，不要強制反向套用；可改用更新前的完整備份資料夾復原。  
