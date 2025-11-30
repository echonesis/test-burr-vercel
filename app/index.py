from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os
import json

# --- 關鍵路徑修正區域 ---
# 目的：解決 Vercel 上常見的 ModuleNotFoundError。
# 將專案根目錄 (api/ 的上一層，即包含 app/ 的目錄) 加入 sys.path。
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..")

if project_root not in sys.path:
    sys.path.append(project_root)

# --- 匯入 Burr 邏輯 ---
try:
    # 直接匯入 app/counter_app.py 裡的 application 函式
    from app.counter_app import application 
except ImportError as e:
    # 如果路徑修正後仍無法匯入，拋出錯誤。
    print(f"FATAL IMPORT ERROR after path fix: {e}")
    raise e 

# 1. 實例化 FastAPI 應用程式
app = FastAPI(title="Burr Counter App")

# 2. 定義 Pydantic 模型來驗證輸入資料
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
        # 建立 Burr 應用實例 (直接使用匯入的 application 函式)
        burr_app = application(count_up_to)
        
        # 運行 Burr 應用直到達到 "result" 節點
        _, _, final_state = burr_app.run(halt_after=["result"])
        
        # 返回標準的 FastAPI JSON 結構 (移除 Lambda 專用的 statusCode)
        return {
            "burr_state": final_state.serialize(),
            "final_counter_value": final_state["counter"],
            "limit": final_state["counter_limit"],
            "message": "Execution successful."
        }

    except Exception as e:
        # 捕獲並記錄 Burr 執行時的錯誤
        print(f"Burr execution failed: {e}")
        # 返回 500 錯誤給客戶端
        raise HTTPException(status_code=500, detail=f"Internal Server Error during Burr execution: {e}")
        