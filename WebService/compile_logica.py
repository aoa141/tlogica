import sys
import os
import json
import re

# Add the repository root to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Supported SQL dialects
SUPPORTED_DIALECTS = [
    'bigquery', 'sqlite', 'psql', 'presto', 'trino',
    'databricks', 'duckdb', 'mssql', 'clickhouse'
]

def prepare_program_with_dialect(program_text, dialect):
    """Prepare the program text with the specified dialect.

    Removes any existing @Engine annotation and prepends the new one.

    Args:
        program_text: The original Logica program text
        dialect: The SQL dialect to use

    Returns:
        Modified program text with the @Engine annotation
    """
    # Remove existing @Engine annotations (handles various formats)
    # Matches: @Engine("dialect"); or @Engine("dialect", param: value);
    program_text = re.sub(
        r'@Engine\s*\([^)]*\)\s*;?\s*',
        '',
        program_text,
        flags=re.MULTILINE
    )

    # Prepend the new @Engine annotation
    engine_annotation = f'@Engine("{dialect}");\n\n'
    return engine_annotation + program_text.lstrip()


def compile_to_sql(program_text, predicate_name, dialect='mssql'):
    """Compile a Logica program to SQL.

    Args:
        program_text: The Logica program source code
        predicate_name: The predicate to generate SQL for
        dialect: The SQL dialect to compile to (default: mssql)

    Returns:
        Dict with 'success', 'sql' or 'error' keys
    """
    try:
        # Validate dialect
        if dialect not in SUPPORTED_DIALECTS:
            return {
                'success': False,
                'error': f"Unsupported dialect: '{dialect}'. Supported: {', '.join(SUPPORTED_DIALECTS)}"
            }

        from parser_py import parse
        from compiler import universe

        # Prepare program with dialect annotation
        prepared_program = prepare_program_with_dialect(program_text, dialect)

        parsed = parse.ParseFile(prepared_program)
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
    dialect = input_data.get('dialect', 'mssql')
    result = compile_to_sql(
        input_data['program'],
        input_data['predicate'],
        dialect
    )
    print(json.dumps(result))
