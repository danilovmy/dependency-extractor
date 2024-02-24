# dependency-extractor
A library which extracts all dependencies from source files in python project

legacy stats 2036

strip_tags only one file
strip_tags falls on dataclass, but it is good.

fab strip-hints
autoflake --remove-all-unused-imports --in-place --recursive -v legacy_strip_hints/
autoflake falls on docstrings included html entities like """ \&quot;event_type\&quot; """

cd legacy_strip_hints/
mklink /J "integrations_openapi_client" "api/clients/integrations/integrations_openapi_client"
mklink /J "platform_openapi_server" "api/server_stub/platform/platform_openapi_server"

fab strip-hints
fab remove-unused-imports (662)
python extractor.py
 491

