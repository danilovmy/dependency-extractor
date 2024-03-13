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


python remove_hints.py filename # or foldername


find 560 dependencies
find 21 libraries to install
find 53 built-in dependencies
search of dependencies finished
summary files for hinting: 560
summary files with hints: 414
summary lines of code: 39638
summary type hints used: 4153
hinting finished
files to refactor 307
Конечный пакет для старта: Файлов: 787; папок: 234 1,46 МБ.


find 505 dependencies
find 20 libraries to install
find 52 built-in dependencies
search of dependencies finished
summary files for hinting: 505
summary files with hints: 362
summary lines of code: 29901
summary type hints used: 4075
hinting finished
files to refactor 94
Конечный пакет для старта: Файлов: 731; папок: 233, 1,19 МБ.

summary files for hinting: 2036
summary files with hints: 821
summary lines of code: 145234
summary count of classes definitions: 1988
summary count of function definitions: 7440
summary type hints used: 7045
hinting finished

summary files for hinting: 346
summary files with hints: 101
summary lines of code: 20197
summary count of classes definitions: 325
summary count of function definitions: 924
summary type hints used: 1088
hinting finished

summary files for hinting: 538
summary files with hints: 0
summary lines of code: 210510
summary count of classes definitions: 1531
summary count of function definitions: 4019
summary type hints used: 0
hinting finished