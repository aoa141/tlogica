import sys
import os
import json

# Add the repository root to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

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
