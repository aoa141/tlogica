using IronPython.Hosting;
using Microsoft.Scripting.Hosting;
using WebService.Models;

namespace WebService.Services;

public class LogicaCompilerService : IDisposable
{
    private readonly ScriptEngine _engine;
    private readonly ScriptScope _scope;
    private readonly string _logicaPath;
    private bool _initialized;
    private readonly object _lock = new();

    public LogicaCompilerService(string? logicaPath = null)
    {
        _logicaPath = logicaPath ?? GetDefaultLogicaPath();
        _engine = Python.CreateEngine();
        _scope = _engine.CreateScope();
    }

    private static string GetDefaultLogicaPath()
    {
        var assemblyLocation = AppContext.BaseDirectory;
        var webServiceDir = Path.GetDirectoryName(assemblyLocation);

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

    private void EnsureInitialized()
    {
        if (_initialized) return;

        lock (_lock)
        {
            if (_initialized) return;

            var searchPaths = _engine.GetSearchPaths().ToList();
            searchPaths.Add(_logicaPath);
            _engine.SetSearchPaths(searchPaths);

            var initCode = $@"
import sys
sys.path.insert(0, r'{_logicaPath.Replace("\\", "\\\\")}')

from parser_py import parse
from compiler import universe

def compile_to_sql(program_text, predicate_name):
    try:
        parsed = parse.ParseFile(program_text)
        rules = parsed.get('rule', [])

        if not rules:
            return None, 'No rules found in program'

        logic_program = universe.LogicaProgram(rules)
        sql = logic_program.FormattedPredicateSql(predicate_name)
        return sql, None
    except Exception as e:
        return None, str(e)
";
            _engine.Execute(initCode, _scope);
            _initialized = true;
        }
    }

    public LogicaResponse CompileToSql(LogicaRequest request)
    {
        try
        {
            EnsureInitialized();

            lock (_lock)
            {
                _scope.SetVariable("program_text", request.Program);
                _scope.SetVariable("predicate_name", request.Predicate);

                _engine.Execute("result_sql, result_error = compile_to_sql(program_text, predicate_name)", _scope);

                var sql = _scope.GetVariable<string?>("result_sql");
                var error = _scope.GetVariable<string?>("result_error");

                if (error != null)
                {
                    return new LogicaResponse
                    {
                        Success = false,
                        Error = error
                    };
                }

                return new LogicaResponse
                {
                    Success = true,
                    Sql = sql
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

    public void Dispose()
    {
        _engine.Runtime.Shutdown();
        GC.SuppressFinalize(this);
    }
}
