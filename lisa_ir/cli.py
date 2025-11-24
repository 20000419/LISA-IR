#!/usr/bin/env python3
"""
Command Line Interface for LISA-IR
"""

import argparse
import json
import sys
from pathlib import Path

from lisa_ir.core.lifter import Lifter


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LISA-IR: Lifting Intermediate Semantic Analysis for Python/C API"
    )
    parser.add_argument(
        "input_file",
        help="Input C source file to lift"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file for the lifted IR (default: stdout)",
        default=None
    )
    parser.add_argument(
        "--format",
        choices=["json", "sexp"],
        default="json",
        help="Output format (default: json)"
    )
    parser.add_argument(
        "--semantic-db",
        help="Path to semantic database file",
        default=None
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize the lifter
        lifter = Lifter(semantic_db_path=args.semantic_db, verbose=args.verbose)
        
        # Lift the input file
        ir_module = lifter.lift_file(args.input_file)
        
        # Serialize the IR
        if args.format == "json":
            output = ir_module.to_dict()
            output_str = json.dumps(output, indent=2)
        elif args.format == "sexp":
            from lisa_ir.ir.ir_nodes import serialize_to_sexp
            output_str = serialize_to_sexp(ir_module)
        
        # Output the result
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_str)
            print(f"IR output written to {args.output}")
        else:
            print(output_str)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()