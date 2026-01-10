#!/bin/bash

# Compile graph_example.l to T-SQL (MSSQL)
# Creates a temporary copy with mssql engine and prints the SQL

TEMP_FILE=$(mktemp)
trap "rm -f $TEMP_FILE" EXIT

# Replace sqlite engine with mssql
sed 's/@Engine("sqlite")/@Engine("mssql")/' graph_example.l > "$TEMP_FILE"

# Print the T-SQL for LongPath predicate
python logica.py "$TEMP_FILE" print LongPath
