import os
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from excel_parser import parse_excel

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DEFAULT_PATH = os.path.join(DATA_DIR, "occurrences.xlsx")

app = FastAPI(title="Proteção Civil API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

def load_data(path: str = DEFAULT_PATH) -> List[dict]:
    if not os.path.exists(path):
        return []
    return parse_excel(path)

@app.get("/health", response_class=JSONResponse)
def health():
    return {"status": "ok"}

@app.get("/occurrences", response_class=JSONResponse)
def get_occurrences():
    try:
        items = load_data()
        return {"count": len(items), "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/occurrences/{occ_id}", response_class=JSONResponse)
def get_occurrence(occ_id: str):
    items = load_data()
    for it in items:
        if it.get("id") == occ_id or (it.get("id") and str(it.get("id")) == str(occ_id)):
            return it
    raise HTTPException(status_code=404, detail="Ocorrência não encontrada")

@app.post("/upload", response_class=JSONResponse)
async def upload_excel(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".xls", ".xlsx")):
        raise HTTPException(status_code=400, detail="Ficheiro não é Excel (.xls/.xlsx)")
    dest = DEFAULT_PATH
    try:
        content = await file.read()
        with open(dest, "wb") as f:
            f.write(content)
        items = parse_excel(dest)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar Excel: {e}")
    return {"message": "Ficheiro carregado com sucesso", "count": len(items)}

@app.get("/metrics", response_class=JSONResponse)
def get_metrics():
    items = load_data()
    metrics = {"total": len(items), "by_severity": {}, "by_status": {}}
    for it in items:
        sev = (it.get("severity") or "unknown").lower()
        st = it.get("status") or "unknown"
        metrics["by_severity"][sev] = metrics["by_severity"].get(sev, 0) + 1
        metrics["by_status"][st] = metrics["by_status"].get(st, 0) + 1
    return metrics

# Serve the frontend HTML at root
@app.get("/", response_class=FileResponse)
def serve_index():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

# Mount static files for CSS and JS
app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")