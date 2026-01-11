# tlogica
Logica fork that supports T-SQL

  Files Created

  1. compiler/dialect_libraries/mssql_library.py - T-SQL specific library functions including ArgMin, ArgMax, Array, Fingerprint, etc.
  2. common/mssql_logica.py - Execution module supporting connection via pyodbc with:
    - Environment variable connection (LOGICA_MSSQL_CONNECTION)
    - Support for both ODBC connection strings and JSON config
    - Windows authentication (Trusted Connection) support

  Files Modified

  1. compiler/dialects.py - Added MSSQL dialect class with:
    - 40+ built-in functions mapped to T-SQL equivalents
    - CONCAT() for string concatenation
    - OPENJSON() for array unnesting
    - JSON_VALUE() for record subscripting
    - STRING_AGG() for aggregations
    - Proper type casting (NVARCHAR(MAX), BIGINT, FLOAT)
    - Registered as 'mssql' in the DIALECTS dictionary
  2. compiler/expr_translate.py - Added MSSQL to the list of dialects using single-quoted strings
  3. logica.py - Added MSSQL execution handler

  Usage

  @Engine("mssql");

  Parent(parent: "Alice", child: "Bob");
  Parent(parent: "Bob", child: "Carol");

  Grandparent(grandparent:, grandchild:) :-
    Parent(parent: grandparent, child: x),
    Parent(parent: x, child: grandchild);

  To compile: python logica.py program.l print Grandparent

  To run with a database, set LOGICA_MSSQL_CONNECTION to your connection string (ODBC format or JSON).
