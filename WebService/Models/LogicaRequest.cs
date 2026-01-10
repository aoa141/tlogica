namespace WebService.Models;

public class LogicaRequest
{
    /// <summary>
    /// The Logica program source code to compile to T-SQL
    /// </summary>
    public required string Program { get; set; }

    /// <summary>
    /// The predicate name to generate SQL for
    /// </summary>
    public required string Predicate { get; set; }
}
