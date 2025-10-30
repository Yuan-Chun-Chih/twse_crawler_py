TWSE Crawler 模組說明

本資料夾包含將台灣證券交易所的兩個資料表抓取並寫入 MongoDB 的模組與 CLI 入口。以下說明各檔案的用途與實作重點。

1) __main__.py — CLI 入口
- 功能：提供命令列操作，支援單日與日期區間抓取，並可選擇抓取 T86、BFI82U 或兩者皆抓。
- 主要流程：
  - 解析參數（子指令：t86 / bfi82u / both）。
  - 呼叫 ensure_indexes() 建立唯一索引。
  - 依單日或日期區間呼叫 run_one()：
    - T86：fetch_t86() 取得資料 → upsert_t86() 寫入。
    - BFI82U：fetch_bfi82u() 取得資料 → upsert_bfi82u() 寫入。
  - 日期區間抓取時，於每日間加入 sleep 以避免過於頻繁請求。

2) twse_api.py — TWSE API 客戶端
- 功能：透過 TWSE 的 JSON API 抓取資料。
- 端點：
  - T86（買賣超日報表）：https://www.twse.com.tw/rwd/zh/fund/T86
  - BFI82U（買賣金額統計表）：https://www.twse.com.tw/rwd/zh/fund/BFI82U
- 兩個核心函式：
  - fetch_t86(date):
    - 以參數 `date`（datetime.date）呼叫 T86 API，`response=json`、`selectType=ALL`。
    - 若回應 `stat == "OK"` 且 `data` 有內容：
      - 使用回傳的 `fields` 與每列 `row` 對應成字典。
      - 另外補充標準化欄位：`date`（YYYY-MM-DD）、`stock_code`（= 證券代號）、`stock_name`（= 證券名稱）。
      - 回傳每檔股票一筆的文件陣列。
    - 非交易日/無資料：回傳空陣列。
  - fetch_bfi82u(date):
    - 以 `dayDate=YYYYMMDD`、`type=day` 呼叫 BFI82U。
    - 若回應 `stat == "OK"` 且 `data` 有內容：
      - 以 `fields` 對應每列為物件，組合為 `rows` 陣列，並附上 `date`。
      - 回傳單一文件（該日一筆）。
    - 非交易日/無資料：回傳 None。
- 其他實作：
  - 採用 Session 與基本 User-Agent/Referer/Accept 標頭。
  - 簡單重試（retry 次數與固定短暫 sleep）。
  - 日期轉換工具：YYYYMMDD（API 需求）與 ISO YYYY-MM-DD（儲存統一）。

3) db.py — MongoDB 存取層
- 功能：提供資料庫連線、索引建立、與 upsert 寫入。
- ensure_indexes():
  - `t86` 集合：在 (`date`, `stock_code`) 建立唯一索引，確保每日每檔僅一筆。
  - `bfi82u` 集合：在 `date` 建立唯一索引，確保每日僅一筆。
- upsert_t86(docs):
  - 以 Bulk Write 的 UpdateOne + upsert 寫入。
  - 查找鍵為 (`date`, `stock_code`)，內容以 `$set` 更新。
- upsert_bfi82u(doc):
  - 以 `date` 為唯一鍵 upsert。

4) config.py — 環境設定
- 功能：讀取 `.env` 或系統環境變數。
- 參數：
  - `MONGODB_URI`（預設：`mongodb://localhost:27017/`）
  - `MONGODB_DB`（預設：`twse`）

5) __init__.py — 套件初始化
- 目前無額外邏輯，作為套件結構必要檔案。

資料與欄位約定
- `t86`：
  - 每檔每日一筆；保留官方中文欄位名稱（含千分位字串），並補充：
    - `date`：ISO 日期字串 `YYYY-MM-DD`
    - `stock_code`：= 原「證券代號」
    - `stock_name`：= 原「證券名稱」
- `bfi82u`：
  - 每日一筆；文件結構：`{ date, fields, rows }`，其中 `rows` 內各列以 `fields` 對應成物件。

錯誤處理與重試策略
- 若 HTTP 失敗或 `stat != "OK"`，視為假日或無資料並返回空資料/None。
- 針對短暫性錯誤提供固定次數重試與短暫 sleep，避免過度打擾官方服務。

設計考量
- 可再執行性（Idempotent）：
  - 透過唯一索引搭配 upsert，重複執行不會產生重複資料。
- 延展性：
  - 如需新增表或欄位轉換，可在 twse_api.py 中增加對應 fetch 函式，並在 db.py 增加 upsert 邏輯。
- 數值處理：
  - 目前保留字串（含千分位），適合直接對齊官網輸出；若需運算，建議於查詢端轉型為數字。

開發與實務建議
- 若需記錄執行狀態與錯誤，可加入 logging（INFO/ERROR）。
- 若環境需代理或驗證，請設定 `HTTPS_PROXY` 或調整 requests Session 設定。
- 大量回補時，建議增加每日請求間隔（CLI 的 `--sleep`），降低被限流風險。

