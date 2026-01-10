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
        _pythonPath = pythonPath ?? "python";
        _compilerScript = CreateCompilerScript();
    }

    private static string GetDefaultLogicaPath()
    {
        var assemblyLocation = AppContext.BaseDirectory;

        // Navigate up from bin/Debug/net10.0 to WebService, then up to repository root
        var current = new DirectoryInfo(assemblyLocation);
        while (current != null)
        {
            var logicaPy = Path.Combine(current.FullName, "logica.py");
            if (File.Exists(logicaPy))
            {
                return current.FullName;
            }
            current = current.Parent;
        }

        throw new InvalidOperationException("Could not find logica.py in parent directories");
    }

    private string CreateCompilerScript()
    {
        var scriptPath = Path.Combine(_logicaPath, "WebService", "compile_logica.py");

        if (!File.Exists(scriptPath))
        {
            var script = @"
import sys
import json

def compile_to_sql(program_text, predicate_name):
    try:
        from parser_py import parse
        from compiler import universe

        parsed = parse.ParseFile(program_text)
        rules = parsed.get('rule', [])

        if not rules:
            return {'success': False, 'error': 'No rules found in program'}

        logic_program = universe.LogicaProgram(rules)
        sql = logic_program.FormattedPredicateSql(predicate_name)
        return {'success': True, 'sql': sql}
    except Exception as e:
        import traceback
        return {'success': False, 'error': traceback.format_exc()}

if __name__ == '__main__':
    input_data = json.loads(sys.stdin.read())
    result = compile_to_sql(input_data['program'], input_data['predicate'])
    print(json.dumps(result))
";
            File.WriteAllText(scriptPath, script);
        }

        return scriptPath;
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
