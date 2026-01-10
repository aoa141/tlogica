  WebService/

  ├── WebService.csproj           # .NET 10 project with IronPython 3.4

  ├── Program.cs                  # App entry with Swagger

  ├── appsettings.json            # Configuration

  ├── Properties/

  │   └── launchSettings.json     # Dev server settings

  ├── Controllers/

  │   └── LogicaController.cs     # API endpoint

  ├── Models/

  │   ├── LogicaRequest.cs        # Input model

  │   └── LogicaResponse.cs       # Output model

  └── Services/

      └── LogicaCompilerService.cs  # IronPython wrapper



  API Endpoint:

  - POST /api/logica/compile - Takes a Logica program and predicate name, returns T-SQL



  Example request:

  {

    "program": "@Engine(\\"mssql\\");\\nParent(parent: \\"Alice\\", child: \\"Bob\\");\\nGrandparent(gp:, gc:) :- Parent(parent: gp, child: x), Parent(parent: x, child: gc);",

    "predicate": "Grandparent"

  }



  To run:

  cd WebService

  dotnet restore

  dotnet run



  The service will be available at http://localhost:5000 with Swagger UI at /swagger.



&nbsp;Here are the deployment instructions for Azure App Service Linux (no Docker):



&nbsp; ---

&nbsp; Deployment Steps



&nbsp; 1. Create Azure Resources (Azure CLI)



&nbsp; # Login to Azure

&nbsp; az login



&nbsp; # Create resource group

&nbsp; az group create --name logica-rg --location eastus



&nbsp; # Create App Service Plan (Linux, B1 tier has Python pre-installed)

&nbsp; az appservice plan create \\

&nbsp;   --name logica-plan \\

&nbsp;   --resource-group logica-rg \\

&nbsp;   --is-linux \\

&nbsp;   --sku B1



&nbsp; # Create Web App with .NET 10 runtime

&nbsp; az webapp create \\

&nbsp;   --name logica-api-app \\

&nbsp;   --resource-group logica-rg \\

&nbsp;   --plan logica-plan \\

&nbsp;   --runtime "DOTNETCORE:10.0"



&nbsp; 2. Configure App Settings



&nbsp; # Set environment variables

&nbsp; az webapp config appsettings set \\

&nbsp;   --name logica-api-app \\

&nbsp;   --resource-group logica-rg \\

&nbsp;   --settings \\

&nbsp;     LOGICA\_PATH="/home/site/wwwroot/logica" \\

&nbsp;     PYTHON\_PATH="/usr/bin/python3"



&nbsp; # Set startup command

&nbsp; az webapp config set \\

&nbsp;   --name logica-api-app \\

&nbsp;   --resource-group logica-rg \\

&nbsp;   --startup-file "dotnet WebService.dll"



&nbsp; 3. Prepare Deployment Package



&nbsp; Create a publish folder with both .NET and Python files:



&nbsp; # From C:\\Repos\\tlogica\\WebService

&nbsp; dotnet publish -c Release -o ./publish



&nbsp; # Copy Python files to publish folder

&nbsp; mkdir ./publish/logica

&nbsp; mkdir ./publish/logica/WebService

&nbsp; xcopy /E /I ..\\parser\_py .\\publish\\logica\\parser\_py

&nbsp; xcopy /E /I ..\\compiler .\\publish\\logica\\compiler

&nbsp; xcopy /E /I ..\\common .\\publish\\logica\\common

&nbsp; xcopy /E /I ..\\type\_inference .\\publish\\logica\\type\_inference

&nbsp; copy .\\compile\_logica.py .\\publish\\logica\\WebService\\



&nbsp; 4. Deploy via ZIP



&nbsp; # Create zip file

&nbsp; cd publish

&nbsp; powershell Compress-Archive -Path \* -DestinationPath ../deploy.zip -Force

&nbsp; cd ..



&nbsp; # Deploy to Azure

&nbsp; az webapp deployment source config-zip \\

&nbsp;   --name logica-api-app \\

&nbsp;   --resource-group logica-rg \\

&nbsp;   --src deploy.zip



&nbsp; 5. Verify Deployment



&nbsp; # Get the URL

&nbsp; az webapp show --name logica-api-app --resource-group logica-rg --query defaultHostName -o tsv



&nbsp; # Test the API

&nbsp; curl -X POST "https://logica-api-app.azurewebsites.net/api/Logica/compile" \\

&nbsp;   -H "Content-Type: application/json" \\

&nbsp;   -d '{"program": "@Engine(\\"mssql\\");\\nTest(x: 1);", "predicate": "Test"}'



&nbsp; ---

&nbsp; Note: Azure App Service Linux B1 tier and above has Python 3 pre-installed at /usr/bin/python3. The LOGICA\_PATH and PYTHON\_PATH environment variables tell the service where to find the files.



