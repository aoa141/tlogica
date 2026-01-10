using Microsoft.AspNetCore.Mvc;
using WebService.Models;
using WebService.Services;

namespace WebService.Controllers;

[ApiController]
[Route("api/[controller]")]
public class LogicaController : ControllerBase
{
    private readonly LogicaCompilerService _compilerService;

    public LogicaController(LogicaCompilerService compilerService)
    {
        _compilerService = compilerService;
    }

    /// <summary>
    /// Compiles a Logica program to SQL for the specified dialect
    /// </summary>
    /// <param name="request">The Logica program, predicate, and optional dialect to compile</param>
    /// <returns>The generated SQL or an error message</returns>
    [HttpPost("compile")]
    [ProducesResponseType<LogicaResponse>(StatusCodes.Status200OK)]
    [ProducesResponseType<LogicaResponse>(StatusCodes.Status400BadRequest)]
    public ActionResult<LogicaResponse> Compile([FromBody] LogicaRequest request)
    {
        if (string.IsNullOrWhiteSpace(request.Program))
        {
            return BadRequest(new LogicaResponse
            {
                Success = false,
                Error = "Program is required"
            });
        }

        if (string.IsNullOrWhiteSpace(request.Predicate))
        {
            return BadRequest(new LogicaResponse
            {
                Success = false,
                Error = "Predicate is required"
            });
        }

        // Validate dialect if provided
        var dialect = request.Dialect?.ToLowerInvariant() ?? LogicaRequest.DefaultDialect;
        if (!LogicaRequest.SupportedDialects.Contains(dialect))
        {
            return BadRequest(new LogicaResponse
            {
                Success = false,
                Error = $"Unsupported dialect: '{request.Dialect}'. Supported dialects are: {string.Join(", ", LogicaRequest.SupportedDialects)}"
            });
        }

        var response = _compilerService.CompileToSql(request, dialect);

        if (!response.Success)
        {
            return BadRequest(response);
        }

        return Ok(response);
    }

    /// <summary>
    /// Returns the list of supported SQL dialects
    /// </summary>
    /// <returns>Array of supported dialect names</returns>
    [HttpGet("dialects")]
    [ProducesResponseType<string[]>(StatusCodes.Status200OK)]
    public ActionResult<string[]> GetSupportedDialects()
    {
        return Ok(LogicaRequest.SupportedDialects);
    }
}
