namespace WebService.Models;

public class LogicaResponse
{
    /// <summary>
    /// The generated T-SQL query
    /// </summary>
    public string? Sql { get; set; }

    /// <summary>
    /// Error message if compilation failed
    /// </summary>
    public string? Error { get; set; }

    /// <summary>
    /// Whether the compilation was successful
    /// </summary>
    public bool Success { get; set; }
}
