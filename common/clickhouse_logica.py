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

"""ClickHouse execution support for Logica."""

import getpass
import json
import os
from decimal import Decimal

if '.' not in __package__:
  from type_inference.research import infer
else:
  from ..type_inference.research import infer


def ClickHouseExecute(sql, connection):
  """Execute SQL against a ClickHouse connection.

  Args:
    sql: SQL query string to execute
    connection: clickhouse_driver.Client connection

  Returns:
    ClickHouseCursor object with results
  """
  try:
    result = connection.execute(sql, with_column_types=True)
    return ClickHouseCursor(result)
  except Exception as e:
    error_str = str(e)
    if 'Unknown table' in error_str or "doesn't exist" in error_str:
      raise infer.TypeErrorCaughtException(
          infer.ContextualizedError.BuildNiceMessage(
              'Running SQL.', 'Undefined table used: ' + error_str))
    raise e


class ClickHouseCursor:
  """Cursor-like wrapper for ClickHouse results.

  Provides a cursor interface compatible with Logica's result processing.
  """

  def __init__(self, result):
    """Initialize cursor with ClickHouse result.

    Args:
      result: Tuple of (data, columns) from clickhouse_driver execute()
    """
    if result:
      self._data, self._columns = result
    else:
      self._data, self._columns = [], []
    # Build description in DB-API format: (name, type_code, ...)
    self._description = [(col[0], col[1], None, None, None, None, None)
                         for col in self._columns]

  @property
  def description(self):
    """Return column descriptions in DB-API format."""
    return self._description

  def fetchall(self):
    """Return all rows."""
    return self._data

  def fetchone(self):
    """Return next row or None."""
    if self._data:
      return self._data.pop(0)
    return None


def DigestClickHouseType(x):
  """Convert ClickHouse types to Python native types.

  Args:
    x: Value from ClickHouse result

  Returns:
    Python native type
  """
  if isinstance(x, Decimal):
    # Convert Decimal to int or float
    if x.as_integer_ratio()[1] == 1:
      return int(x)
    return float(x)
  if isinstance(x, tuple):
    # Convert named tuples to list
    return [DigestClickHouseType(item) for item in x]
  if isinstance(x, list):
    return [DigestClickHouseType(item) for item in x]
  if isinstance(x, dict):
    return {k: DigestClickHouseType(v) for k, v in x.items()}
  return x


# Cache for remembered connection in interactive mode
REMEMBERED_CONNECTION = None


def ConnectToClickHouse(mode, annotation_params=None):
  """Connect to ClickHouse database.

  Args:
    mode: Connection mode - 'environment', 'interactive', or 'annotation'
    annotation_params: Dict of parameters from @Engine annotation

  Returns:
    clickhouse_driver.Client connection
  """
  from clickhouse_driver import Client
  global REMEMBERED_CONNECTION

  if mode == 'interactive':
    if REMEMBERED_CONNECTION:
      return REMEMBERED_CONNECTION
    print('Enter ClickHouse connection (JSON format):')
    print('Example: {"host": "localhost", "port": 9000, "database": "default", "user": "default", "password": ""}')
    connection_str = getpass.getpass('Connection: ')
    config = json.loads(connection_str)
    connection = Client(**config)
    REMEMBERED_CONNECTION = connection
    return connection

  elif mode == 'environment':
    connection_str = os.environ.get('LOGICA_CLICKHOUSE_CONNECTION')
    assert connection_str, (
        'Please provide ClickHouse connection parameters '
        'in LOGICA_CLICKHOUSE_CONNECTION environment variable. '
        'Format: JSON object {"host": "...", "port": 9000, "database": "...", "user": "...", "password": "..."} '
        'or URL clickhouse://user:password@host:port/database')

    if connection_str.startswith('clickhouse://'):
      # Parse URL format using clickhouse_driver's from_url
      connection = Client.from_url(connection_str)
    else:
      # JSON format
      config = json.loads(connection_str)
      connection = Client(**config)
    return connection

  elif mode == 'annotation':
    # Extract parameters from @Engine annotation
    params = annotation_params or {}
    config = {
        'host': params.get('host', 'localhost'),
        'port': int(params.get('port', 9000)),
        'database': params.get('database', 'default'),
        'user': params.get('user', 'default'),
        'password': params.get('password', ''),
    }
    # Optional: secure connection
    if params.get('secure'):
      config['secure'] = True
    if params.get('verify'):
      config['verify'] = params.get('verify')
    return Client(**config)

  else:
    assert False, 'Unknown connection mode: ' + mode


def FetchResults(cursor):
  """Fetch all results and convert to Python types.

  Args:
    cursor: ClickHouseCursor object

  Returns:
    List of rows with converted types
  """
  if cursor.description is None:
    return []
  rows = cursor.fetchall()
  return [[DigestClickHouseType(cell) for cell in row] for row in rows]
