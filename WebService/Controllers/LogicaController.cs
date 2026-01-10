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
    /// Compiles a Logica program to T-SQL
    /// </summary>
    /// <param name="request">The Logica program and predicate to compile</param>
    /// <returns>The generated T-SQL or an error message</returns>
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

        var response = _compilerService.CompileToSql(request);

        if (!response.Success)
        {
            return BadRequest(response);
        }

        return Ok(response);
    }
}
