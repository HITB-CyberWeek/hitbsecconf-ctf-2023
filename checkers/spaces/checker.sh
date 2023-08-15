#/bin/bash

cd `dirname $0`/src/bin/Release/net7.0/publish >/dev/null 2>&1
exec dotnet spaceschecker.dll "$@"
