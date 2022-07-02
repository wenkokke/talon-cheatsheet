from dataclasses import dataclass
from logging import warn
from pathlib import Path
import re
from typing import Optional, Sequence
import ast
from .info import *


@dataclass
class PythonAnalyser:
    @staticmethod
    def process_file(file_path: Path, package_root: Path = Path(".")) -> PythonFileInfo:
        return PythonFileInfoVisitor(file_path, package_root).process()

    @staticmethod
    def process_package(package_root: Path) -> PythonPackageInfo:
        package_info = PythonPackageInfo(package_root=str(package_root))
        for file_path in package_root.glob("**/*.py"):
            file_path = file_path.relative_to(package_root)
            file_info = PythonAnalyser.process_file(file_path, package_root)
            package_info.add(file_info)
        return package_info


def VariableTalonName(path: Path, node: ast.AST):
    warn(
        f"""
        Variable name in {path}:{node.lineno}-{node.end_lineno}:
        {ast.unparse(node)}
        """
    )


@dataclass
class QualifiedNameError(Exception):
    name: ast.expr


def qualified_name(name: ast.expr) -> Sequence[str]:
    if type(name) == ast.Name:
        return (name.id,)
    if type(name) == ast.Attribute:
        return (*qualified_name(name.value), name.attr)
    raise QualifiedNameError(name)


@dataclass
class DecoratorInfo:
    decorator_name: str
    decorator: ast.ClassDef
    scope: str
    is_override: bool

    @staticmethod
    def from_ast(decorator_name: str, decorator: ast.expr) -> Optional["DecoratorInfo"]:
        # For @mod.action_class
        try:
            if re.match("mod", decorator.value.id) and decorator.attr == decorator_name:
                return DecoratorInfo(
                    decorator_name=decorator_name,
                    decorator=decorator,
                    scope="user",
                    is_override=False,
                )
        except AttributeError:
            pass
        # For @ctx.action_class(scope)
        try:
            if (
                re.match("ctx", decorator.func.value.id)
                and decorator.func.attr == decorator_name
            ):
                return DecoratorInfo(
                    decorator_name=decorator_name,
                    decorator=decorator,
                    scope=decorator.args[0].value,
                    is_override=True,
                )
        except AttributeError:
            pass
        return None


@dataclass
class ActionClassInfo:
    scope: str
    is_override: bool
    class_def: ast.ClassDef = None

    @staticmethod
    def from_ast(class_def: ast.ClassDef) -> Optional["ActionClassInfo"]:
        for decorator in class_def.decorator_list:
            decorator_info = DecoratorInfo.from_ast("action_class", decorator)
            if decorator_info:
                return ActionClassInfo(
                    scope=decorator_info.scope,
                    is_override=decorator_info.is_override,
                    class_def=class_def,
                )
        return None


class PythonFileInfoVisitor(ast.NodeVisitor):
    def __init__(self, file_path: Path, package_root: Path = Path(".")):
        self.file_path: Path = file_path
        self.package_root: Path = package_root
        self.declarations: dict[TalonSort, TalonDecl] = {}
        self.overrides: dict[TalonSort, dict[TalonDeclName, set[TalonDecl]]] = {}
        self.uses: dict[TalonSort, set[TalonDeclName]] = {}
        self.action_class: Optional[ActionClassInfo] = None

    def process(self) -> PythonFileInfo:
        path = self.package_root / self.file_path
        with path.open("r") as f:
            tree = ast.parse(f.read(), filename=str(self.file_path))
        self.visit(tree)
        return self.info()

    def info(self) -> PythonFileInfo:
        return PythonFileInfo(
            file_path=str(self.file_path),
            declarations={
                sort.name: declarations
                for sort, declarations in self.declarations.items()
            },
            overrides={
                sort.name: overrides for sort, overrides in self.overrides.items()
            },
            uses={sort.name: uses for sort, uses in self.uses.items()},
        )

    def add_use(self, sort: TalonSort, name: str):
        if not sort in self.uses:
            self.uses[sort] = set()
        self.uses[sort].add(name)

    def add_declaration(self, decl: TalonDecl):
        name = decl.name
        sort = decl.sort
        if decl.is_override:
            if not sort in self.overrides:
                self.overrides[sort] = {}
            if not name in self.overrides[sort]:
                self.overrides[sort][name] = set()
            self.overrides[sort][name].add(decl)
        else:
            if not sort in self.declarations:
                self.declarations[sort] = {}
            self.declarations[sort][name] = decl

    def visit_ClassDef(self, class_def: ast.ClassDef):
        self.action_class = ActionClassInfo.from_ast(class_def)
        self.generic_visit(class_def)
        self.action_class = None

    def visit_Call(self, call: ast.Call):
        try:
            func_name = qualified_name(call.func)

            # Use Action
            if func_name[0] == "actions":
                name = ".".join(func_name[1:])
                self.add_use(TalonSort.Action, name)

            mod_var, list_func = func_name

            # Declare List
            if re.match("mod", mod_var) and list_func == "list":
                name = call.args[0].value
                try:
                    desc = call.args[1].value
                except (IndexError, AttributeError):
                    desc = None
                self.add_declaration(
                    TalonDecl(
                        name=name,
                        sort=TalonSort.List,
                        file_path=str(self.file_path),
                        is_override=False,
                        desc=desc,
                        source=Source.from_ast(call),
                    )
                )

            # Declare Tag
            if re.match("mod", mod_var) and list_func == "tag":
                name = call.args[0].value
                try:
                    desc = call.args[1].value
                except (IndexError, AttributeError):
                    desc = None
                self.add_declaration(
                    TalonDecl(
                        name=name,
                        sort=TalonSort.Tag,
                        file_path=str(self.file_path),
                        is_override=False,
                        desc=desc,
                        source=Source.from_ast(call),
                    )
                )
        except AttributeError:
            VariableTalonName(self.file_path, call)
        except (ValueError, IndexError, QualifiedNameError) as e:
            pass
        self.generic_visit(call)

    def visit_Subscript(self, subscript: ast.Subscript):
        try:
            ctx_var, list_func = qualified_name(subscript.value)

            # Override List
            if re.match("ctx", ctx_var) and list_func == "lists":
                name = subscript.slice.value
                self.add_declaration(
                    TalonDecl(
                        name=name,
                        sort=TalonSort.List,
                        file_path=str(self.file_path),
                        is_override=True,
                        source=Source.from_ast(subscript),
                    )
                )
        except (QualifiedNameError, ValueError, AttributeError):
            pass

    def visit_FunctionDef(self, function_def: ast.FunctionDef):
        if self.action_class:
            # Declare or Override Action
            name = f"{self.action_class.scope}.{function_def.name}"
            desc = ast.get_docstring(function_def)
            self.add_declaration(
                TalonDecl(
                    name=name,
                    sort=TalonSort.Action,
                    file_path=str(self.file_path),
                    is_override=self.action_class.is_override,
                    desc=desc,
                    source=Source.from_ast(function_def),
                )
            )
        else:
            for decorator in function_def.decorator_list:
                decorator_info = DecoratorInfo.from_ast("capture", decorator)
                if decorator_info:
                    # Declare or Override Capture
                    name = f"{decorator_info.scope}.{function_def.name}"
                    desc = ast.get_docstring(function_def)
                    self.add_declaration(
                        TalonDecl(
                            name=name,
                            sort=TalonSort.Capture,
                            file_path=str(self.file_path),
                            is_override=decorator_info.is_override,
                            desc=desc,
                            source=Source.from_ast(function_def),
                        )
                    )
                    break
        self.generic_visit(function_def)
