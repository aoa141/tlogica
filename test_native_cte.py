#!/usr/bin/env python
"""Test native recursive CTE compilation for MSSQL."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from compiler.universe import LogicaProgram
from parser_py import parse

# Simple recursive program - ancestry/reachability without @Recursive
program_text = '''
@Engine("mssql");

Parent("Alice", "Bob");
Parent("Bob", "Charlie");
Parent("Charlie", "Diana");

# Recursive predicate - should use native CTE
Ancestor(x, y) :- Parent(x, y);
Ancestor(x, z) :- Parent(x, y), Ancestor(y, z);
'''

print("Testing Native Recursive CTE Compilation")
print("=" * 50)
print("\nProgram:")
print(program_text)
print("\n" + "=" * 50)

try:
    # Parse the program text first
    parsed = parse.ParseFile(program_text)
    program = LogicaProgram(parsed['rule'])
    print("\nProgram parsed successfully.")

    # Check if Ancestor is detected as native recursive
    if hasattr(program, 'native_recursive_predicates'):
        print(f"\nNative recursive predicates: {program.native_recursive_predicates}")

    sql = program.FormattedPredicateSql('Ancestor')
    print("\nGenerated SQL for Ancestor:")
    print("-" * 50)
    print(sql)
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
