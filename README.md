TWSE 三大法人爬蟲 -> MongoDB

簡單的 Python 小工具，抓取台灣證券交易所：
- 三大法人買賣超日報表（T86）
- 三大法人買賣金額統計表（BFI82U）

並將資料整合寫入本機 MongoDB。

使用前提
- 已安裝 Python 3.9+。
- 本機已啟動 MongoDB（預設連線 `mongodb://localhost:27017/`）。

安裝
1) 建議使用虛擬環境
```
python -m venv .venv
. .venv/Scripts/activate
```
2) 安裝套件
```
pip install -r requirements.txt
```
3) 可選：設定 `.env` 覆蓋預設
```
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=twse
```

使用方式
- 單日抓取（兩張表一起）：
```
python -m twse_crawler both --date 2024-10-01
```
- 只抓 T86：
```
python -m twse_crawler t86 --date 2024-10-01
```
- 只抓 BFI82U：
```
python -m twse_crawler bfi82u --date 2024-10-01
```
- 區間回補（含假日自動略過）：
```
python -m twse_crawler both --start 2024-09-01 --end 2024-09-30
```

資料寫入規則
- DB：`twse`（可用 `.env` 中 `MONGODB_DB` 覆蓋）
- 集合：
  - `t86`：每檔股票每日一筆（`date`+`stock_code` 唯一）
  - `bfi82u`：每日一筆（`date` 唯一），內含表格列資料陣列

欄位說明（重點）
- `t86`：保留原表頭中文欄位，並加上：
  - `date`（ISO 日期字串 `YYYY-MM-DD`）
  - `stock_code`（= 原「證券代號」）
  - `stock_name`（= 原「證券名稱」）
- `bfi82u`：
  - `date`（ISO 日期字串）
  - `rows`：以官方 `fields` 對應的列資料陣列（保留字串格式）

注意
- API 假日或無資料會回傳非 OK 狀態，程式會略過並列印訊息。
- 數值欄位以字串（含千分位）保留，避免誤差；如需運算建議轉型後再用。

排程建議
- Windows Task Scheduler 或 `schtasks` 執行：
```
python -m twse_crawler both --date %DATE:~0,4%-%DATE:~5,2%-%DATE:~8,2%
```

