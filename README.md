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

### Native Recursive CTE Support

tlogica supports **native recursive CTEs** for T-SQL, similar to the C# implementation (logicasharp). When you define a recursive predicate without the `@Recursive` annotation, tlogica automatically compiles it to a true SQL recursive CTE:

```logica
@Engine("mssql");

Parent("Alice", "Bob");
Parent("Bob", "Carol");
Parent("Carol", "David");

# Native recursive CTE - no @Recursive annotation needed
Ancestor(a, d) :- Parent(a, d);
Ancestor(a, d) :- Parent(a, c), Ancestor(c, d);
```

This generates efficient T-SQL with `WITH ... AS (anchor UNION ALL recursive)` syntax:

```sql
WITH t_0_Parent AS (...),
Ancestor AS (
    SELECT ... FROM t_0_Parent AS Parent  -- anchor
    UNION ALL
    SELECT ... FROM t_0_Parent, Ancestor WHERE ...  -- recursive
)
SELECT col0, col1 FROM Ancestor;
```

**When to use each approach:**
- **Native CTE** (no annotation): Best for most recursive queries, lets SQL Server optimize the recursion
- **`@Recursive(Predicate, depth)`**: Use when you need explicit depth control or the native CTE causes issues

### Files Created

1. `compiler/dialect_libraries/mssql_library.py` - T-SQL specific library functions including ArgMin, ArgMax, Array, Fingerprint, etc.
2. `common/mssql_logica.py` - Execution module supporting connection via pyodbc with:
   - Environment variable connection (LOGICA_MSSQL_CONNECTION)
   - Support for both ODBC connection strings and JSON config
   - Windows authentication (Trusted Connection) support
3. `compiler/recursive_cte.py` - Native recursive CTE compilation support with:
   - Automatic detection of recursive predicates
   - Separation of base cases and recursive cases
   - Integration with existing WITH clause system

### Files Modified

1. `compiler/dialects.py` - Added MSSQL dialect class with:
   - 40+ built-in functions mapped to T-SQL equivalents
   - CONCAT() for string concatenation
   - OPENJSON() for array unnesting
   - JSON_VALUE() for record subscripting
   - STRING_AGG() for aggregations
   - Proper type casting (NVARCHAR(MAX), BIGINT, FLOAT)
   - Native recursive CTE support (`SupportsNativeRecursiveCte()`)
   - Registered as 'mssql' in the DIALECTS dictionary
2. `compiler/expr_translate.py` - Added MSSQL to the list of dialects using single-quoted strings
3. `compiler/universe.py` - Added native CTE compilation logic and self-reference handling
4. `logica.py` - Added MSSQL execution handler

### LocalDB Integration Tests

The `integration_tests/mssql_localdb_tests.py` file contains integration tests that run against SQL Server LocalDB on Windows. These tests verify T-SQL compilation and execution for:

- Simple facts and rules
- Named fields
- Filters and joins
- Self-joins
- Recursive predicates (both native CTE and depth-based)
- Aggregation (COUNT, SUM)
- Arithmetic operations
- Negation
- UNION of multiple rules

**Running the tests:**

```bash
# Using the batch file (Windows)
run_localdb_tests.bat

# Or using pytest directly
pip install pyodbc pytest
python -m pytest integration_tests/mssql_localdb_tests.py -v
```

**Requirements:**
- SQL Server LocalDB installed (comes with Visual Studio or SQL Server Express)
- Python pyodbc package
- ODBC Driver 17 or 18 for SQL Server

---

## ClickHouse Support

ClickHouse dialect provides OLAP-optimized SQL generation.

### Key Features

- `groupArray()` for array aggregation
- `arrayJoin()` for array unnesting
- `tuple()` for record types
- ClickHouse-specific type casting
- Backtick identifier quoting

