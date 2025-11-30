# Vercel Deployment for Burr

## Guidelines
1. 結構確認: 確保您的專案結構如下：
```
/your-vercel-project 
├── app/ 
│ ├── init.py 
│ └── counter_app.py # 您的 Burr 邏輯 
├── api/ 
│ └── index.py # 新的 Vercel 入口 (FastAPI) 
├── requirements.txt # 包含 fastapi, pydantic, apache-burr 
└── ...
```

2. Git 推送: 將所有更改推送到您的 Git 儲存庫。

3. Vercel 部署: 連接您的 Git 儲存庫到 Vercel。Vercel 會自動偵測 api/ 資料夾並部署 index.py 作為 Serverless Function，路徑為 /api/run。

4. 測試 API: 部署完成後，您可以對 Vercel 提供的 URL 發送一個 POST 請求到 /api/run，並在請求體 (JSON body) 中傳入：
```json
{
    "number": 5
}
```