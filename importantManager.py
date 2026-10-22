import csv
import os
import sys
from datetime import date
from urllib.parse import urlparse


csvPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "important.csv")
fieldNames = ["date", "item", "link"]


def parseDateInput(text, today):
    text = text.strip()
    parts = text.split("/")
    if len(parts) == 3:
        y, m, d = parts
        y = int(y)
    elif len(parts) == 2:
        m, d = parts
        y = today.year
    elif len(parts) == 1:
        d = parts[0]
        m = today.month
        y = today.year
    else:
        raise ValueError(f"無法解析日期：{text}")
    return date(y, int(m), int(d))


def normalizeRow(row):
    return {
        "date": (row.get("date") or "").strip(),
        "item": (row.get("item") or row.get("range") or "").strip(),
        "link": (row.get("link") or "").strip(),
    }


def loadRows():
    if not os.path.exists(csvPath):
        return []
    with open(csvPath, newline="", encoding="utf-8-sig") as f:
        return [normalizeRow(row) for row in csv.DictReader(f)]


def saveRows(rows):
    rows.sort(key=lambda row: row["date"])
    with open(csvPath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldNames)
        writer.writeheader()
        writer.writerows(rows)


def dropPastRows(rows, today):
    todayStr = today.isoformat()
    kept = [row for row in rows if row["date"] >= todayStr]
    return kept, len(rows) - len(kept)


def printRows(rows):
    if not rows:
        print("目前沒有任何近期事項")
        return
    for i, row in enumerate(rows, start=1):
        print(f"{i}. {row['date']}  {row['item']}  {row['link']}")


def readLink(prompt, current=""):
    link = input(prompt).strip()
    if not link:
        return current
    parsed = urlparse(link)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("連結請使用 http:// 或 https:// 開頭的網址")
    return link


def addRow(rows, today):
    dateText = input("截止日 (yyyy/mm/dd、mm/dd 或 dd)：")
    try:
        parsedDate = parseDateInput(dateText, today)
    except ValueError as error:
        print(f"日期格式錯誤：{error}")
        return

    item = input("事項：").strip()
    if not item:
        print("事項不可空白")
        return
    try:
        link = readLink("連結（可留空）：")
    except ValueError as error:
        print(f"連結格式錯誤：{error}")
        return

    rows.append({"date": parsedDate.isoformat(), "item": item, "link": link})
    print("已新增")


def selectRow(rows, prompt):
    printRows(rows)
    if not rows:
        return None
    indexText = input(prompt).strip()
    if not indexText.isdigit() or not (1 <= int(indexText) <= len(rows)):
        print("編號錯誤")
        return None
    return int(indexText) - 1


def editRow(rows, today):
    index = selectRow(rows, "要修改第幾筆？（輸入編號）：")
    if index is None:
        return
    target = rows[index]

    dateText = input(f"截止日 [{target['date']}]（直接按 Enter 保留）：").strip()
    if dateText:
        try:
            target["date"] = parseDateInput(dateText, today).isoformat()
        except ValueError as error:
            print(f"日期格式錯誤：{error}")
            return

    itemText = input(f"事項 [{target['item']}]（直接按 Enter 保留）：").strip()
    if itemText:
        target["item"] = itemText

    linkText = input(f"連結 [{target['link']}]（直接按 Enter 保留，輸入 - 清空）：").strip()
    if linkText == "-":
        target["link"] = ""
    elif linkText:
        try:
            parsed = urlparse(linkText)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValueError("連結請使用 http:// 或 https:// 開頭的網址")
            target["link"] = linkText
        except ValueError as error:
            print(f"連結格式錯誤：{error}")
            return
    print("已更新")


def deleteRow(rows):
    index = selectRow(rows, "要刪除第幾筆？（輸入編號）：")
    if index is None:
        return
    removed = rows.pop(index)
    print(f"已刪除：{removed['date']} {removed['item']}")


def main():
    today = date.today()
    rows = loadRows()
    rows, removedCount = dropPastRows(rows, today)
    if removedCount:
        print(f"已自動移除 {removedCount} 筆過期事項")

    menu = """
1. 列出所有事項
2. 新增事項
3. 修改事項
4. 刪除事項
5. 儲存並離開
6. 不儲存離開
"""
    while True:
        print(menu)
        choice = input("請選擇：").strip()
        if choice == "1":
            printRows(rows)
        elif choice == "2":
            addRow(rows, today)
        elif choice == "3":
            editRow(rows, today)
        elif choice == "4":
            deleteRow(rows)
        elif choice == "5":
            saveRows(rows)
            print(f"已儲存至 {csvPath}")
            sys.exit(0)
        elif choice == "6":
            sys.exit(0)
        else:
            print("無效選項")


if __name__ == "__main__":
    main()
