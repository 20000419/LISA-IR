"""
Semantic Database for LISA-IR

This module implements a semantic database that stores and manages
semantic information about Python/C API functions, including reference
counting semantics, error handling patterns, and API behavior.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List
from pathlib import Path


class SemanticDatabase:
    """
    Semantic database for storing and retrieving semantic information
    about Python/C API functions.
    
    The database stores information such as:
    - Reference counting semantics (new_ref, borrowed_ref, none)
    - Argument reference stealing behavior
    - Error return values
    - API behavior patterns
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the semantic database.
        
        Args:
            db_path: Path to the semantic database file. If None, uses default.
        """
        self.logger = logging.getLogger(__name__)
        
        if db_path is None:
            # Use a default path in the current working directory
            self.db_path = Path.cwd() / "semantic_db.json"
        else:
            self.db_path = Path(db_path)
        
        # Initialize the database
        self.db = self._load_database()
        
        self.logger.info(f"Semantic database initialized at: {self.db_path}")
        self.logger.info(f"Database contains {len(self.db)} entries")
    
    def _load_database(self) -> Dict[str, Any]:
        """
        Load the semantic database from file.
        
        Returns:
            Dict containing the semantic database
        """
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    db = json.load(f)
                self.logger.debug(f"Loaded semantic database from {self.db_path}")
                return db
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Failed to load semantic database from {self.db_path}: {e}")
                return {}
        else:
            self.logger.debug(f"Semantic database file {self.db_path} does not exist, creating empty database")
            return {}
    
    def _save_database(self) -> None:
        """
        Save the semantic database to file.
        """
        try:
            # Create directory if it doesn't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.db, f, indent=2, ensure_ascii=False)
            self.logger.debug(f"Saved semantic database to {self.db_path}")
        except IOError as e:
            self.logger.error(f"Failed to save semantic database to {self.db_path}: {e}")
    
    def get_function_info(self, func_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve semantic information for a function.
        
        Args:
            func_name: Name of the function
            
        Returns:
            Dictionary containing semantic information or None if not found
        """
        return self.db.get(func_name)
    
    def update(self, semantic_info: Dict[str, Any]) -> None:
        """
        Update the database with new semantic information.
        
        Args:
            semantic_info: Dictionary mapping function names to their semantic info
        """
        updated_count = 0
        for func_name, info in semantic_info.items():
            if self._validate_semantic_info(info):
                self.db[func_name] = info
                updated_count += 1
            else:
                self.logger.warning(f"Invalid semantic info for function {func_name}, skipping")
        
        if updated_count > 0:
            self._save_database()
            self.logger.info(f"Updated {updated_count} entries in semantic database")
    
    def update_function(self, func_name: str, info: Dict[str, Any]) -> None:
        """
        Update semantic information for a single function.
        
        Args:
            func_name: Name of the function
            info: Semantic information dictionary
        """
        if self._validate_semantic_info(info):
            self.db[func_name] = info
            self._save_database()
            self.logger.info(f"Updated semantic info for function: {func_name}")
        else:
            self.logger.warning(f"Invalid semantic info for function {func_name}, not updating")
    
    def _validate_semantic_info(self, info: Dict[str, Any]) -> bool:
        """
        Validate semantic information structure.
        
        Args:
            info: Semantic information dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(info, dict):
            return False
        
        # Validate return_ref_type if present
        if 'return_ref_type' in info:
            valid_return_types = ['new_ref', 'borrowed_ref', 'none']
            if info['return_ref_type'] not in valid_return_types:
                self.logger.warning(f"Invalid return_ref_type: {info['return_ref_type']}")
                return False
        
        # Validate arg_ref_steal if present
        if 'arg_ref_steal' in info:
            if not isinstance(info['arg_ref_steal'], dict):
                self.logger.warning("arg_ref_steal must be a dictionary")
                return False
            
            for arg_idx, steal_flag in info['arg_ref_steal'].items():
                try:
                    int(arg_idx)  # Check if arg_idx can be converted to int
                    if not isinstance(steal_flag, bool):
                        self.logger.warning(f"arg_ref_steal values must be boolean, got {type(steal_flag)}")
                        return False
                except ValueError:
                    self.logger.warning(f"arg_ref_steal keys must be numeric indices, got {arg_idx}")
                    return False
        
        # error_return can be any value, so no validation needed
        
        return True
    
    def bulk_update(self, semantic_infos: List[Dict[str, Any]]) -> int:
        """
        Bulk update the database with multiple semantic information entries.
        
        Args:
            semantic_infos: List of semantic information dictionaries
                           Each dict should have 'func_name' and 'info' keys
            
        Returns:
            Number of successfully updated entries
        """
        updated_count = 0
        for entry in semantic_infos:
            if 'func_name' in entry and 'info' in entry:
                func_name = entry['func_name']
                info = entry['info']
                
                if self._validate_semantic_info(info):
                    self.db[func_name] = info
                    updated_count += 1
                else:
                    self.logger.warning(f"Invalid semantic info for function {func_name}, skipping")
            else:
                self.logger.warning(f"Invalid entry format: {entry}")
        
        if updated_count > 0:
            self._save_database()
            self.logger.info(f"Bulk updated {updated_count} entries in semantic database")
        
        return updated_count
    
    def get_all_functions(self) -> List[str]:
        """
        Get a list of all function names in the database.
        
        Returns:
            List of function names
        """
        return list(self.db.keys())
    
    def has_function(self, func_name: str) -> bool:
        """
        Check if a function exists in the database.
        
        Args:
            func_name: Name of the function
            
        Returns:
            True if function exists, False otherwise
        """
        return func_name in self.db
    
    def remove_function(self, func_name: str) -> bool:
        """
        Remove a function from the database.
        
        Args:
            func_name: Name of the function to remove
            
        Returns:
            True if function was removed, False if it didn't exist
        """
        if func_name in self.db:
            del self.db[func_name]
            self._save_database()
            self.logger.info(f"Removed function {func_name} from semantic database")
            return True
        else:
            self.logger.debug(f"Function {func_name} not found in semantic database")
            return False
    
    def get_functions_by_ref_type(self, ref_type: str) -> List[str]:
        """
        Get all functions with a specific return reference type.
        
        Args:
            ref_type: The reference type ('new_ref', 'borrowed_ref', 'none')
            
        Returns:
            List of function names with the specified return reference type
        """
        valid_types = ['new_ref', 'borrowed_ref', 'none']
        if ref_type not in valid_types:
            raise ValueError(f"Invalid ref_type: {ref_type}. Must be one of {valid_types}")
        
        result = []
        for func_name, info in self.db.items():
            if info.get('return_ref_type') == ref_type:
                result.append(func_name)
        
        return result
    
    def merge_with(self, other_db: 'SemanticDatabase') -> None:
        """
        Merge this database with another semantic database.
        
        Args:
            other_db: Another SemanticDatabase instance to merge with
        """
        for func_name, info in other_db.db.items():
            if self._validate_semantic_info(info):
                self.db[func_name] = info
        
        self._save_database()
        self.logger.info(f"Merged with another semantic database, now contains {len(self.db)} entries")