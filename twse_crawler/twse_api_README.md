 
 
 使用API 爬蟲
 直接讀取 TWSE 提供的 JSON API

 流程圖如下:
 
      [Start]
         │
         ▼
  建立 Session (_session)
         │
         ▼
  重試 3 次：
     ├─ 發送 GET 到 T86_URL
     ├─ 若失敗 → retry
     ├─ 若成功：
     │    ├─ 檢查 JSON "stat" == "OK"
     │    ├─ 解析欄位 fields + rows
     │    ├─ 每列轉成 dict
     │    ├─ 補上日期與股票代號
     │    └─ 加入 docs
     ▼
  回傳 docs 或 []