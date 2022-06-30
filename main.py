from pathlib import Path
from george.analysis.info import *
from george.analysis.python import *

for python_file in Path("vendor").glob("**/*.py"):
  python_file_info = PythonInfoVisitor(python_file).process()
  json = python_file_info.to_json()
  print(json)
  # print(PythonInfo.from_json(json))
