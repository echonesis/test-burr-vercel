from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
# 移除所有 sys.path 和 os 相關的匯入，因為 Vercel 環境會自動將檔案扁平化。

# --- 匯入 Burr 邏輯 (最終且最穩定的相對匯入) ---
application = None
try:
    # 根據 Vercel 日誌，index.py 和 counter_app.py 最終被視為兄弟文件，
    # 故使用相對匯入是唯一可靠的方式。
    from . import counter_app 
    application = counter_app.application
except ImportError as e:
    # 如果在 Vercel 上執行到這裡，表示環境發生了重大變化。
    print(f"FATAL IMPORT ERROR: Relative module import failed: {e}")
    # 嘗試標準絕對匯入作為本地備用
    try:
        from app import counter_app
        application = counter_app.application
    except ImportError:
        # 如果所有方式都失敗，拋出錯誤。
        raise ImportError(f"Failed to load application function: {e}") 

# 1. 實例化 FastAPI 應用程式
app = FastAPI(title="Burr Counter App")

# 2. 定義 Pydantic 模型來驗證輸入資料
class CounterInput(BaseModel):
    number: int

@app.get("/")
def read_root():
    """根路由，用於健康檢查 (Health Check) - GET /api/index"""
    return {"message": "Burr Counter App is Ready on Vercel!", "status": "running"}

@app.post("/")
def run_burr_counter(input_data: CounterInput):
    """
    接收 JSON body 中的 "number" (計數上限)，運行 Burr 應用程式，並返回最終狀態。
    此路由現在處理 POST /api/index (解決 404 問題)
    """
    count_up_to = input_data.number
    
    if count_up_to <= 0:
        raise HTTPException(status_code=400, detail="Number must be a positive integer.")

    try:
        burr_app = application(count_up_to)
        _, _, final_state = burr_app.run(halt_after=["result"])
        
        return {
            "burr_state": final_state.serialize(),
            "final_counter_value": final_state["counter"],
            "limit": final_state["counter_limit"],
            "message": "Execution successful."
        }

    except Exception as e:
        print(f"Burr execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error during Burr execution: {e}")
        