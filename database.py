"""
Módulo de base de dados SQLite para gestão de ocorrências.
"""
import sqlite3
import os
from typing import List, Dict, Optional
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "data", "ocorrencias.db")


def get_connection() -> sqlite3.Connection:
    """Obtém conexão à base de dados SQLite."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Inicializa a base de dados com a tabela de ocorrências."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occurrence_id TEXT,
            type TEXT,
            location TEXT,
            severity TEXT,
            status TEXT,
            timestamp TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"Base de dados inicializada em: {DB_PATH}")


def insert_occurrence(occurrence: Dict) -> int:
    """Insere uma nova ocorrência na base de dados."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO ocorrencias (occurrence_id, type, location, severity, status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        occurrence.get("id"),
        occurrence.get("type"),
        occurrence.get("location"),
        occurrence.get("severity"),
        occurrence.get("status"),
        occurrence.get("timestamp")
    ))
    
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_id


def insert_occurrences_batch(occurrences: List[Dict]) -> int:
    """Insere múltiplas ocorrências de uma vez."""
    conn = get_connection()
    cursor = conn.cursor()
    
    data = [
        (
            occ.get("id"),
            occ.get("type"),
            occ.get("location"),
            occ.get("severity"),
            occ.get("status"),
            occ.get("timestamp")
        )
        for occ in occurrences
    ]
    
    cursor.executemany("""
        INSERT INTO ocorrencias (occurrence_id, type, location, severity, status, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, data)
    
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count


def get_all_occurrences() -> List[Dict]:
    """Obtém todas as ocorrências da base de dados."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, occurrence_id, type, location, severity, status, timestamp, created_at
        FROM ocorrencias
        ORDER BY id DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_occurrence_by_id(occ_id: int) -> Optional[Dict]:
    """Obtém uma ocorrência pelo ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, occurrence_id, type, location, severity, status, timestamp, created_at
        FROM ocorrencias
        WHERE id = ?
    """, (occ_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def search_occurrences(query: str) -> List[Dict]:
    """Pesquisa ocorrências por texto."""
    conn = get_connection()
    cursor = conn.cursor()
    
    search_term = f"%{query}%"
    cursor.execute("""
        SELECT id, occurrence_id, type, location, severity, status, timestamp, created_at
        FROM ocorrencias
        WHERE occurrence_id LIKE ? 
           OR type LIKE ? 
           OR location LIKE ?
           OR status LIKE ?
        ORDER BY id DESC
    """, (search_term, search_term, search_term, search_term))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_occurrences_by_status(status: str) -> List[Dict]:
    """Obtém ocorrências por estado."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, occurrence_id, type, location, severity, status, timestamp, created_at
        FROM ocorrencias
        WHERE status LIKE ?
        ORDER BY id DESC
    """, (f"%{status}%",))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_metrics() -> Dict:
    """Obtém métricas/estatísticas das ocorrências."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total
    cursor.execute("SELECT COUNT(*) as total FROM ocorrencias")
    total = cursor.fetchone()["total"]
    
    # Por status
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM ocorrencias 
        GROUP BY status
    """)
    by_status = {row["status"] or "unknown": row["count"] for row in cursor.fetchall()}
    
    # Por severidade
    cursor.execute("""
        SELECT severity, COUNT(*) as count 
        FROM ocorrencias 
        GROUP BY severity
    """)
    by_severity = {row["severity"] or "unknown": row["count"] for row in cursor.fetchall()}
    
    # Por tipo
    cursor.execute("""
        SELECT type, COUNT(*) as count 
        FROM ocorrencias 
        GROUP BY type
        ORDER BY count DESC
        LIMIT 10
    """)
    by_type = {row["type"] or "unknown": row["count"] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "total": total,
        "by_status": by_status,
        "by_severity": by_severity,
        "by_type": by_type
    }


def clear_all_occurrences():
    """Remove todas as ocorrências da base de dados."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ocorrencias")
    conn.commit()
    conn.close()


def delete_occurrence(occ_id: int) -> bool:
    """Remove uma ocorrência pelo ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ocorrencias WHERE id = ?", (occ_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# Inicializar base de dados quando o módulo é importado
init_database()
