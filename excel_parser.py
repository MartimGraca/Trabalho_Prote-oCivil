import os
import zipfile
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

# aliases esperados (em minúsculas) para mapear colunas do Excel
COLUMN_ALIASES = {
    "id": ["id", "codigo", "code", "ref", "reference", "occurrence_id", "ocorrência n.º", "ocorrencia n."],
    "type": ["type", "tipo", "descricao", "description", "title", "categoria", "tipo de evento meteorológico", "class. interna", "tipo ocorrência"],
    "location": ["location", "local", "localizacao", "morada", "endereco", "freguesia", "concelho"],
    "severity": ["severity", "severidade", "nivel", "gravidade", "impacto"],
    "status": ["status", "estado", "situacao"],
    "timestamp": ["timestamp", "data", "data_hora", "datetime", "hora", "created_at", "date", "data de alerta"]
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

def _read_excel_with_engine(path: str, ext: str, header: int = 0) -> pd.DataFrame:
    """Read Excel file with appropriate engine based on extension."""
    if ext in ('.xlsx', '.xlsm', '.xltx'):
        if zipfile.is_zipfile(path):
            return pd.read_excel(path, engine='openpyxl', header=header)
        else:
            # File has .xlsx extension but is actually an old .xls format
            return pd.read_excel(path, engine='xlrd', header=header)
    elif ext == '.xls':
        return pd.read_excel(path, engine='xlrd', header=header)
    elif ext == '.xlsb':
        return pd.read_excel(path, engine='pyxlsb', header=header)
    else:
        return pd.read_excel(path, header=header)


def _find_best_header_row(path: str, ext: str, max_rows: int = 10) -> int:
    """Try to find the best header row by looking for known column names."""
    known_columns = ["estado", "local", "data de alerta", "tipo", "ocorrência n", "descrição", "impacto"]
    best_row = 0
    best_matches = 0
    
    for header_row in range(max_rows):
        try:
            df = _read_excel_with_engine(path, ext, header=header_row)
            cols_lower = [str(c).lower() for c in df.columns]
            # Count non-"unnamed" columns and known columns
            named_cols = sum(1 for c in cols_lower if not c.startswith('unnamed'))
            matches = sum(1 for col in cols_lower for kc in known_columns if kc in col)
            total_score = named_cols + matches * 2
            if total_score > best_matches:
                best_matches = total_score
                best_row = header_row
        except Exception:
            continue
    return best_row


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
        # Try to find the best header row
        header_row = _find_best_header_row(path, ext)
        df = _read_excel_with_engine(path, ext, header=header_row)
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