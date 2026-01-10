

&nbsp; WebService/

&nbsp; ├── WebService.csproj           # .NET 10 project with IronPython 3.4

&nbsp; ├── Program.cs                  # App entry with Swagger

&nbsp; ├── appsettings.json            # Configuration

&nbsp; ├── Properties/

&nbsp; │   └── launchSettings.json     # Dev server settings

&nbsp; ├── Controllers/

&nbsp; │   └── LogicaController.cs     # API endpoint

&nbsp; ├── Models/

&nbsp; │   ├── LogicaRequest.cs        # Input model

&nbsp; │   └── LogicaResponse.cs       # Output model

&nbsp; └── Services/

&nbsp;     └── LogicaCompilerService.cs  # IronPython wrapper



&nbsp; API Endpoint:

&nbsp; - POST /api/logica/compile - Takes a Logica program and predicate name, returns T-SQL



&nbsp; Example request:

&nbsp; {

&nbsp;   "program": "@Engine(\\"mssql\\");\\nParent(parent: \\"Alice\\", child: \\"Bob\\");\\nGrandparent(gp:, gc:) :- Parent(parent: gp, child: x), Parent(parent: x, child: gc);",

&nbsp;   "predicate": "Grandparent"

&nbsp; }



&nbsp; To run:

&nbsp; cd WebService

&nbsp; dotnet restore

&nbsp; dotnet run



&nbsp; The service will be available at http://localhost:5000 with Swagger UI at /swagger.

