"""
AST to LISA IR Converter

This module converts pycparser AST nodes to LISA IR nodes with semantic preservation.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from pycparser import c_ast

from lisa_ir.ir.ir_nodes import (
    Module, FuncDef, BasicBlock, Operation, Expression,
    Param, Assign, Call, Return, Variable, Constant,
    BinaryOp, UnaryOp, FunctionCall, Cast, ArrayRef, StructRef,
    Load, Store, BranchIf, Jump, Switch, Unreachable,
    make_coord, make_constant_int, make_constant_string, make_variable,
    make_binary_op, make_assign, make_call, make_return, make_jump, make_branch_if
)


class ASTConverter:
    """
    Converts pycparser AST to LISA IR with semantic preservation.
    
    This class handles the complex mapping from C AST nodes to LISA IR nodes,
    including variable scoping, control flow, and semantic information integration.
    """
    
    def __init__(self, semantic_db):
        """
        Initialize the converter.
        
        Args:
            semantic_db: Semantic database for reference counting and API semantics
        """
        self.semantic_db = semantic_db
        self.logger = logging.getLogger(__name__)
        self.current_scope = {}
        self.temp_var_counter = 0
        
    def convert_ast(self, ast: c_ast.FileAST, source_path: str) -> Module:
        """
        Convert a pycparser FileAST to a LISA IR Module.
        
        Args:
            ast: The pycparser FileAST
            source_path: Source file path for coordinate tracking
            
        Returns:
            Module: The converted LISA IR module
        """
        self.logger.info("Converting AST to LISA IR")
        
        # Create the module
        module_name = source_path.replace('/', '_').replace('\\', '_').replace('.', '_')
        module = Module(name=module_name, coord=make_coord(source_path, 1, 1))
        
        # Process all top-level declarations
        for ext_decl in ast.ext:
            if isinstance(ext_decl, c_ast.FuncDef):
                func_def = self.convert_function(ext_decl, source_path)
                module.add_function(func_def)
            elif isinstance(ext_decl, c_ast.Decl) and isinstance(ext_decl.type, c_ast.FuncDecl):
                # Function declaration
                pass  # For now, we only handle function definitions
            elif isinstance(ext_decl, c_ast.Decl):
                # Global variable declaration
                pass  # For now, we don't handle global variables
        
        return module
    
    def convert_function(self, func_def: c_ast.FuncDef, source_path: str) -> FuncDef:
        """
        Convert a pycparser FuncDef to a LISA IR FuncDef.
        
        Args:
            func_def: The pycparser function definition
            source_path: Source file path for coordinate tracking
            
        Returns:
            FuncDef: The converted LISA IR function definition
        """
        # Extract function name
        func_name = func_def.decl.name
        
        # Extract parameters
        params = []
        if func_def.decl.type.args:
            for param in func_def.decl.type.args.params:
                if hasattr(param, 'name') and param.name:
                    param_name = param.name
                    param_type = str(param.type)
                    coord = make_coord(source_path, param.coord.line if param.coord else 1, 
                                      param.coord.column if param.coord else 1) if param.coord else None
                    params.append(Param(name=param_name, param_type=param_type, coord=coord))
        
        # Create the function definition
        lisa_func = FuncDef(
            name=func_name,
            params=params,
            coord=make_coord(source_path, func_def.coord.line if func_def.coord else 1, 
                           func_def.coord.column if func_def.coord else 1) if func_def.coord else None
        )
        
        # Initialize scope with parameters
        self.current_scope = {p.name: p.param_type for p in params}
        
        # Create entry block
        entry_block = BasicBlock(name="entry", coord=make_coord(source_path, func_def.coord.line if func_def.coord else 1, 1) if func_def.coord else None)
        
        # Convert the function body
        if hasattr(func_def, 'body') and func_def.body:
            self.convert_block(func_def.body, entry_block, source_path)
        
        lisa_func.add_block(entry_block)
        
        return lisa_func
    
    def convert_block(self, block: c_ast.Compound, lisa_block: BasicBlock, source_path: str):
        """
        Convert a C compound statement (block) to LISA IR operations in the given basic block.
        
        Args:
            block: The pycparser compound statement (equivalent to a block)
            lisa_block: The target LISA IR basic block
            source_path: Source file path for coordinate tracking
        """
        if not hasattr(block, 'block_items') or not block.block_items:
            return
            
        for stmt in block.block_items:
            if isinstance(stmt, c_ast.Decl):
                # Handle variable declarations
                if stmt.init:  # If the declaration has an initializer
                    # Create assignment: var = initializer
                    coord = make_coord(source_path, stmt.coord.line if stmt.coord else 1,
                                     stmt.coord.column if stmt.coord else 1) if stmt.coord else None
                    target_var = make_variable(stmt.name)
                    value_expr = self.convert_expr(stmt.init, source_path)
                    assign_op = make_assign(stmt.name, value_expr, coord)
                    lisa_block.add_operation(assign_op)
                    
                    # Add to scope
                    self.current_scope[stmt.name] = str(stmt.type)
            elif isinstance(stmt, c_ast.Assignment):
                # Handle assignment statements
                coord = make_coord(source_path, stmt.coord.line if stmt.coord else 1,
                                 stmt.coord.column if stmt.coord else 1) if stmt.coord else None
                target = self.convert_expr(stmt.lvalue, source_path)
                value = self.convert_expr(stmt.rvalue, source_path)
                
                # For now, we assume simple variable assignments
                if isinstance(target, Variable):
                    assign_op = make_assign(target.name, value, coord)
                    lisa_block.add_operation(assign_op)
            elif isinstance(stmt, c_ast.FuncCall):
                # Handle function calls
                coord = make_coord(source_path, stmt.coord.line if stmt.coord else 1,
                                 stmt.coord.column if stmt.coord else 1) if stmt.coord else None
                func_name = self.extract_func_name(stmt.name)
                
                # Convert arguments
                args = []
                if stmt.args:
                    for arg in stmt.args.exprs:
                        args.append(self.convert_expr(arg, source_path))
                
                # Check if this is a Python/C API function that needs special handling
                semantic_info = self.semantic_db.get_function_info(func_name)
                
                call_op = make_call(None, func_name, args, coord)
                lisa_block.add_operation(call_op)
            elif isinstance(stmt, c_ast.Return):
                # Handle return statements
                coord = make_coord(source_path, stmt.coord.line if stmt.coord else 1,
                                 stmt.coord.column if stmt.coord else 1) if stmt.coord else None
                if stmt.expr:
                    value = self.convert_expr(stmt.expr, source_path)
                else:
                    value = None
                return_op = make_return(value, coord)
                lisa_block.set_terminator(return_op)
            elif isinstance(stmt, c_ast.If):
                # Handle if statements - this creates multiple basic blocks
                # For now, just add a placeholder to avoid terminator conflicts
                self.logger.warning("If statements require complex control flow handling, adding placeholder")
                # This is a simplified implementation that doesn't create multiple blocks
                # In a full implementation, we would need to create proper control flow
                pass
            elif isinstance(stmt, c_ast.For):
                # Handle for loops - add placeholder
                self.logger.warning("For loops require complex control flow handling, adding placeholder")
                pass
            elif isinstance(stmt, c_ast.While):
                # Handle while loops - add placeholder
                self.logger.warning("While loops require complex control flow handling, adding placeholder")
                pass
            elif isinstance(stmt, c_ast.Compound):
                # Handle compound statements (nested blocks)
                self.convert_block(stmt, lisa_block, source_path)
    
    def convert_if_statement(self, if_stmt: c_ast.If, current_block: BasicBlock, source_path: str):
        """
        Convert an if statement to LISA IR with proper control flow.
        
        Args:
            if_stmt: The pycparser if statement
            current_block: The current LISA IR basic block
            source_path: Source file path for coordinate tracking
        """
        # Generate unique block names
        next_block_id = len(current_block.parent.blocks) if hasattr(current_block, 'parent') else 0
        then_block_name = f"then_{next_block_id}"
        else_block_name = f"else_{next_block_id+1}" 
        merge_block_name = f"merge_{next_block_id+2}"
        
        # Convert the condition
        coord = make_coord(source_path, if_stmt.coord.line if if_stmt.coord else 1,
                         if_stmt.coord.column if if_stmt.coord else 1) if if_stmt.coord else None
        condition = self.convert_expr(if_stmt.cond, source_path)
        
        # Create branch operation to then and else blocks
        branch_op = make_branch_if(condition, then_block_name, else_block_name if if_stmt.iftrue and if_stmt.iffalse else merge_block_name, coord)
        current_block.set_terminator(branch_op)
        
        # Create then block
        then_block = BasicBlock(name=then_block_name, coord=coord)
        if if_stmt.iftrue:
            self.convert_block(if_stmt.iftrue, then_block, source_path)
        # If then block doesn't have a terminator, add a jump to merge
        if then_block.terminator is None:
            then_block.set_terminator(make_jump(merge_block_name, coord))
        
        # Create else block if exists
        if if_stmt.iffalse:
            else_block = BasicBlock(name=else_block_name, coord=coord)
            self.convert_block(if_stmt.iffalse, else_block, source_path)
            # If else block doesn't have a terminator, add a jump to merge
            if else_block.terminator is None:
                else_block.set_terminator(make_jump(merge_block_name, coord))
        else:
            # If no else block, create an empty one that jumps to merge
            else_block = BasicBlock(name=else_block_name, coord=coord)
            else_block.set_terminator(make_jump(merge_block_name, coord))
        
        # Create merge block
        merge_block = BasicBlock(name=merge_block_name, coord=coord)
        # Note: We need to properly link these blocks in the function, 
        # but this is a simplified representation
        
    def convert_for_loop(self, for_stmt: c_ast.For, current_block: BasicBlock, source_path: str):
        """
        Convert a for loop to LISA IR with proper control flow.
        
        Args:
            for_stmt: The pycparser for statement
            current_block: The current LISA IR basic block
            source_path: Source file path for coordinate tracking
        """
        # For now, just convert the components without full loop structure
        # This is a simplified implementation
        if for_stmt.init:  # Initialization
            if isinstance(for_stmt.init, c_ast.DeclList):
                for decl in for_stmt.init.decls:
                    if decl.init:  # If the declaration has an initializer
                        coord = make_coord(source_path, decl.coord.line if decl.coord else 1,
                                         decl.coord.column if decl.coord else 1) if decl.coord else None
                        target_var = make_variable(decl.name)
                        value_expr = self.convert_expr(decl.init, source_path)
                        assign_op = make_assign(decl.name, value_expr, coord)
                        current_block.add_operation(assign_op)
                        
                        # Add to scope
                        self.current_scope[decl.name] = str(decl.type)
            elif isinstance(for_stmt.init, c_ast.Assignment):
                coord = make_coord(source_path, for_stmt.init.coord.line if for_stmt.init.coord else 1,
                                 for_stmt.init.coord.column if for_stmt.init.coord else 1) if for_stmt.init.coord else None
                target = self.convert_expr(for_stmt.init.lvalue, source_path)
                value = self.convert_expr(for_stmt.init.rvalue, source_path)
                
                # For now, we assume simple variable assignments
                if isinstance(target, Variable):
                    assign_op = make_assign(target.name, value, coord)
                    current_block.add_operation(assign_op)
        
        # The condition and increment parts would be handled in a full implementation
        # along with the loop body
        
        if for_stmt.stmt:  # Loop body
            # For a complete implementation, we'd need to create proper basic blocks for the loop
            # This is a simplified version
            self.convert_block(for_stmt.stmt, current_block, source_path)
    
    def convert_while_loop(self, while_stmt: c_ast.While, current_block: BasicBlock, source_path: str):
        """
        Convert a while loop to LISA IR with proper control flow.
        
        Args:
            while_stmt: The pycparser while statement
            current_block: The current LISA IR basic block
            source_path: Source file path for coordinate tracking
        """
        # Similar to for loop, this is a simplified implementation
        if while_stmt.stmt:  # Loop body
            self.convert_block(while_stmt.stmt, current_block, source_path)
    
    def convert_expr(self, expr: c_ast.Node, source_path: str) -> Expression:
        """
        Convert a pycparser expression to a LISA IR expression.
        
        Args:
            expr: The pycparser expression node
            source_path: Source file path for coordinate tracking
            
        Returns:
            Expression: The converted LISA IR expression
        """
        coord = make_coord(source_path, expr.coord.line if expr.coord else 1,
                         expr.coord.column if expr.coord else 1) if expr.coord else None
        
        if isinstance(expr, c_ast.Constant):
            # Handle constants
            if expr.type == 'int':
                try:
                    value = int(expr.value)
                    return make_constant_int(value)
                except ValueError:
                    # If conversion fails, return as string
                    return make_constant_string(expr.value)
            else:
                return make_constant_string(expr.value)
        elif isinstance(expr, c_ast.ID):
            # Handle variable references
            return make_variable(expr.name)
        elif isinstance(expr, c_ast.BinaryOp):
            # Handle binary operations
            left = self.convert_expr(expr.left, source_path)
            right = self.convert_expr(expr.right, source_path)
            return make_binary_op(expr.op, left, right)
        elif isinstance(expr, c_ast.UnaryOp):
            # Handle unary operations
            operand = self.convert_expr(expr.expr, source_path)
            # For now, return as a more general expression - we'd need to extend IR for full support
            return make_variable(f"unary_{expr.op}_{operand.name if hasattr(operand, 'name') else 'expr'}")
        elif isinstance(expr, c_ast.FuncCall):
            # Handle function calls in expressions
            func_name = self.extract_func_name(expr.name)
            
            args = []
            if expr.args:
                for arg in expr.args.exprs:
                    args.append(self.convert_expr(arg, source_path))
            
            return FunctionCall(function_name=func_name, args=args, coord=coord)
        elif isinstance(expr, c_ast.ArrayRef):
            # Handle array references
            array = self.convert_expr(expr.name, source_path)
            index = self.convert_expr(expr.subscript, source_path)
            return ArrayRef(array=array, index=index, coord=coord)
        elif isinstance(expr, c_ast.StructRef):
            # Handle struct references
            struct = self.convert_expr(expr.name, source_path)
            field = expr.field.name
            is_arrow = expr.type == '->'
            return StructRef(struct=struct, field=field, is_arrow=is_arrow, coord=coord)
        else:
            # For unsupported expressions, return a placeholder
            self.logger.warning(f"Unsupported expression type: {type(expr)}, using placeholder")
            return make_variable(f"placeholder_{type(expr).__name__}")
    
    def extract_func_name(self, func_node: Union[c_ast.ID, c_ast.Node]) -> str:
        """
        Extract function name from a function call node.
        
        Args:
            func_node: The function name node
            
        Returns:
            str: The function name
        """
        if isinstance(func_node, c_ast.ID):
            return func_node.name
        elif isinstance(func_node, c_ast.FuncCall):
            return self.extract_func_name(func_node.name)
        else:
            # For more complex expressions, we'd need more sophisticated handling
            return "unknown_func"