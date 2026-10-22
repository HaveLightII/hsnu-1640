# 師大附中 1640 班公告網頁

此專案是以 GitHub Pages 發佈的班級公告網頁，可 fork 後依需求客製化。

## 網頁內容

- `index.html`：公告首頁，顯示近期小考、近期事項、常用連結與 Google 行事曆。
- `calender.csv`：近期小考資料，由 `calenderManager.py` 管理。
- `important.csv`：近期事項資料，由 `importantManager.py` 管理。

## 管理近期事項

在專案根目錄執行：

```sh
python3 importantManager.py
```

控制器可列出、新增、修改及刪除事項，並將資料儲存至 `important.csv`。新增或修改截止日可輸入 `yyyy/mm/dd`、`mm/dd` 或 `dd`；連結可留空，填寫時請使用 `http://` 或 `https://` 網址。控制器會略過已過截止日的事項，儲存時一併更新 CSV。

`important.csv` 使用 UTF-8 編碼，欄位如下：

| 欄位 | 說明 | 範例 |
| --- | --- | --- |
| `date` | 截止日，格式為 `yyyy-mm-dd` | `2026-11-01` |
| `item` | 事項名稱 | `疫苗接種意願書填寫` |
| `link` | 相關網頁連結，可留空 | `https://example.com/` |

首頁只顯示截止日為今天或未來的事項，並依截止日排序；有連結時會顯示「開啟連結」。

## 發佈更新

控制器會更新本機 CSV。要將變更發佈到 GitHub Pages，請將更新後的 CSV 提交並推送至 GitHub。
