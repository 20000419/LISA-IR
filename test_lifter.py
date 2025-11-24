#!/usr/bin/env python3
"""
Test script for LISA-IR lifter
"""

import os
import tempfile
from pathlib import Path

from lisa_ir.core.lifter import Lifter


def test_lifter():
    """Test the lifter with a simple C function."""
    
    # Create a simple C code example
    c_code = """
#include <Python.h>

static PyObject* example_function(PyObject* self, PyObject* args) {
    int value;
    if (!PyArg_ParseTuple(args, "i", &value)) {
        return NULL;
    }
    
    PyObject* result = PyLong_FromLong(value * 2);
    return result;
}
"""
    
    # Write to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
        f.write(c_code)
        temp_file = f.name
    
    try:
        # Initialize the lifter
        lifter = Lifter(verbose=True)
        
        # Lift the code
        ir_module = lifter.lift_file(temp_file)
        
        # Print the IR
        print("Lifted IR Module:")
        print(ir_module.to_dict())
        
        print("\nSerialized to JSON:")
        from lisa_ir.ir.ir_nodes import serialize_to_json
        print(serialize_to_json(ir_module))
        
    finally:
        # Clean up the temporary file
        os.unlink(temp_file)


if __name__ == "__main__":
    test_lifter()