from pathlib import Path
from george.analysis.info import *
from george.analysis.python import PythonAnalyser
from george.analysis.talon import TalonAnalyser
from george.tree_sitter.node_types import *
from george.tree_sitter.talon import TreeSitterTalon
from george.tree_sitter.type_provider import *


package_root = Path("vendor/knausj_talon")
python_analyser = PythonAnalyser()
python_package_info = python_analyser.process_package(package_root)

tree_sitter_talon = TreeSitterTalon(repository_path="vendor/tree-sitter-talon")
talon_analyser = TalonAnalyser(python_package_info, tree_sitter_talon)
talon_package_info = talon_analyser.process_package(package_root)

package_info = PackageInfo(str(package_root), python_package_info, talon_package_info)

print(package_info.to_json())