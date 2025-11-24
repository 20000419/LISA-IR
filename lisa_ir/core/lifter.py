"""
Lifter: Core lifting module for converting C code to LISA IR

This module implements the main lifting logic that transforms C code
into the LISA intermediate representation with semantic preservation.
"""

import logging
import os
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from pycparser import c_ast

from lisa_ir.ir.ir_nodes import Module, FuncDef, BasicBlock, Operation, Expression
from lisa_ir.core.ast_converter import ASTConverter
from lisa_ir.database.semantic_db import SemanticDatabase
from lisa_ir.utils.logger import get_logger


class Lifter:
    """
    Main lifter class that orchestrates the conversion from C code to LISA IR.
    
    The lifter handles:
    - C code parsing
    - AST to IR conversion
    - Semantic information integration
    - Error handling and reporting
    """
    
    def __init__(self, 
                 semantic_db_path: Optional[str] = None,
                 verbose: bool = False):
        """
        Initialize the lifter.
        
        Args:
            semantic_db_path: Path to the semantic database
            verbose: Enable verbose logging
        """
        self.logger = get_logger("Lifter", level=logging.DEBUG if verbose else logging.INFO)
        self.semantic_db = SemanticDatabase(semantic_db_path) if semantic_db_path else SemanticDatabase()
        self.ast_converter = ASTConverter(self.semantic_db)
        
        self.logger.info("Lifter initialized successfully")
    
    def lift_file(self, file_path: str) -> Module:
        """
        Lift a C source file to LISA IR.
        
        Args:
            file_path: Path to the C source file
            
        Returns:
            Module: The lifted IR module
        """
        self.logger.info(f"Lifting file: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"C source file not found: {file_path}")
        
        # Read the C source file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            c_code = f.read()
        
        return self.lift_code(c_code, file_path)
    
    def lift_code(self, c_code: str, source_path: Optional[str] = None) -> Module:
        """
        Lift C source code to LISA IR.
        
        Args:
            c_code: The C source code as a string
            source_path: Optional source file path for coordinate tracking
            
        Returns:
            Module: The lifted IR module
        """
        self.logger.info("Starting code lifting process")
        
        try:
            # Parse the C code to AST
            self.logger.debug("Parsing C code to AST")
            from ..parsers.c_parser import CCodeParser
            parser = CCodeParser(verbose=self.logger.level <= logging.DEBUG)
            
            if source_path:
                ast = parser.parse_file(source_path)
            else:
                ast = parser.parse(c_code)
            
            # Convert AST to LISA IR
            self.logger.debug("Converting AST to LISA IR")
            ir_module = self.ast_converter.convert_ast(ast, source_path or "<input>")
            
            self.logger.info("Code lifting completed successfully")
            return ir_module
            
        except Exception as e:
            self.logger.error(f"Error during code lifting: {e}")
            raise
    
    def lift_ast(self, ast: c_ast.Node, source_path: str = "<input>") -> Module:
        """
        Lift a pycparser AST to LISA IR.
        
        Args:
            ast: The pycparser AST node
            source_path: Source file path for coordinate tracking
            
        Returns:
            Module: The lifted IR module
        """
        self.logger.info("Lifting AST to LISA IR")
        
        try:
            ir_module = self.ast_converter.convert_ast(ast, source_path)
            self.logger.info("AST lifting completed successfully")
            return ir_module
            
        except Exception as e:
            self.logger.error(f"Error during AST lifting: {e}")
            raise
    
    def update_semantic_db(self, semantic_info: Dict[str, Any]) -> None:
        """
        Update the semantic database with new information.
        
        Args:
            semantic_info: Dictionary containing semantic information
        """
        self.semantic_db.update(semantic_info)
        self.logger.info(f"Updated semantic database with {len(semantic_info)} entries")
    
    def get_semantic_info(self, func_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve semantic information for a function.
        
        Args:
            func_name: Name of the function
            
        Returns:
            Semantic information dictionary or None if not found
        """
        return self.semantic_db.get_function_info(func_name)