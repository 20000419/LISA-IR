"""
Robust C Code Parser for LISA-IR

This module provides a production-grade C code parser using pycparser with comprehensive
preprocessor handling, system header management, and robust error handling.

The parser is specifically designed to handle C code that uses Python/C API functions
and includes automatic detection of system include paths and preprocessors.
"""

import os
import sys
import logging
import subprocess
import platform
from typing import List, Optional, Dict, Any
from pathlib import Path

from pycparser import c_parser, c_ast, parse_file
from pycparser.c_ast import FileAST


class CCodeParser:
    """
    A robust C code parser that handles preprocessing, system headers, and complex C constructs.

    This class provides a clean interface for parsing C source code into ASTs using pycparser,
    with automatic handling of common preprocessing challenges and system dependencies.
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize the C code parser.

        Args:
            verbose: Enable verbose logging output
        """
        self.logger = self._setup_logger(verbose)
        self.cpp_path = self._find_cpp()
        self.fake_libc_path = self._get_fake_libc_path()
        self.system_includes = self._find_system_includes()

        self.logger.info(f"Initialized C parser with CPP: {self.cpp_path}")
        self.logger.info(f"Fake libc path: {self.fake_libc_path}")
        self.logger.info(f"System includes found: {len(self.system_includes)}")

    def _setup_logger(self, verbose: bool) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        return logger

    def _find_cpp(self) -> Optional[str]:
        """
        Find the C preprocessor executable on the system.

        Returns:
            Path to the C preprocessor executable or None if not found
        """
        cpp_candidates = []

        # Platform-specific preprocessor candidates
        if platform.system() == "Windows":
            # On Windows, try to find gcc/clang in common locations
            cpp_candidates.extend([
                "gcc.exe",
                "clang.exe",
                "cpp.exe",
                r"C:\msys64\mingw64\bin\gcc.exe",
                r"C:\msys64\usr\bin\gcc.exe",
                r"C:\TDM-GCC-64\bin\gcc.exe",
            ])

            # Check common installation paths
            program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
            program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

            for base in [program_files, program_files_x86]:
                for toolchain in ["LLVM", "mingw-w64", "TDM-GCC-64"]:
                    path = os.path.join(base, toolchain, "bin", "gcc.exe")
                    if os.path.exists(path):
                        cpp_candidates.append(path)
        else:
            # Unix-like systems
            cpp_candidates.extend([
                "gcc",
                "clang",
                "cpp",
                "/usr/bin/gcc",
                "/usr/bin/clang",
                "/usr/bin/cpp",
                "/bin/gcc",
                "/bin/clang",
            ])

        # Test each candidate
        for cpp in cpp_candidates:
            try:
                result = subprocess.run(
                    [cpp, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    self.logger.debug(f"Found working preprocessor: {cpp}")
                    return cpp
            except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
                continue

        # Fallback: try to use pycparser's internal preprocessor
        self.logger.warning("No external C preprocessor found, falling back to minimal preprocessing")
        return None

    def _get_fake_libc_path(self) -> str:
        """
        Get the path to pycparser's fake libc include directory.

        Returns:
            Path to the fake libc include directory
        """
        try:
            import pycparser
            pycparser_dir = os.path.dirname(pycparser.__file__)
            fake_libc_path = os.path.join(pycparser_dir, "utils", "fake_libc_include")

            self.logger.debug(f"Looking for fake_libc_include at: {fake_libc_path}")

            if os.path.exists(fake_libc_path):
                self.logger.debug(f"Found fake_libc_include at: {fake_libc_path}")
                return os.path.abspath(fake_libc_path)

            # Try alternative locations
            alt_paths = [
                os.path.join(os.path.dirname(__file__), "fake_libc_include"),
                "fake_libc_include",
                "./fake_libc_include",
                os.path.join(pycparser_dir, "fake_libc_include"),
            ]

            for path in alt_paths:
                self.logger.debug(f"Trying alternative path: {path}")
                if os.path.exists(path):
                    self.logger.debug(f"Found fake_libc_include at: {path}")
                    return os.path.abspath(path)

            # List what we found
            self.logger.error(f"Could not find pycparser's fake_libc_include directory")
            self.logger.error(f"Searched paths: {fake_libc_path}, {alt_paths}")
            self.logger.error(f"pycparser directory: {pycparser_dir}")
            raise RuntimeError("fake_libc_include not found")

        except ImportError:
            raise RuntimeError("pycparser not installed")

    def _find_system_includes(self) -> List[str]:
        """
        Find system C include directories.

        Returns:
            List of system include directory paths
        """
        includes = []

        if not self.cpp_path:
            self.logger.warning("No C preprocessor available, cannot detect system includes")
            return includes

        try:
            # Get include paths from the preprocessor
            cmd = [self.cpp_path, "-E", "-v", "-x", "c", "/dev/null"]
            if platform.system() == "Windows":
                cmd[-1] = "NUL"  # Windows equivalent of /dev/null

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Parse the output to extract include paths
            in_include_section = False
            for line in result.stderr.split('\n'):
                line = line.strip()
                if "#include <...> search starts here:" in line:
                    in_include_section = True
                    continue
                elif "End of search list." in line:
                    in_include_section = False
                    continue
                elif in_include_section and line:
                    includes.append(line)

            # Add common include directories as fallback
            common_includes = []
            if platform.system() == "Linux":
                common_includes = [
                    "/usr/include",
                    "/usr/local/include",
                    "/usr/include/x86_64-linux-gnu"
                ]
            elif platform.system() == "Darwin":  # macOS
                common_includes = [
                    "/usr/include",
                    "/usr/local/include",
                    "/Library/Developer/CommandLineTools/usr/include",
                    "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/usr/include"
                ]
            elif platform.system() == "Windows":
                common_includes = [
                    r"C:\msys64\mingw64\include",
                    r"C:\msys64\usr\include",
                    r"C:\TDM-GCC-64\include"
                ]

            for include_dir in common_includes:
                if os.path.exists(include_dir) and include_dir not in includes:
                    includes.append(include_dir)

            self.logger.debug(f"Found system includes: {includes}")
            return includes

        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            self.logger.warning(f"Failed to detect system includes: {e}")
            return includes

    def _build_cpp_args(self, extra_cpp_args: Optional[List[str]] = None) -> List[str]:
        """
        Build the complete list of preprocessor arguments.

        Args:
            extra_cpp_args: Additional arguments to pass to the preprocessor

        Returns:
            Complete list of preprocessor arguments
        """
        if not self.cpp_path:
            # Fallback: use pycparser's built-in preprocessing
            return []

        cpp_args = []

        # Add include paths
        cpp_args.extend(["-I" + self.fake_libc_path])

        # Add system include paths
        for include_path in self.system_includes:
            cpp_args.extend(["-I" + include_path])

        # Add common defines for Python extensions
        cpp_args.extend([
            "-DPy_BUILD_CORE",
            "-DNDEBUG",
            "-D_FILE_OFFSET_BITS=64",
            "-D_LARGEFILE_SOURCE",
            "-D_LARGEFILE64_SOURCE"
        ])

        # Add user-specified arguments
        if extra_cpp_args:
            cpp_args.extend(extra_cpp_args)

        return cpp_args

    def _preprocess_code(self, c_code: str, cpp_args: Optional[List[str]] = None) -> str:
        """
        Preprocess C code using the external preprocessor.

        Args:
            c_code: The C source code to preprocess
            cpp_args: Additional preprocessor arguments

        Returns:
            Preprocessed C code
        """
        if not self.cpp_path:
            # Fallback: return original code (pycparser will handle basic preprocessing)
            return c_code

        try:
            full_cpp_args = [self.cpp_path, "-E", "-x", "c"] + self._build_cpp_args(cpp_args) + ["-"]

            self.logger.debug(f"Running preprocessor with args: {full_cpp_args}")

            result = subprocess.run(
                full_cpp_args,
                input=c_code,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self.logger.error(f"Preprocessor failed with return code {result.returncode}")
                self.logger.error(f"Preprocessor stderr: {result.stderr}")
                raise RuntimeError(f"Preprocessing failed: {result.stderr}")

            self.logger.debug("Preprocessing completed successfully")
            return result.stdout

        except subprocess.TimeoutExpired:
            raise RuntimeError("Preprocessing timed out")
        except subprocess.SubprocessError as e:
            self.logger.error(f"Preprocessing error: {e}")
            # Fallback to original code
            return c_code

    def parse(self, c_code: str, cpp_args: Optional[List[str]] = None,
              use_cpp: bool = True) -> FileAST:
        """
        Parse C source code into an AST.

        Args:
            c_code: The C source code to parse
            cpp_args: Additional arguments to pass to the preprocessor
            use_cpp: Whether to use external preprocessor

        Returns:
            pycparser FileAST object

        Raises:
            RuntimeError: If parsing fails
        """
        self.logger.info("Starting C code parsing")

        try:
            # Preprocess the code if requested
            if use_cpp and self.cpp_path:
                preprocessed_code = self._preprocess_code(c_code, cpp_args)
                self.logger.debug("Code preprocessed successfully")
            else:
                preprocessed_code = c_code

            # Create parser instance
            parser = c_parser.CParser()

            # Parse the code
            ast = parser.parse(preprocessed_code, filename="<input>")

            if not isinstance(ast, FileAST):
                raise RuntimeError("Parsing did not produce a valid FileAST")

            self.logger.info(f"Parsing completed successfully. AST has {len(ast.ext or [])} top-level declarations")
            return ast

        except c_parser.ParseError as e:
            self.logger.error(f"Parse error: {e}")
            raise RuntimeError(f"C code parsing failed: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during parsing: {e}")
            raise RuntimeError(f"Unexpected parsing error: {e}")

    def parse_file(self, file_path: str, cpp_args: Optional[List[str]] = None) -> FileAST:
        """
        Parse a C source file into an AST.

        Args:
            file_path: Path to the C source file
            cpp_args: Additional arguments to pass to the preprocessor

        Returns:
            pycparser FileAST object

        Raises:
            RuntimeError: If parsing fails
            FileNotFoundError: If the file doesn't exist
        """
        file_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"C source file not found: {file_path}")

        self.logger.info(f"Parsing C file: {file_path}")

        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                c_code = f.read()

            # Parse the code
            ast = self.parse(c_code, cpp_args)

            # Set the file coordinate for all nodes
            self._set_file_coordinates(ast, file_path)

            return ast

        except IOError as e:
            self.logger.error(f"Failed to read file {file_path}: {e}")
            raise RuntimeError(f"Failed to read file: {e}")

    def _set_file_coordinates(self, ast: FileAST, file_path: str) -> None:
        """
        Set file coordinates for all nodes in the AST.

        Args:
            ast: The AST to modify
            file_path: The source file path
        """
        def set_coord_recursive(node):
            if hasattr(node, 'coord') and node.coord:
                # Update the coordinate to include the full file path
                if not node.coord.file:
                    node.coord.file = file_path
            elif hasattr(node, 'coord'):
                # Create a new Coord object with the file path
                from pycparser.plyparser import Coord
                node.coord = Coord(file=file_path, line=1, column=1)

            # Recursively process child nodes
            # node.children() returns a list of (name, child) tuples
            for child_name, child in node.children():
                if child:
                    set_coord_recursive(child)

        set_coord_recursive(ast)

    def validate_ast(self, ast: FileAST) -> Dict[str, Any]:
        """
        Validate the parsed AST for common issues.

        Args:
            ast: The AST to validate

        Returns:
            Dictionary containing validation results
        """
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "stats": {
                "functions": 0,
                "globals": 0,
                "typedefs": 0,
                "total_declarations": 0
            }
        }

        def count_nodes(node):
            if isinstance(node, c_ast.FuncDef):
                validation_result["stats"]["functions"] += 1
            elif isinstance(node, c_ast.Decl):
                if isinstance(node.type, c_ast.FuncDecl):
                    validation_result["stats"]["functions"] += 1
                else:
                    validation_result["stats"]["globals"] += 1
            elif isinstance(node, c_ast.Typedef):
                validation_result["stats"]["typedefs"] += 1
            validation_result["stats"]["total_declarations"] += 1

            # Count child nodes recursively
            for child_name, child in node.children():
                count_nodes(child)

        try:
            count_nodes(ast)
            self.logger.info(f"AST validation completed: {validation_result['stats']}")
        except Exception as e:
            self.logger.error(f"Error during AST validation: {e}")
            validation_result["valid"] = False
            validation_result["errors"].append(str(e))

        return validation_result