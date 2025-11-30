from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os
import json

# --- 關鍵路徑修正區域 ---
# 目的：確保專案根目錄 (包含 app/ 的目錄) 在 sys.path 中。
current_dir = os.path.dirname(os.path.abspath(__file__))
# 計算出專案根目錄 (即 api/ 的上一層，用於找到 app/ 模組)
project_root = os.path.join(current_dir, "..") 

if project_root not in sys.path:
    sys.path.append(project_root)

# --- 匯入 Burr 邏輯 (適應 Vercel 的特殊執行環境) ---

# 設置 application 變數為 None，準備接收匯入的函式
application = None
import_error = None

# 嘗試 1 (標準方法): 絕對匯入。如果 Vercel 嚴格遵守 Python 套件結構，這會成功。
try:
    from app.counter_app import application
except ImportError as e:
    import_error = e
    
    # 嘗試 2 (Serverless 備用方法): 由於執行文件被放在 /var/task/app/，
    # 且 /var/task/ 在 path 中，有時需要直接匯入模組名。
    try:
        # 這會直接尋找 counter_app.py 文件，而不需要 app. 前綴
        import counter_app 
        application = counter_app.application
    except ImportError as e2:
        # 如果所有嘗試都失敗，拋出最開始的絕對匯入錯誤
        print(f"FATAL IMPORT ERROR: Standard path failed ({import_error}). Direct import failed ({e2}).")
        raise import_error 

# 如果 application 仍然是 None，表示匯入邏輯有誤
if application is None:
    raise ImportError("Failed to load application function from counter_app module.")


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
        # 建立 Burr 應用實例 (使用已成功解析的 application 函式)
        burr_app = application(count_up_to)
        
        # 運行 Burr 應用直到達到 "result" 節點
        _, _, final_state = burr_app.run(halt_after=["result"])
        
        # 返回標準的 FastAPI JSON 結構
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
        