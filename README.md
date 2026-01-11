# tlogica

Logica fork with extended SQL dialect support including T-SQL (SQL Server) and ClickHouse.

## Supported Dialects

| Dialect | Engine Name | Description |
|---------|-------------|-------------|
| BigQuery | `bigquery` | Google BigQuery (original Logica target) |
| SQLite | `sqlite` | SQLite database |
| PostgreSQL | `psql` | PostgreSQL database |
| Trino | `trino` | Trino distributed SQL |
| Presto | `presto` | Presto distributed SQL |
| Databricks | `databricks` | Databricks SQL |
| DuckDB | `duckdb` | DuckDB analytical database |
| **T-SQL** | `mssql` | Microsoft SQL Server |
| **ClickHouse** | `clickhouse` | ClickHouse OLAP database |

## Usage

Specify the engine in your Logica program:

```logica
@Engine("mssql");  # For SQL Server

Parent(parent: "Alice", child: "Bob");
Parent(parent: "Bob", child: "Carol");

Grandparent(grandparent:, grandchild:) :-
  Parent(parent: grandparent, child: x),
  Parent(parent: x, child: grandchild);
```

### Compile to SQL

```bash
python logica.py program.l print Grandparent
```

### Run with Database

Set the appropriate connection environment variable:
- `LOGICA_MSSQL_CONNECTION` - SQL Server (ODBC format or JSON)
- `LOGICA_CLICKHOUSE_CONNECTION` - ClickHouse connection string

---

## T-SQL (SQL Server) Support

### Files Created

1. `compiler/dialect_libraries/mssql_library.py` - T-SQL specific library functions including ArgMin, ArgMax, Array, Fingerprint, etc.
2. `common/mssql_logica.py` - Execution module supporting connection via pyodbc with:
   - Environment variable connection (LOGICA_MSSQL_CONNECTION)
   - Support for both ODBC connection strings and JSON config
   - Windows authentication (Trusted Connection) support

### Files Modified

1. `compiler/dialects.py` - Added MSSQL dialect class with:
   - 40+ built-in functions mapped to T-SQL equivalents
   - CONCAT() for string concatenation
   - OPENJSON() for array unnesting
   - JSON_VALUE() for record subscripting
   - STRING_AGG() for aggregations
   - Proper type casting (NVARCHAR(MAX), BIGINT, FLOAT)
   - Registered as 'mssql' in the DIALECTS dictionary
2. `compiler/expr_translate.py` - Added MSSQL to the list of dialects using single-quoted strings
3. `logica.py` - Added MSSQL execution handler

---

## ClickHouse Support

ClickHouse dialect provides OLAP-optimized SQL generation.

### Key Features

- `groupArray()` for array aggregation
- `arrayJoin()` for array unnesting
- `tuple()` for record types
- ClickHouse-specific type casting
- Backtick identifier quoting

