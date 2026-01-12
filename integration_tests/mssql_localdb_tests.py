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

"""Integration tests for T-SQL using LocalDB on Windows.

These tests require SQL Server LocalDB to be installed on Windows.
Run with: python -m pytest integration_tests/mssql_localdb_tests.py -v
"""

import os
import sys
import uuid
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False

from compiler import universe
from parser_py import parse


def skip_if_no_pyodbc(func):
    """Decorator to skip tests if pyodbc is not available."""
    def wrapper(*args, **kwargs):
        if not PYODBC_AVAILABLE:
            raise unittest.SkipTest("pyodbc is not installed")
        return func(*args, **kwargs)
    return wrapper


def get_localdb_connection_string(database="master"):
    """Get the LocalDB connection string with the appropriate driver."""
    if not PYODBC_AVAILABLE:
        return None

    # Find available SQL Server driver
    drivers = pyodbc.drivers()
    sql_drivers = [d for d in drivers if "SQL Server" in d]

    # Prefer ODBC Driver 17 for better LocalDB compatibility, then 18, then generic
    preferred_order = ["ODBC Driver 17 for SQL Server", "ODBC Driver 18 for SQL Server", "SQL Server"]
    driver = None
    for pref in preferred_order:
        if pref in sql_drivers:
            driver = pref
            break

    if not driver and sql_drivers:
        driver = sql_drivers[0]

    if not driver:
        return None

    # Build connection string based on driver version
    conn_str = (
        f"Driver={{{driver}}};"
        f"Server=(localdb)\\MSSQLLocalDB;"
        f"Database={database};"
        f"Trusted_Connection=yes;"
    )

    # Add encryption settings based on driver
    if "18" in driver:
        # ODBC Driver 18 requires explicit encryption settings
        conn_str += "Encrypt=Optional;"
    else:
        # ODBC Driver 17 and earlier
        conn_str += "TrustServerCertificate=yes;"

    return conn_str


def skip_if_no_localdb(func):
    """Decorator to skip tests if LocalDB is not available."""
    def wrapper(*args, **kwargs):
        if not PYODBC_AVAILABLE:
            raise unittest.SkipTest("pyodbc is not installed")
        conn_str = get_localdb_connection_string()
        if not conn_str:
            raise unittest.SkipTest("No SQL Server ODBC driver found")
        try:
            conn = pyodbc.connect(conn_str, timeout=5)
            conn.close()
        except Exception as e:
            raise unittest.SkipTest(f"LocalDB is not available: {e}")
        return func(*args, **kwargs)
    return wrapper


class LocalDbIntegrationTests(unittest.TestCase):
    """Integration tests that compile Logica to T-SQL and execute against LocalDB."""

    @classmethod
    def setUpClass(cls):
        """Create a test database."""
        if not PYODBC_AVAILABLE:
            return

        cls.database_name = f"LogicaTest_{uuid.uuid4().hex}"
        master_conn_str = get_localdb_connection_string("master")

        if not master_conn_str:
            cls.localdb_available = False
            cls.localdb_error = "No SQL Server ODBC driver found"
            return

        try:
            # Connect to master to create test database
            master_conn = pyodbc.connect(master_conn_str)
            master_conn.autocommit = True
            cursor = master_conn.cursor()
            cursor.execute(f"CREATE DATABASE [{cls.database_name}]")
            cursor.close()
            master_conn.close()

            # Connect to test database
            cls.connection_string = get_localdb_connection_string(cls.database_name)
            cls.connection = pyodbc.connect(cls.connection_string)
            cls.connection.autocommit = True
            cls.localdb_available = True
        except Exception as e:
            cls.localdb_available = False
            cls.localdb_error = str(e)

    @classmethod
    def tearDownClass(cls):
        """Drop the test database."""
        if not PYODBC_AVAILABLE or not getattr(cls, 'localdb_available', False):
            return

        try:
            cls.connection.close()

            # Connect to master to drop test database
            master_conn_str = get_localdb_connection_string("master")
            if master_conn_str:
                master_conn = pyodbc.connect(master_conn_str)
                master_conn.autocommit = True
                cursor = master_conn.cursor()
                cursor.execute(f"""
                    ALTER DATABASE [{cls.database_name}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
                    DROP DATABASE [{cls.database_name}];
                """)
                cursor.close()
                master_conn.close()
        except Exception:
            pass

    def setUp(self):
        """Check if LocalDB is available before each test."""
        if not PYODBC_AVAILABLE:
            self.skipTest("pyodbc is not installed")
        if not getattr(self.__class__, 'localdb_available', False):
            self.skipTest(f"LocalDB is not available: {getattr(self.__class__, 'localdb_error', 'Unknown error')}")

    def compile_logica(self, source, predicate_name):
        """Compile Logica source to T-SQL."""
        parsed = parse.ParseFile(source)
        program = universe.LogicaProgram(parsed['rule'])
        sql = program.FormattedPredicateSql(predicate_name)
        return sql

    def execute_sql(self, sql):
        """Execute SQL and return results as list of dictionaries."""
        cursor = self.connection.cursor()
        cursor.execute(sql)

        if cursor.description is None:
            return []

        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({columns[i]: row[i] for i in range(len(columns))})

        return result

    def compile_and_execute(self, source, predicate_name):
        """Compile Logica source and execute against LocalDB."""
        sql = self.compile_logica(source, predicate_name)
        return self.execute_sql(sql)

    # ==================== Simple Facts Tests ====================

    def test_simple_fact_returns_correct_data(self):
        """Test that simple facts compile and return correct row count."""
        source = '''
@Engine("mssql");
Person("Alice", 30);
Person("Bob", 25);
Person("Carol", 35);
'''
        result = self.compile_and_execute(source, "Person")
        self.assertEqual(len(result), 3)

    def test_named_field_facts_returns_correct_data(self):
        """Test that named field facts have correct column names."""
        source = '''
@Engine("mssql");
Employee(name: "Alice", department: "Engineering", salary: 75000);
Employee(name: "Bob", department: "Marketing", salary: 65000);
Employee(name: "Carol", department: "Engineering", salary: 80000);
'''
        result = self.compile_and_execute(source, "Employee")
        self.assertEqual(len(result), 3)

        # Check column names exist
        first_row = result[0]
        self.assertIn("name", first_row)
        self.assertIn("department", first_row)
        self.assertIn("salary", first_row)

    # ==================== Simple Rules Tests ====================

    def test_simple_rule_filters_data(self):
        """Test that rules with conditions filter correctly."""
        source = '''
@Engine("mssql");
Employee(name: "Alice", salary: 75000);
Employee(name: "Bob", salary: 65000);
Employee(name: "Carol", salary: 80000);
Employee(name: "David", salary: 55000);

HighEarner(name:) :- Employee(name:, salary:), salary > 70000;
'''
        result = self.compile_and_execute(source, "HighEarner")
        self.assertEqual(len(result), 2)

        names = [r["name"] for r in result]
        self.assertIn("Alice", names)
        self.assertIn("Carol", names)

    def test_rule_with_string_filter_filters_correctly(self):
        """Test that rules with string equality filter correctly."""
        source = '''
@Engine("mssql");
Employee(name: "Alice", department: "Engineering");
Employee(name: "Bob", department: "Marketing");
Employee(name: "Carol", department: "Engineering");
Employee(name: "David", department: "Sales");

Engineer(name:) :- Employee(name:, department: "Engineering");
'''
        result = self.compile_and_execute(source, "Engineer")
        self.assertEqual(len(result), 2)

        names = [r["name"] for r in result]
        self.assertIn("Alice", names)
        self.assertIn("Carol", names)

    # ==================== Join Tests ====================

    def test_join_rule_combines_data(self):
        """Test that join rules correctly combine data from multiple predicates."""
        source = '''
@Engine("mssql");
Parent(parent: "Alice", child: "Bob");
Parent(parent: "Alice", child: "Carol");
Parent(parent: "Bob", child: "David");
Parent(parent: "Carol", child: "Eve");

Grandparent(grandparent: gp, grandchild: gc) :-
    Parent(parent: gp, child: p),
    Parent(parent: p, child: gc);
'''
        result = self.compile_and_execute(source, "Grandparent")
        self.assertEqual(len(result), 2)

        pairs = [(r["grandparent"], r["grandchild"]) for r in result]
        self.assertIn(("Alice", "David"), pairs)
        self.assertIn(("Alice", "Eve"), pairs)

    def test_self_join_finds_siblings(self):
        """Test that self-join rules work correctly."""
        source = '''
@Engine("mssql");
Parent(parent: "Alice", child: "Bob");
Parent(parent: "Alice", child: "Carol");
Parent(parent: "Alice", child: "David");
Parent(parent: "Eve", child: "Frank");

Sibling(person1: p1, person2: p2) :-
    Parent(parent: parent, child: p1),
    Parent(parent: parent, child: p2),
    p1 != p2;
'''
        result = self.compile_and_execute(source, "Sibling")
        # Alice's 3 children form 6 sibling pairs (3*2 = 6 ordered pairs)
        self.assertEqual(len(result), 6)

    # ==================== Recursive CTE Tests ====================

    def test_recursive_ancestor_finds_all_ancestors(self):
        """Test that recursive predicates find transitive closure."""
        source = '''
@Engine("mssql");
@Recursive(Ancestor, 8);
Parent("Alice", "Bob");
Parent("Bob", "Carol");
Parent("Carol", "David");

Ancestor(a, d) :- Parent(a, d);
Ancestor(a, d) :- Parent(a, c), Ancestor(c, d);
'''
        result = self.compile_and_execute(source, "Ancestor")
        # Direct: Alice->Bob, Bob->Carol, Carol->David (3)
        # Indirect: Alice->Carol, Alice->David, Bob->David (3)
        # Total: 6
        self.assertEqual(len(result), 6)

    def test_recursive_ancestor_queen_victoria_style(self):
        """Test recursive predicate with longer chain (royal lineage)."""
        source = '''
@Engine("mssql");
@Recursive(Ancestor, 16);
Parent("Queen Victoria", "King Edward VII");
Parent("King Edward VII", "King George V");
Parent("King George V", "King George VI");
Parent("King George VI", "Queen Elizabeth II");
Parent("Queen Elizabeth II", "Prince Charles");

Ancestor(a, d) :- Parent(a, d);
Ancestor(a, d) :- Parent(a, c), Ancestor(c, d);
'''
        result = self.compile_and_execute(source, "Ancestor")
        # Direct pairs: 5 (each parent link)
        # 2-step: 4
        # 3-step: 3
        # 4-step: 2
        # 5-step: 1
        # Total: 5+4+3+2+1 = 15
        self.assertEqual(len(result), 15)

        # Verify Queen Victoria is ancestor of Prince Charles
        queen_to_charles = any(
            r["col0"] == "Queen Victoria" and r["col1"] == "Prince Charles"
            for r in result
        )
        self.assertTrue(queen_to_charles)

    def test_native_cte_recursive_ancestor(self):
        """Test native recursive CTE (without @Recursive annotation).

        This test verifies that MSSQL can use true recursive CTEs
        instead of depth-based unfolding when @Recursive is not specified.
        """
        source = '''
@Engine("mssql");
Parent("Alice", "Bob");
Parent("Bob", "Carol");
Parent("Carol", "David");

Ancestor(a, d) :- Parent(a, d);
Ancestor(a, d) :- Parent(a, c), Ancestor(c, d);
'''
        result = self.compile_and_execute(source, "Ancestor")
        # Direct: Alice->Bob, Bob->Carol, Carol->David (3)
        # Indirect: Alice->Carol, Alice->David, Bob->David (3)
        # Total: 6
        self.assertEqual(len(result), 6)

        # Verify it includes transitive closures
        alice_david = any(
            r["col0"] == "Alice" and r["col1"] == "David"
            for r in result
        )
        self.assertTrue(alice_david, "Alice should be ancestor of David via native CTE")

    # ==================== Aggregation Tests ====================

    def test_count_aggregation_counts_correctly(self):
        """Test that count aggregation works correctly."""
        source = '''
@Engine("mssql");
Sale(product: "Widget", amount: 100);
Sale(product: "Widget", amount: 150);
Sale(product: "Gadget", amount: 200);
Sale(product: "Widget", amount: 120);

ProductSaleCount(product:, count? += 1) distinct :- Sale(product:, amount:);
'''
        result = self.compile_and_execute(source, "ProductSaleCount")
        self.assertEqual(len(result), 2)  # Widget and Gadget

        widget_row = next((r for r in result if r["product"] == "Widget"), None)
        gadget_row = next((r for r in result if r["product"] == "Gadget"), None)

        self.assertIsNotNone(widget_row)
        self.assertIsNotNone(gadget_row)
        self.assertEqual(int(widget_row["count"]), 3)
        self.assertEqual(int(gadget_row["count"]), 1)

    def test_sum_aggregation_sums_correctly(self):
        """Test that sum aggregation works correctly."""
        source = '''
@Engine("mssql");
Sale(product: "Widget", amount: 100);
Sale(product: "Widget", amount: 150);
Sale(product: "Gadget", amount: 200);
Sale(product: "Widget", amount: 120);

ProductTotal(product:, total? += amount) distinct :- Sale(product:, amount:);
'''
        result = self.compile_and_execute(source, "ProductTotal")
        self.assertEqual(len(result), 2)

        widget_row = next((r for r in result if r["product"] == "Widget"), None)
        gadget_row = next((r for r in result if r["product"] == "Gadget"), None)

        self.assertIsNotNone(widget_row)
        self.assertIsNotNone(gadget_row)
        self.assertEqual(int(widget_row["total"]), 370)  # 100 + 150 + 120
        self.assertEqual(int(gadget_row["total"]), 200)

    # ==================== Arithmetic and Comparison Tests ====================

    def test_arithmetic_in_rule_calculates_correctly(self):
        """Test that arithmetic expressions in rules work correctly."""
        source = '''
@Engine("mssql");
Rectangle(name: "A", width: 10, height: 5);
Rectangle(name: "B", width: 8, height: 6);
Rectangle(name: "C", width: 4, height: 3);

RectangleArea(name:, area: width * height) :- Rectangle(name:, width:, height:);
'''
        result = self.compile_and_execute(source, "RectangleArea")
        self.assertEqual(len(result), 3)

        area_a = next(r for r in result if r["name"] == "A")["area"]
        area_b = next(r for r in result if r["name"] == "B")["area"]
        area_c = next(r for r in result if r["name"] == "C")["area"]

        self.assertEqual(int(area_a), 50)
        self.assertEqual(int(area_b), 48)
        self.assertEqual(int(area_c), 12)

    def test_multiple_conditions_filter_correctly(self):
        """Test that multiple conditions in a rule work correctly."""
        source = '''
@Engine("mssql");
Employee(name: "Alice", age: 35, salary: 80000);
Employee(name: "Bob", age: 28, salary: 60000);
Employee(name: "Carol", age: 45, salary: 90000);
Employee(name: "David", age: 32, salary: 75000);

SeniorHighEarner(name:) :-
    Employee(name:, age:, salary:),
    age > 30,
    salary > 70000;
'''
        result = self.compile_and_execute(source, "SeniorHighEarner")
        # Alice (35, 80k), Carol (45, 90k), David (32, 75k)
        self.assertEqual(len(result), 3)

        names = [r["name"] for r in result]
        self.assertIn("Alice", names)
        self.assertIn("Carol", names)
        self.assertIn("David", names)
        self.assertNotIn("Bob", names)

    # ==================== Negation Tests ====================

    def test_negation_excludes_matching_rows(self):
        """Test that negation (~) correctly excludes rows."""
        source = '''
@Engine("mssql");
Employee(name: "Alice");
Employee(name: "Bob");
Employee(name: "Carol");
Manager(name: "Alice");

NonManager(name:) :- Employee(name:), ~Manager(name:);
'''
        result = self.compile_and_execute(source, "NonManager")
        self.assertEqual(len(result), 2)

        names = [r["name"] for r in result]
        self.assertIn("Bob", names)
        self.assertIn("Carol", names)
        self.assertNotIn("Alice", names)

    # ==================== Multiple Rules (UNION) Tests ====================

    def test_multiple_rules_union_results(self):
        """Test that multiple rules for same predicate produce UNION."""
        source = '''
@Engine("mssql");
Dog(name: "Buddy");
Dog(name: "Max");
Cat(name: "Whiskers");
Cat(name: "Mittens");

Pet(name:) :- Dog(name:);
Pet(name:) :- Cat(name:);
'''
        result = self.compile_and_execute(source, "Pet")
        self.assertEqual(len(result), 4)

        names = [r["name"] for r in result]
        self.assertIn("Buddy", names)
        self.assertIn("Max", names)
        self.assertIn("Whiskers", names)
        self.assertIn("Mittens", names)


def run_tests():
    """Run all LocalDB integration tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(LocalDbIntegrationTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    # Can be run directly or via pytest
    success = run_tests()
    sys.exit(0 if success else 1)
