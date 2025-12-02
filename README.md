# Gestão de Ocorrências - Proteção Civil

Sistema de gestão de ocorrências para a Proteção Civil usando Python com SQLite.

## Requisitos

- Python 3.8+
- Bibliotecas listadas em `requirements.txt`

## Instalação

```bash
pip install -r requirements.txt
```

## Utilização

### Importar dados do Excel

```bash
# Importar do ficheiro padrão (data/occurrences.xlsx)
python main.py import

# Importar de um ficheiro específico
python main.py import meu_ficheiro.xlsx

# Limpar dados existentes e importar
python main.py import-clean
```

### Listar ocorrências

```bash
# Listar as 20 mais recentes
python main.py list

# Listar as 50 mais recentes
python main.py list 50
```

### Ver estatísticas

```bash
python main.py metrics
```

### Pesquisar ocorrências

```bash
python main.py search "cheias"
python main.py search "Arruda"
```

### Limpar base de dados

```bash
python main.py clear
```

## Estrutura do Projeto

```
├── main.py           # Aplicação principal (CLI)
├── database.py       # Módulo de base de dados SQLite
├── excel_parser.py   # Parser de ficheiros Excel
├── requirements.txt  # Dependências Python
└── data/
    ├── occurrences.xlsx  # Ficheiro Excel de exemplo
    └── ocorrencias.db    # Base de dados SQLite (gerada automaticamente)
```

## Base de Dados

A base de dados SQLite é criada automaticamente em `data/ocorrencias.db` e contém a tabela `ocorrencias` com os seguintes campos:

- `id` - ID interno (auto-incremento)
- `occurrence_id` - ID da ocorrência do Excel
- `type` - Tipo de ocorrência
- `location` - Local
- `severity` - Severidade
- `status` - Estado (Fechado, Aberto, etc.)
- `timestamp` - Data/hora
- `created_at` - Data de importação