#!/usr/bin/env python3
"""
Aplicação principal para gestão de ocorrências da Proteção Civil.
Permite importar dados de Excel e armazená-los em SQLite.
"""
import os
import sys
from typing import Optional

from excel_parser import parse_excel
from database import (
    init_database,
    insert_occurrences_batch,
    get_all_occurrences,
    get_occurrence_by_id,
    search_occurrences,
    get_occurrences_by_status,
    get_metrics,
    clear_all_occurrences,
    delete_occurrence
)

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
DEFAULT_EXCEL = os.path.join(DATA_DIR, "occurrences.xlsx")


def import_excel(file_path: str, clear_existing: bool = False) -> int:
    """
    Importa dados de um ficheiro Excel para a base de dados SQLite.
    
    Args:
        file_path: Caminho para o ficheiro Excel
        clear_existing: Se True, limpa dados existentes antes de importar
        
    Returns:
        Número de ocorrências importadas
    """
    if not os.path.exists(file_path):
        print(f"Erro: Ficheiro não encontrado: {file_path}")
        return 0
    
    print(f"A ler ficheiro Excel: {file_path}")
    
    try:
        occurrences = parse_excel(file_path)
        print(f"Encontradas {len(occurrences)} ocorrências no Excel")
        
        if clear_existing:
            print("A limpar dados existentes...")
            clear_all_occurrences()
        
        print("A inserir na base de dados...")
        count = insert_occurrences_batch(occurrences)
        print(f"Importadas {count} ocorrências com sucesso!")
        
        return count
        
    except Exception as e:
        print(f"Erro ao importar Excel: {e}")
        return 0


def list_occurrences(limit: int = 20):
    """Lista as ocorrências mais recentes."""
    occurrences = get_all_occurrences()
    
    if not occurrences:
        print("Nenhuma ocorrência encontrada na base de dados.")
        print(f"Use 'python main.py import' para importar do Excel.")
        return
    
    print(f"\n=== Ocorrências ({len(occurrences)} total) ===\n")
    
    for occ in occurrences[:limit]:
        print(f"[{occ['id']}] {occ['occurrence_id'] or 'N/A'}")
        print(f"    Tipo: {occ['type'] or 'N/A'}")
        print(f"    Local: {occ['location'] or 'N/A'}")
        print(f"    Estado: {occ['status'] or 'N/A'}")
        print(f"    Data: {occ['timestamp'] or 'N/A'}")
        print()
    
    if len(occurrences) > limit:
        print(f"... e mais {len(occurrences) - limit} ocorrências")


def show_metrics():
    """Mostra estatísticas das ocorrências."""
    metrics = get_metrics()
    
    print("\n=== Métricas ===\n")
    print(f"Total de ocorrências: {metrics['total']}")
    
    print("\nPor Estado:")
    for status, count in sorted(metrics['by_status'].items(), key=lambda x: -x[1]):
        print(f"  {status}: {count}")
    
    print("\nPor Severidade:")
    for sev, count in sorted(metrics['by_severity'].items(), key=lambda x: -x[1]):
        print(f"  {sev or 'N/A'}: {count}")
    
    print("\nTop 10 Tipos de Ocorrência:")
    for tipo, count in metrics['by_type'].items():
        print(f"  {tipo or 'N/A'}: {count}")


def search(query: str):
    """Pesquisa ocorrências."""
    results = search_occurrences(query)
    
    if not results:
        print(f"Nenhuma ocorrência encontrada para: '{query}'")
        return
    
    print(f"\n=== Resultados para '{query}' ({len(results)} encontradas) ===\n")
    
    for occ in results[:20]:
        print(f"[{occ['id']}] {occ['occurrence_id'] or 'N/A'} - {occ['type'] or 'N/A'}")
        print(f"    Local: {occ['location'] or 'N/A'} | Estado: {occ['status'] or 'N/A'}")
        print()


def show_help():
    """Mostra ajuda de utilização."""
    print("""
=== Gestão de Ocorrências - Proteção Civil ===

Uso: python main.py [comando] [argumentos]

Comandos:
  import [ficheiro]     Importa ocorrências de um ficheiro Excel
                        (default: data/occurrences.xlsx)
  
  import-clean [fich]   Importa, limpando dados existentes primeiro
  
  list [limite]         Lista ocorrências (default: 20)
  
  metrics               Mostra estatísticas das ocorrências
  
  search <texto>        Pesquisa ocorrências por texto
  
  clear                 Remove todas as ocorrências (pede confirmação)
  
  help                  Mostra esta ajuda

Exemplos:
  python main.py import                    # Importa do ficheiro default
  python main.py import dados.xlsx         # Importa de um ficheiro específico
  python main.py import-clean dados.xlsx   # Limpa e importa
  python main.py list 50                   # Lista 50 ocorrências
  python main.py search "inundação"        # Pesquisa por inundação
  python main.py metrics                   # Mostra estatísticas
""")


def main():
    """Função principal."""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "import":
        file_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_EXCEL
        import_excel(file_path, clear_existing=False)
    
    elif command == "import-clean":
        file_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_EXCEL
        import_excel(file_path, clear_existing=True)
    
    elif command == "list":
        try:
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        except ValueError:
            print("Erro: O limite deve ser um número inteiro")
            return
        list_occurrences(limit)
    
    elif command == "metrics":
        show_metrics()
    
    elif command == "search":
        if len(sys.argv) < 3:
            print("Erro: Especifique o texto a pesquisar")
            print("Uso: python main.py search <texto>")
            return
        query = " ".join(sys.argv[2:])
        search(query)
    
    elif command == "clear":
        confirm = input("Tem a certeza que quer remover TODAS as ocorrências? (s/N): ")
        if confirm.lower() == 's':
            clear_all_occurrences()
            print("Todas as ocorrências foram removidas.")
        else:
            print("Operação cancelada.")
    
    elif command == "help":
        show_help()
    
    else:
        print(f"Comando desconhecido: {command}")
        show_help()


if __name__ == "__main__":
    main()
