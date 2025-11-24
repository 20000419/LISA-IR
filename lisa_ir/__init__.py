"""
LISA-IR: Lifting Intermediate Semantic Analysis for Python/C API

A comprehensive framework for analyzing Python/C API code and generating
semantic-preserving intermediate representations.
"""

__version__ = "1.0.0"
__author__ = "LISA-IR Team"

from .core.lifter import Lifter
from .database.semantic_db import SemanticDatabase
from .ir.ir_nodes import Module, FuncDef, BasicBlock, Operation, Expression

__all__ = [
    'Lifter',
    'SemanticDatabase',
    'Module',
    'FuncDef',
    'BasicBlock',
    'Operation',
    'Expression'
]