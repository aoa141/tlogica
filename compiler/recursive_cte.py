#!/usr/bin/python
#
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Native recursive CTE support for dialects that support it.

This module provides functionality to compile recursive predicates to
true SQL recursive CTEs, similar to the LogicaSharp C# implementation.
"""


def GetReferencedPredicates(body):
    """Extract all predicate names referenced in a rule body.

    Args:
        body: The body portion of a rule (conjunction, disjunction, etc.)

    Returns:
        Set of predicate names referenced.
    """
    if body is None:
        return set()

    predicates = set()

    def Walk(node):
        if isinstance(node, dict):
            if 'predicate_name' in node:
                predicates.add(node['predicate_name'])
            for key, value in node.items():
                Walk(value)
        elif isinstance(node, list):
            for item in node:
                Walk(item)

    Walk(body)
    return predicates


def IsRecursivePredicate(predicate_name, rules_of):
    """Check if a predicate is recursive (references itself in body).

    Args:
        predicate_name: Name of the predicate to check.
        rules_of: Dictionary mapping predicate names to their rules.

    Returns:
        True if the predicate is recursive.
    """
    if predicate_name not in rules_of:
        return False

    rules = rules_of[predicate_name]
    for rule in rules:
        if 'body' in rule:
            referenced = GetReferencedPredicates(rule['body'])
            if predicate_name in referenced:
                return True

    return False


def SeparateRecursiveRules(predicate_name, rules):
    """Separate rules into base cases and recursive cases.

    Args:
        predicate_name: Name of the predicate.
        rules: List of rules for this predicate.

    Returns:
        Tuple of (base_case_rules, recursive_case_rules).
    """
    base_cases = []
    recursive_cases = []

    for rule in rules:
        if 'body' in rule:
            referenced = GetReferencedPredicates(rule['body'])
            if predicate_name in referenced:
                recursive_cases.append(rule)
            else:
                base_cases.append(rule)
        else:
            # Rules without bodies are facts (base cases)
            base_cases.append(rule)

    return base_cases, recursive_cases


def GetPredicateColumns(rules):
    """Extract column names from rule heads.

    Args:
        rules: List of rules for a predicate.

    Returns:
        List of column names.
    """
    if not rules:
        return []

    # Use the first rule's head to determine columns
    rule = rules[0]
    head = rule.get('head', {})
    record = head.get('record', {})
    field_values = record.get('field_value', [])

    columns = []
    for i, fv in enumerate(field_values):
        field = fv.get('field')
        if isinstance(field, int):
            columns.append(f'col{field}')
        elif field:
            columns.append(str(field))
        else:
            columns.append(f'col{i}')

    return columns


class RecursiveCteCompiler:
    """Compiler for native recursive CTEs."""

    def __init__(self, program, dialect):
        """Initialize the compiler.

        Args:
            program: The LogicaProgram instance.
            dialect: The SQL dialect to use.
        """
        self.program = program
        self.dialect = dialect

    def CanCompileNatively(self, predicate_name):
        """Check if a predicate can be compiled to native recursive CTE.

        Args:
            predicate_name: Name of the predicate.

        Returns:
            True if native CTE compilation is possible.
        """
        if not self.dialect.SupportsNativeRecursiveCte():
            return False

        rules_of = self.program.annotations.rules_of
        return IsRecursivePredicate(predicate_name, rules_of)

    def CompileRecursiveCte(self, predicate_name, single_rule_sql_func):
        """Compile a recursive predicate to a native CTE.

        Args:
            predicate_name: Name of the recursive predicate.
            single_rule_sql_func: Function to compile a single rule to SQL.

        Returns:
            SQL string with recursive CTE.
        """
        rules_of = self.program.annotations.rules_of
        rules = list(rules_of.get(predicate_name, []))

        if not rules:
            raise ValueError(f"No rules found for predicate: {predicate_name}")

        base_cases, recursive_cases = SeparateRecursiveRules(predicate_name, rules)

        if not base_cases:
            raise ValueError(f"Recursive predicate '{predicate_name}' has no base case")

        # Compile base cases (anchor query)
        anchor_queries = []
        for rule in base_cases:
            sql = single_rule_sql_func(rule)
            if sql and not sql.startswith('/* nil */'):
                anchor_queries.append(sql.strip())

        if not anchor_queries:
            raise ValueError(f"All base cases for '{predicate_name}' are nil")

        anchor_query = '\nUNION ALL\n'.join(anchor_queries)

        # Compile recursive cases
        recursive_queries = []
        for rule in recursive_cases:
            sql = single_rule_sql_func(rule)
            if sql and not sql.startswith('/* nil */'):
                recursive_queries.append(sql.strip())

        if not recursive_queries:
            # No recursive cases means it's not actually recursive
            return f"WITH {predicate_name} AS (\n{anchor_query}\n)\nSELECT * FROM {predicate_name}"

        recursive_query = '\nUNION ALL\n'.join(recursive_queries)

        # Build final SELECT
        columns = GetPredicateColumns(rules)
        if columns:
            select_columns = ', '.join(columns)
            select_query = f"SELECT {select_columns} FROM {predicate_name}"
        else:
            select_query = f"SELECT * FROM {predicate_name}"

        return self.dialect.RecursiveCte(
            predicate_name,
            anchor_query,
            recursive_query,
            select_query
        )
