#!/bin/bash

# Install Python 3 if not available
if ! command -v python3 &> /dev/null; then
    apt-get update && apt-get install -y python3
fi

# Start the .NET application
cd /home/site/wwwroot
dotnet WebService.dll
