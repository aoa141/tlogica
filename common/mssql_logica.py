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

"""Microsoft SQL Server (T-SQL) execution support for Logica."""

import getpass
import json
import os
from decimal import Decimal

if '.' not in __package__:
  from type_inference.research import infer
else:
  from ..type_inference.research import infer


def MSSQLExecute(sql, connection):
  """Execute SQL against a Microsoft SQL Server connection.

  Args:
    sql: The SQL statement to execute.
    connection: A pyodbc connection object.

  Returns:
    A cursor with the query results.
  """
  import pyodbc
  cursor = connection.cursor()
  try:
    cursor.execute(sql)
  except pyodbc.ProgrammingError as e:
    if 'Invalid object name' in str(e):
      raise infer.TypeErrorCaughtException(
        infer.ContextualizedError.BuildNiceMessage(
          'Running SQL.', 'Undefined table used: ' + str(e)))
    connection.rollback()
    raise e
  except pyodbc.Error as e:
    connection.rollback()
    raise e
  return cursor


def DigestMSSQLType(x):
  """Convert MSSQL types to Python native types."""
  if isinstance(x, Decimal):
    if x.as_integer_ratio()[1] == 1:
      return int(x)
    else:
      return float(x)
  if isinstance(x, str):
    # Try to parse JSON if it looks like JSON
    if x.startswith('[') or x.startswith('{'):
      try:
        return json.loads(x)
      except json.JSONDecodeError:
        pass
  return x


def MSSQLTypeAsDictionary(row, description):
  """Convert a pyodbc row to a dictionary."""
  result = {}
  for i, col in enumerate(description):
    col_name = col[0]
    result[col_name] = DigestMSSQLType(row[i])
  return result


def MSSQLTypeAsList(rows, description):
  """Convert pyodbc rows to a list of dictionaries."""
  return [MSSQLTypeAsDictionary(row, description) for row in rows]


REMEMBERED_CONNECTION_STR = None


def ConnectToMSSQL(mode):
  """Connect to Microsoft SQL Server.

  Args:
    mode: Either 'interactive' (prompt for credentials) or 'environment'
          (use LOGICA_MSSQL_CONNECTION environment variable).

  Returns:
    A pyodbc connection object.

  The connection string can be in one of these formats:
  - ODBC connection string: "DRIVER={ODBC Driver 17 for SQL Server};SERVER=...;DATABASE=...;UID=...;PWD=..."
  - JSON config: {"server": "...", "database": "...", "user": "...", "password": "...", "driver": "..."}
  """
  import pyodbc
  global REMEMBERED_CONNECTION_STR

  if mode == 'interactive':
    if REMEMBERED_CONNECTION_STR:
      connection_str = REMEMBERED_CONNECTION_STR
    else:
      print('Please enter SQL Server connection string (ODBC format) or JSON config.')
      print('ODBC format: DRIVER={ODBC Driver 17 for SQL Server};SERVER=server;DATABASE=db;UID=user;PWD=pass')
      print('JSON format: {"server": "...", "database": "...", "user": "...", "password": "...", "driver": "ODBC Driver 17 for SQL Server"}')
      connection_str = getpass.getpass()
      REMEMBERED_CONNECTION_STR = connection_str
  elif mode == 'environment':
    connection_str = os.environ.get('LOGICA_MSSQL_CONNECTION')
    assert connection_str, (
        'Please provide MSSQL connection parameters '
        'in LOGICA_MSSQL_CONNECTION environment variable.')
  else:
    assert False, 'Unknown mode: ' + mode

  if connection_str.startswith('{') and connection_str.endswith('}'):
    # JSON format
    config = json.loads(connection_str)
    driver = config.get('driver', 'ODBC Driver 17 for SQL Server')
    server = config['server']
    database = config.get('database', '')
    user = config.get('user', '')
    password = config.get('password', '')

    if user and password:
      # SQL Server authentication
      conn_str = f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={user};PWD={password}'
    else:
      # Windows authentication (Trusted Connection)
      conn_str = f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes'

    connection = pyodbc.connect(conn_str)
  else:
    # Assume ODBC connection string format
    connection = pyodbc.connect(connection_str)

  connection.autocommit = True
  return connection


def FetchResults(cursor):
  """Fetch all results from a cursor and convert to Python types."""
  if cursor.description is None:
    return []

  rows = cursor.fetchall()
  return MSSQLTypeAsList(rows, cursor.description)
