using System.Diagnostics;
using System.Text.Json;
using WebService.Models;

namespace WebService.Services;

public class LogicaCompilerService
{
    private readonly string _logicaPath;
    private readonly string _pythonPath;
    private readonly string _compilerScript;

    public LogicaCompilerService(string? logicaPath = null, string? pythonPath = null)
    {
        _logicaPath = logicaPath ?? GetDefaultLogicaPath();
        _pythonPath = pythonPath ?? GetDefaultPythonPath();
        _compilerScript = Path.Combine(_logicaPath, "WebService", "compile_logica.py");
    }

    private static string GetDefaultLogicaPath()
    {
        // Check environment variable first (used in Azure)
        var envPath = Environment.GetEnvironmentVariable("LOGICA_PATH");
        if (!string.IsNullOrEmpty(envPath) && Directory.Exists(envPath))
        {
            return envPath;
        }

        // Navigate up from bin directory to find repository root
        var current = new DirectoryInfo(AppContext.BaseDirectory);
        while (current != null)
        {
            var logicaPy = Path.Combine(current.FullName, "logica.py");
            if (File.Exists(logicaPy))
            {
                return current.FullName;
            }
            current = current.Parent;
        }

        throw new InvalidOperationException("Could not find logica.py. Set LOGICA_PATH environment variable.");
    }

    private static string GetDefaultPythonPath()
    {
        // Check environment variable first (used in Azure)
        var envPath = Environment.GetEnvironmentVariable("PYTHON_PATH");
        if (!string.IsNullOrEmpty(envPath))
        {
            return envPath;
        }

        // On Linux, prefer python3
        if (!OperatingSystem.IsWindows())
        {
            return "python3";
        }

        return "python";
    }

    public LogicaResponse CompileToSql(LogicaRequest request)
    {
        try
        {
            var inputJson = JsonSerializer.Serialize(new
            {
                program = request.Program,
                predicate = request.Predicate
            });

            var psi = new ProcessStartInfo
            {
                FileName = _pythonPath,
                Arguments = $"\"{_compilerScript}\"",
                WorkingDirectory = _logicaPath,
                RedirectStandardInput = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = Process.Start(psi);
            if (process == null)
            {
                return new LogicaResponse
                {
                    Success = false,
                    Error = "Failed to start Python process"
                };
            }

            process.StandardInput.Write(inputJson);
            process.StandardInput.Close();

            var output = process.StandardOutput.ReadToEnd();
            var error = process.StandardError.ReadToEnd();
            process.WaitForExit();

            if (process.ExitCode != 0 || !string.IsNullOrEmpty(error))
            {
                return new LogicaResponse
                {
                    Success = false,
                    Error = string.IsNullOrEmpty(error) ? output : error
                };
            }

            var result = JsonSerializer.Deserialize<JsonElement>(output);

            if (result.TryGetProperty("success", out var success) && success.GetBoolean())
            {
                return new LogicaResponse
                {
                    Success = true,
                    Sql = result.GetProperty("sql").GetString()
                };
            }
            else
            {
                return new LogicaResponse
                {
                    Success = false,
                    Error = result.TryGetProperty("error", out var err) ? err.GetString() : "Unknown error"
                };
            }
        }
        catch (Exception ex)
        {
            return new LogicaResponse
            {
                Success = false,
                Error = ex.Message
            };
        }
    }
}
