import asyncio
import threading
import random
import os
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
import pydicom
import os
import numpy as np
from PIL import Image
import io
from fastapi.middleware.cors import CORSMiddleware
import datetime
import google.generativeai as genai
from pynetdicom import AE, evt, StoragePresentationContexts
from triage_engine import process_dicom_dataset
from dicom_to_gemini import analyze_dicom_to_dict

app = FastAPI()
active_websockets = []
transfer_history = []
fastapi_loop = None

SERVER_START_TIME = time.time()

metrics = {
    "started_at": time.time(),
    "attempts": 0,
    "delivered": 0,
    "failed": 0,
}

def get_metrics_payload():
    attempts = metrics["attempts"]
    delivered = metrics["delivered"]
    failed = metrics["failed"]

    
    uptime_pct = 100.0 
    
    
    deliverability_pct = 100.0 if attempts == 0 else (delivered / attempts) * 100.0

    current_time = time.time()
    elapsed_seconds = current_time - SERVER_START_TIME

    return {
        "type": "METRICS",
        "uptime_pct": round(uptime_pct, 2),
        "deliverability_pct": round(deliverability_pct, 2),
        "uptime_seconds": elapsed_seconds,
        "attempts": attempts,
        "delivered": delivered,
        "failed": failed,
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key="Gemini API Key")

@app.get("/api/ai-analyze/{sop_uid}")
async def analyze_dicom_with_gemini(sop_uid: str, access_id: str = None):
    
    if not access_id or access_id.upper() not in VALID_ACCESS_IDS:
        log_audit("UNAUTHORIZED_AI_ACCESS", access_id or "NONE", f"Attempted AI analysis on: {sop_uid}")
        return Response(status_code=401, content="Unauthorized")

    log_audit("AI_ANALYSIS_REQUESTED", access_id.upper(), f"Study UID: {sop_uid}")

    file_path = f"pacs_storage/{sop_uid}.dcm"
    if not os.path.exists(file_path):
        return Response(status_code=404, content="Study not found")

    try:
        
        ai_result = analyze_dicom_to_dict(file_path)
        
        
        ai_priority_str = "ROUTINE"
        if ai_result.get("priority") == 1:
            ai_priority_str = "URGENT"
        elif ai_result.get("priority") == 2:
            ai_priority_str = "CRITICAL"
            
        return {
            "status": "success", 
            "analysis": ai_result.get("response", "Analysis complete without response."),
            "ai_priority": ai_priority_str
        }
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return Response(status_code=500, content="AI Analysis Failed")

os.makedirs("pacs_storage", exist_ok=True)


async def broadcast_status(message: dict):
    dead = []
    for ws in active_websockets:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in active_websockets:
            active_websockets.remove(ws)

@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)

    for past_study in transfer_history:
        await websocket.send_json(past_study)

    try:
        while True:
            
            payload = get_metrics_payload()
            await websocket.send_json(payload)
            await asyncio.sleep(1) 
            
    except WebSocketDisconnect:
        if websocket in active_websockets:
            active_websockets.remove(websocket)
    except Exception as e:
        print(f"WebSocket disconnected: {e}")
        if websocket in active_websockets:
            active_websockets.remove(websocket)


def handle_store(event):
    """Handles incoming C-STORE requests (Push)"""
    dataset = event.dataset
    dataset.file_meta = event.file_meta

    metrics["attempts"] += 1

    if random.random() < 0.2:
        print("\n[CHAOS] Simulating network failure. Dropping connection!")
        metrics["failed"] += 1
        if fastapi_loop:
            asyncio.run_coroutine_threadsafe(broadcast_status(get_metrics_payload()), fastapi_loop)
        return 0xC000

    
    triage_results = process_dicom_dataset(dataset)

    ws_payload = {
        "time": datetime.datetime.now().strftime("%H:%M:%S"), 
        "study_uid": str(dataset.StudyInstanceUID),
        "patient_id": str(dataset.PatientID),
        "status": "STORE_COMPLETE",
        "urgency_level": triage_results["urgency_level"],
        "flags": triage_results["flags"],
    }
    transfer_history.append(ws_payload)
    metrics["delivered"] += 1

    if fastapi_loop:
        asyncio.run_coroutine_threadsafe(broadcast_status(ws_payload), fastapi_loop)
        asyncio.run_coroutine_threadsafe(broadcast_status(get_metrics_payload()), fastapi_loop)

    
    dataset.save_as(f"pacs_storage/{dataset.StudyInstanceUID}.dcm", write_like_original=False)
    print(f"[SUCCESS] Stored {dataset.StudyInstanceUID}")
    return 0x0000


def start_dicom_server():
    ae = AE(ae_title=b'MINI_PACS')
    ae.supported_contexts = StoragePresentationContexts
    handlers = [(evt.EVT_C_STORE, handle_store)]
    
    print("Starting DICOM SCP on port 11112...")
    ae.start_server(("0.0.0.0", 11112), block=True, evt_handlers=handlers)

@app.on_event("startup")
async def startup_event():
    global fastapi_loop
    fastapi_loop = asyncio.get_running_loop()
    threading.Thread(target=start_dicom_server, daemon=True).start()



VALID_ACCESS_IDS = {
    "R-001": "Dr. Rishi",
    "R-002": "Dr. Raksha",
    "R-003": "Dr Rohana",
    "S-001": "Tech Admin"
}

def log_audit(action: str, access_id: str, details: str = ""):
    """Logs security events to the terminal to prevent FastAPI --reload from crashing."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = VALID_ACCESS_IDS.get(access_id, "UNKNOWN")
    log_entry = f"[{timestamp}] USER: {user} ({access_id}) | ACTION: {action} | DETAILS: {details}"
    
    print(f"🔒 AUDIT: {log_entry}")


@app.post("/api/auth/login")
async def login(payload: dict):
    access_id = payload.get("access_id", "").upper()
    if access_id in VALID_ACCESS_IDS:
        return {"status": "success", "user": VALID_ACCESS_IDS[access_id]}
    else:
        return {"status": "error", "message": "Invalid ID"}


@app.post("/api/auth/logout")
async def logout(payload: dict):
    access_id = payload.get("access_id", "").upper()
    log_audit("LOGOUT", access_id)
    return {"status": "success"}


@app.post("/api/audit")
async def log_custom_action(payload: dict):
    access_id = payload.get("access_id", "").upper()
    action = payload.get("action", "UNKNOWN_ACTION")
    details = payload.get("details", "")
    log_audit(action, access_id, details)
    return {"status": "success"}


@app.get("/api/render/{sop_uid}")
async def render_dicom(sop_uid: str, access_id: str = None):
    
    if not access_id or access_id.upper() not in VALID_ACCESS_IDS:
        return Response(status_code=401, content="Unauthorized")

    log_audit("IMAGE_RENDER", access_id.upper(), f"Study UID: {sop_uid}")
        
    file_path = f"pacs_storage/{sop_uid}.dcm"
    if not os.path.exists(file_path):
        return Response(status_code=404, content="DICOM not found")
        
    try:
        ds = pydicom.dcmread(file_path)
        
        if ds.file_meta.TransferSyntaxUID.is_compressed:
            ds.decompress()
            
        pixels = ds.pixel_array
        normalized = ((pixels - pixels.min()) / (pixels.max() - pixels.min()) * 255.0).astype(np.uint8)
        img = Image.fromarray(normalized)
        
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return Response(content=buf.getvalue(), media_type="image/png")
        
    except Exception as e:
        print(f"Error rendering {sop_uid}: {e}")
        return Response(status_code=500, content=f"Render Error: {str(e)}")


@app.on_event("startup")
async def startup_event():
    print(r"""
                                                  
                    ≠≠≠≠≠≠≠≠≠                     
                   ≠≠≠≠    ≠≠≠≠                   
                  =≠≠=      ≠≠≠                   
                  ==== ×××× =≠=                   
                  ====××××× ===                   
             ÷========×÷×÷÷ ===÷=====             
         =============÷÷÷÷÷ =============         
       ÷===           ÷÷÷÷÷           ÷===        
       ÷÷÷    ÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷÷    ÷÷÷       
       ÷÷÷    ÷÷=÷÷÷÷ ÷÷÷÷÷÷÷=÷÷==÷÷   ÷÷÷÷       
        ÷÷÷÷÷÷÷÷÷÷÷÷÷   ÷==  ÷÷÷÷÷÷÷÷÷÷÷÷÷        
         ×÷÷÷÷÷÷÷÷÷÷÷÷===== ÷÷÷÷÷÷÷÷÷÷÷÷          
                  ×÷÷÷===== ÷÷÷                   
                  ××××===≠= ×××                   
                  ×××× =≠=  ×××                   
                  ××××      ×××                   
                   ×××××  ××××-                   
                     ××××××××    
                           
███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗     
██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║     
███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║     
╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║     
███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
                                                                                                                                                              
    """)
