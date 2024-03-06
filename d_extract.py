from src_dependency_extractor.dextractor import analyse

# Use all default parameters.
result = analyse("legacy/", verbose=True)
# Enable verbose output. NOTE: Do not enable on parallel analyses.
# result = analyse("path/to/file/or/directory", verbose=True)

#
# Then you can access the following keys:
# --
dependencies = result["dependencies"]
print(dependencies)

configurations = result["configurations"]
print(configurations)