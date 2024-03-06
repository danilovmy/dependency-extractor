# dependency-extractor
A library which extracts all dependencies from source files in python project

legacy stats 2036 files
622 folders


https://github.com/Wally869/TypeStripper
cut only simply assignments

https://github.com/abarker/strip-hints
strip_hints only one file
strip_hints falls on dataclass, but it is works.


fab strip-hints
autoflake --remove-all-unused-imports --in-place --recursive -v legacy_strip_hints/
autoflake falls on docstrings included html entities like """ \&quot;event_type\&quot; """

cd legacy_strip_hints/
mklink /J "integrations_openapi_client" "api/clients/integrations/integrations_openapi_client"
mklink /J "platform_openapi_server" "api/server_stub/platform/platform_openapi_server"

fab strip-hints
fab remove-unused-imports (662)
python extractor.py (491)

work with typehints:

summary type hints used: 18116
summary files with hints: 768
summary files: 1914


lib type_stripper build on the regexp. It is not works due permanent changes of typhints rules
https://github.com/Wally869/TypeStripper

dependency extractor. Not collect dependency in local project
https://github.com/dacresearchgroup/c137-morphemic-dependency-extractor
