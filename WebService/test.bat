@echo off
curl -X "POST" ^
  "http://localhost:5000/api/Logica/compile" ^
  -H "accept: application/json" ^
  -H "Content-Type: application/json" ^
  -d "{\"program\": \"@Engine(\\\"mssql\\\");\n\nParent(parent: \\\"Alice\\\", child: \\\"Bob\\\");\nParent(parent: \\\"Bob\\\", child: \\\"Carol\\\");\n\nGrandparent(grandparent:, grandchild:) :-\n  Parent(parent: grandparent, child: x),\n  Parent(parent: x, child: grandchild);\", \"predicate\": \"Grandparent\"}"
