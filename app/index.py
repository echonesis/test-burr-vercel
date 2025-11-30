from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
import sys

# 為了確保在 Vercel 環境中能正確匯入，我們需要將當前目錄加到 Python 路徑
# 這樣才能找到 app.counter_app
sys.path.append(os.path.dirname(os.path.abspath(__file__))) 

# 從您的核心 Burr 邏輯中匯入必要的函式
# 注意：這裡使用相對路徑，因為 Vercel 的執行環境會從 `api/index.py` 啟動
try:
    from app import counter_app
except ImportError:
    # 這有助於在本地測試時也能運行
    from . import counter_app

# 1. 實例化 FastAPI 應用程式
app = FastAPI(title="Burr Counter App")

# 2. 定義 Pydantic 模型來驗證輸入資料
# 輸入格式將是 JSON body，包含您期望的 "number"
class CounterInput(BaseModel):
    number: int

@app.get("/")
def read_root():
    """根路由，用於健康檢查 (Health Check)"""
    return {"message": "Burr Counter App is Ready on Vercel!", "status": "running"}

@app.post("/run")
def run_burr_counter(input_data: CounterInput):
    """
    接收 JSON body 中的 "number" (計數上限)，運行 Burr 應用程式，並返回最終狀態。
    """
    count_up_to = input_data.number
    
    if count_up_to <= 0:
        raise HTTPException(status_code=400, detail="Number must be a positive integer.")

    try:
        # 建立 Burr 應用實例
        # 這一行對應於您 Lambda 處理器中的：app = counter_app.application(count_up_to)
        burr_app = counter_app.application(count_up_to)
        
        # 運行 Burr 應用直到達到 "result" 節點
        # 這一行對應於您 Lambda 處理器中的：action, result, state = app.run(halt_after=["result"])
        _, _, final_state = burr_app.run(halt_after=["result"])
        
        # 返回最終的狀態數據
        # 狀態物件需要被序列化才能透過 HTTP 返回
        return {
            "statusCode": 200, 
            "body": final_state.serialize(),
            "final_counter_value": final_state["counter"],
            "limit": final_state["counter_limit"]
        }

    except Exception as e:
        # 在實際生產環境中，建議將錯誤日誌記錄到 Vercel Logs 中
        print(f"Burr execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error during Burr execution: {e}")

# Vercel 會自動檢測並使用這個 `app` 變數來運行 Serverless Function。
