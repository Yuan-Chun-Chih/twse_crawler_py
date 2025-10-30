1.

🚀 環境設定步驟
1️⃣ 安裝 MongoDB Community Server

前往 MongoDB 官方下載頁面

選擇 Windows MSI Installer

安裝時勾選：

✅ Install MongoDB as a Service

✅ Run service as Network Service user

安裝完成後啟動服務：

Start-Service MongoDB


驗證是否啟動：

mongosh
show dbs

2️⃣ 建立 Python 虛擬環境

在專案根目錄（例如 C:\Users\kdsam\twse_crawler_py）執行：

python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1


安裝必要模組：

pip install -r requirements.txt

3️⃣ （可選）設定 .env 檔案

在專案根目錄新增 .env：

MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=twse

4️⃣ 啟動爬蟲
抓取單日資料
python -m twse_crawler both --date 2024-10-01

抓取日期區間
python -m twse_crawler both --start 2024-09-01 --end 2024-09-30

只抓其中一類
python -m twse_crawler t86 --date 2024-10-01
python -m twse_crawler bfi82u --date 2024-10-01

🧰 SSL 憑證問題修正（Python 3.14 特別說明）

由於 Python 3.14 的 OpenSSL 驗證有 Bug，會出現：

SSLCertVerificationError: Missing Subject Key Identifier (_ssl.c:1077)


為此，twse_api.py 內已加入自動修正機制：

import certifi, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
r = s.get(T86_URL, params=params, verify=certifi.where())
# 若失敗會自動 fallback：
# ⚠️ SSL 憑證驗證失敗，改用非驗證連線（verify=False）


✅ 可正常運作於 Python 3.14
💡 若你想要更安全的驗證，建議改用 Python 3.12。

📊 驗證資料是否成功寫入 MongoDB

開啟 MongoDB Shell (mongosh)，逐行輸入：

mongosh
use twse
show collections
db.t86.countDocuments({ date: "2024-10-01" })
db.bfi82u.findOne({ date: "2024-10-01" })


範例輸出：

twse> db.bfi82u.findOne({ date: "2024-10-01" })
{
  _id: ObjectId('68fbb5fc7d04da57621f954b'),
  date: '2024-10-01',
  fields: ['單位名稱', '買進金額', '賣出金額', '買賣差額'],
  rows: [
    { '單位名稱': '自營商 (自行買賣)', '買進金額': '3,572,802,012', '賣出金額': '4,390,740,655', '買賣差額': '-817,938,643' },
    { '單位名稱': '投信', '買進金額': '6,057,743,445', '賣出金額': '4,231,091,896', '買賣差額': '1,826,651,549' }
  ]
}

🗓️ 自動化排程（選用）

建立批次檔 update_daily.bat：

@echo off
cd /d C:\Users\kdsam\twse_crawler_py
call .\.venv\Scripts\activate
python -m twse_crawler both --date %date:~0,4%-%date:~5,2%-%date:~8,2%


然後用 Windows 工作排程器 設定每日早上 09:00 執行。

🧠 Troubleshooting
問題	原因	解法
mongosh 顯示 Missing semicolon	指令一次貼太多行	請逐行輸入
SSLCertVerificationError	Python 3.14 憑證鏈錯誤	已自動降級為 verify=False
pip 無法辨識	尚未啟動虛擬環境	執行 .\.venv\Scripts\Activate.ps1
MongoDB 無法啟動	服務未執行	Start-Service MongoDB
🧾 成果摘要
模組	狀態
MongoDB 本地連線	✅ 正常
TWSE API 抓取	✅ 成功
SSL 憑證處理	⚠️ 自動 fallback
寫入資料庫	✅ 正常
驗證查詢結果	✅ 成功顯示

2.

🚀 實作方向 A：每日自動抓取並發佈
🧩 系統架構概念
每日 09:00
    ↓
Windows 排程器 (Task Scheduler)
    ↓
啟動虛擬環境 + 執行 Python
    ↓
1. 抓取 TWSE 當日資料
2. 產出圖表/報表 (可用 matplotlib / pandas)
3. 自動上傳或寄送報表
   - LINE Notify / Telegram bot / Email / GitHub Pages

⚙️ 第一步：每日自動抓取
建立一個批次檔 auto_update.bat
@echo off
cd /d C:\Users\kdsam\twse_crawler_py
call .\.venv\Scripts\activate
python -m twse_crawler both --date %date:~0,4%-%date:~5,2%-%date:~8,2%

設定排程

1️⃣ 打開 Windows 搜尋「工作排程器 (Task Scheduler)」
2️⃣ 選「建立基本工作」
3️⃣ 名稱：TWSE Daily Update
4️⃣ 觸發條件：每天 09:00
5️⃣ 動作 → 執行程式

程式/指令：cmd.exe
參數：/c "C:\Users\kdsam\twse_crawler_py\auto_update.bat"


6️⃣ 儲存後即可自動每天執行。

🧠 第二步：自動產生圖表或摘要報告（選配）

可用 pandas + matplotlib 做每日法人買賣金額圖：

import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["twse"]

doc = db["bfi82u"].find_one({"date": "2024-10-01"})
df = pd.DataFrame(doc["rows"])
df["買賣差額"] = df["買賣差額"].astype(str).str.replace(",", "").astype(float)

plt.bar(df["單位名稱"], df["買賣差額"])
plt.title(f"三大法人買賣金額差額 - {doc['date']}")
plt.ylabel("買賣差額 (NTD)")
plt.savefig("daily_report.png", dpi=200, bbox_inches="tight")
