namespace WebService.Models;

public class LogicaRequest
{
    /// <summary>
    /// The Logica program source code to compile to SQL
    /// </summary>
    public required string Program { get; set; }

    /// <summary>
    /// The predicate name to generate SQL for
    /// </summary>
    public required string Predicate { get; set; }

    /// <summary>
    /// The SQL dialect to compile to. Supported values:
    /// bigquery, sqlite, psql, presto, trino, databricks, duckdb, mssql, clickhouse
    /// Defaults to "mssql" if not specified.
    /// </summary>
    public string? Dialect { get; set; }

    /// <summary>
    /// List of supported SQL dialects
    /// </summary>
    public static readonly string[] SupportedDialects =
    {
        "bigquery", "sqlite", "psql", "presto", "trino",
        "databricks", "duckdb", "mssql", "clickhouse"
    };

    /// <summary>
    /// Default dialect if none specified
    /// </summary>
    public const string DefaultDialect = "mssql";
}
