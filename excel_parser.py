import zipfile
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

# aliases esperados (em minúsculas) para mapear colunas do Excel
COLUMN_ALIASES = {
    "id": ["id", "codigo", "code", "ref", "reference", "occurrence_id"],
    "type": ["type", "tipo", "descricao", "description", "title", "categoria"],
    "location": ["location", "local", "localizacao", "morada", "endereco"],
    "severity": ["severity", "severidade", "nivel", "gravidade"],
    "status": ["status", "estado", "situacao"],
    "timestamp": ["timestamp", "data", "data_hora", "datetime", "hora", "created_at", "date"]
}

# normaliza valores de severidade para um conjunto conhecido
SEVERITY_MAP = {
    "critico": "critical", "crítico": "critical", "critical": "critical",
    "alta": "high", "high": "high",
    "medio": "medium", "médio": "medium", "medium": "medium",
    "baixa": "low", "baixo": "low", "low": "low"
}

def _find_column(columns: List[str], aliases: List[str]) -> Optional[str]:
    cols_lower = [c.lower() for c in columns]
    for a in aliases:
        if a.lower() in cols_lower:
            return columns[cols_lower.index(a.lower())]
    return None

def _normalize_severity(value) -> Optional[str]:
    if value is None:
        return None
    try:
        import pandas as _pd
        if isinstance(value, float) and _pd.isna(value):
            return None
    except Exception:
        pass
    s = str(value).strip().lower()
    return SEVERITY_MAP.get(s, s)  # devolve mapeado ou string lowercase

def _parse_timestamp(val) -> Optional[str]:
    if val is None:
        return None
    try:
        # pandas lida com muitos formatos e com Excel datetimes
        ts = pd.to_datetime(val)
        return ts.isoformat()
    except Exception:
        try:
            return datetime.fromisoformat(str(val)).isoformat()
        except Exception:
            return str(val)

def parse_excel(path: str) -> List[Dict]:
    """
    Lê um ficheiro Excel e devolve lista de ocorrências normalizadas:
    { id, type, location, severity, status, timestamp }
    """
    # quick checks
    if not os.path.exists(path):
        raise FileNotFoundError(f"Ficheiro não existe: {path}")
    size = os.path.getsize(path)
    if size == 0:
        raise ValueError("Ficheiro vazio (upload falhou?)")
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext in ('.xlsx', '.xlsm', '.xltx'):
            if not zipfile.is_zipfile(path):
                raise ValueError("Ficheiro .xlsx inválido / não é um zip válido")
            df = pd.read_excel(path, engine='openpyxl')
        elif ext == '.xls':
            # xlrd 1.2.0 required for .xls support
            df = pd.read_excel(path, engine='xlrd')
        elif ext == '.xlsb':
            # pyxlsb required
            df = pd.read_excel(path, engine='pyxlsb')
        else:
            # fallback: tentar pandas autodetect
            df = pd.read_excel(path)
    except Exception as e:
        raise ValueError(f"Erro ao ler Excel ({ext}): {e}")

    cols = list(df.columns)

    mapping = { key: _find_column(cols, aliases) for key, aliases in COLUMN_ALIASES.items() }

    items: List[Dict] = []
    for _, row in df.iterrows():
        def get(colkey):
            col = mapping.get(colkey)
            if col is None:
                return None
            v = row.get(col)
            # tratar NaNs
            if isinstance(v, float) and pd.isna(v):
                return None
            return v

        ts = _parse_timestamp(get("timestamp"))
        item = {
            "id": str(get("id")) if get("id") is not None else None,
            "type": str(get("type")) if get("type") is not None else None,
            "location": str(get("location")) if get("location") is not None else None,
            "severity": _normalize_severity(get("severity")),
            "status": str(get("status")) if get("status") is not None else None,
            "timestamp": ts
        }
        items.append(item)
    return items