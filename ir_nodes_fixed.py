#!/usr/bin/env python3
"""
LISA IR Node Data Structures (Fixed Version)

This is a corrected version that avoids circular import issues.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Union, Optional, Any
import json


class IRNode:
    """Base class for all IR nodes."""
    coord: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, filtering None values."""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                if hasattr(value, 'to_dict'):
                    result[key] = value.to_dict()
                elif isinstance(value, list):
                    result[key] = [item.to_dict() if hasattr(item, 'to_dict') else item for item in value]
                elif isinstance(value, dict):
                    result[key] = {k: v.to_dict() if hasattr(v, 'to_dict') else v for k, v in value.items()}
                else:
                    result[key] = value
        return result


@dataclass
class Param(IRNode):
    """Function parameter."""
    name: str
    param_type: str


# Expressions
@dataclass
class Load(IRNode):
    address: 'Expression'


@dataclass
class BinaryOp(IRNode):
    op: str
    left: 'Expression'
    right: 'Expression'


@dataclass
class UnaryOp(IRNode):
    op: str
    operand: 'Expression'


@dataclass
class Constant(IRNode):
    const_type: str
    value: Any


@dataclass
class Variable(IRNode):
    name: str


@dataclass
class Cast(IRNode):
    target_type: str
    expr: 'Expression'


@dataclass
class FunctionCall(IRNode):
    function_name: str
    args: List['Expression'] = field(default_factory=list)


@dataclass
class ArrayRef(IRNode):
    array: 'Expression'
    index: 'Expression'


@dataclass
class StructRef(IRNode):
    struct: 'Expression'
    field: str
    is_arrow: bool = False


# Type aliases - defined after all expression classes
Expression = Union[
    Load, BinaryOp, UnaryOp, Constant, Variable, Cast,
    FunctionCall, ArrayRef, StructRef
]


# Operations
@dataclass
class Assign(IRNode):
    target: Variable
    value: Expression


@dataclass
class Call(IRNode):
    dest_var: Optional[str]
    function_name: str
    args: List[Expression] = field(default_factory=list)


@dataclass
class Store(IRNode):
    address: Expression
    value: Expression


@dataclass
class SemanticOp(IRNode):
    op_type: str
    attributes: Dict[str, Any] = field(default_factory=dict)


Operation = Union[Assign, Call, Store, SemanticOp]


# Terminators
@dataclass
class Return(IRNode):
    value: Optional[Expression]


@dataclass
class BranchIf(IRNode):
    condition: Expression
    true_target: str
    false_target: str


@dataclass
class Jump(IRNode):
    target: str


@dataclass
class Switch(IRNode):
    expr: Expression
    cases: Dict[Union[int, str], str] = field(default_factory=dict)
    default_target: Optional[str] = None


@dataclass
class Unreachable(IRNode):
    pass


Terminator = Union[Return, BranchIf, Jump, Switch, Unreachable]


@dataclass
class BasicBlock(IRNode):
    """Basic block with operations and terminator."""
    name: str
    operations: List[Operation] = field(default_factory=list)
    terminator: Optional[Terminator] = None

    def add_operation(self, operation: Operation) -> None:
        self.operations.append(operation)

    def set_terminator(self, terminator: Terminator) -> None:
        if self.terminator is not None:
            raise ValueError(f"Block {self.name} already has a terminator")
        self.terminator = terminator


@dataclass
class FuncDef(IRNode):
    """Function definition."""
    name: str
    params: List[Param] = field(default_factory=list)
    entry_point: str = "entry"
    blocks: Dict[str, BasicBlock] = field(default_factory=dict)
    local_vars: Dict[str, str] = field(default_factory=dict)

    def add_block(self, block: BasicBlock) -> None:
        self.blocks[block.name] = block

    def add_local_var(self, name: str, var_type: str) -> None:
        self.local_vars[name] = var_type


@dataclass
class Module(IRNode):
    """Module representation."""
    name: str
    functions: Dict[str, FuncDef] = field(default_factory=dict)
    global_vars: Dict[str, str] = field(default_factory=dict)
    includes: List[str] = field(default_factory=list)

    def add_function(self, func: FuncDef) -> None:
        self.functions[func.name] = func

    def add_global_var(self, name: str, var_type: str) -> None:
        self.global_vars[name] = var_type

    def add_include(self, include_path: str) -> None:
        if include_path not in self.includes:
            self.includes.append(include_path)


# Utility functions
def create_coord(file_path: str, line: int, col: int) -> str:
    return f"{file_path}:{line}:{col}"


def serialize_to_json(ir_node: IRNode, pretty: bool = True) -> str:
    if pretty:
        return json.dumps(ir_node.to_dict(), indent=2, ensure_ascii=False)
    else:
        return json.dumps(ir_node.to_dict(), ensure_ascii=False)


# Factory functions
def make_constant_int(value: int) -> Constant:
    return Constant(const_type="int", value=value)


def make_variable(name: str) -> Variable:
    return Variable(name=name)


def make_binary_op(op: str, left: Expression, right: Expression) -> BinaryOp:
    return BinaryOp(op=op, left=left, right=right)


def make_assign(target: str, value: Expression, coord: Optional[str] = None) -> Assign:
    return Assign(target=Variable(target), value=value, coord=coord)


def make_call(dest_var: Optional[str], func_name: str, args: List[Expression],
              coord: Optional[str] = None) -> Call:
    return Call(dest_var=dest_var, function_name=func_name, args=args, coord=coord)


def make_return(value: Optional[Expression], coord: Optional[str] = None) -> Return:
    return Return(value=value, coord=coord)


def make_jump(target: str, coord: Optional[str] = None) -> Jump:
    return Jump(target=target, coord=coord)


def make_branch_if(condition: Expression, true_target: str, false_target: str,
                   coord: Optional[str] = None) -> BranchIf:
    return BranchIf(
        condition=condition,
        true_target=true_target,
        false_target=false_target,
        coord=coord
    )


def make_semantic_op(op_type: str, attributes: Dict[str, Any],
                     coord: Optional[str] = None) -> SemanticOp:
    return SemanticOp(op_type=op_type, attributes=attributes, coord=coord)