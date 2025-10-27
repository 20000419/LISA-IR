# LISA-LLM Example Files

This directory contains example C Python extension modules that demonstrate various aspects of memory management and reference counting for testing the LISA semantic lifter.

## Files

### `leaky_module.c`
A Python extension module with **intentional memory management bugs** that the LISA lifter should detect and analyze:

- **Reference counting errors**: Incorrect handling of borrowed vs. new references
- **Memory leaks**: Objects not properly cleaned up on error paths
- **Double-free bugs**: Attempting to decref already stolen references
- **Complex control flow**: Multiple error paths that need proper resource cleanup

#### Functions in `leaky_module.c`:
- `create_int_list()`: Leaks list reference if `PyList_SetItem` fails
- `dict_get_borrowed()`: Incorrectly decrements a borrowed reference
- `list_append_no_steal()`: Leaks reference when `PyList_Append` fails
- `create_tuple_from_list()`: Potential double-free in error handling
- `process_sequence()`: Complex loop with proper error handling
- `complex_processing()`: Nested operations with multiple cleanup paths

### `simple_extension.c`
A **well-behaved** Python extension module that demonstrates correct memory management practices:

- Proper reference counting for all Python objects
- Correct error handling with resource cleanup
- Appropriate use of Python/C API functions
- Clean, readable code structure

#### Functions in `simple_extension.c`:
- `simple_add()`: Basic integer addition
- `create_squares()`: List creation with proper error handling
- `list_length()`: Type checking and size extraction

## Usage

These examples can be used to test the LISA lifter:

```bash
# Analyze the leaky module (should detect issues)
python lisa_lifter.py examples/leaky_module.c --verbose --summary-report

# Analyze the simple extension (should show clean code)
python lisa_lifter.py examples/simple_extension.c --verbose --summary-report

# Output to S-expression format
python lisa_lifter.py examples/leaky_module.c --format sexp --output leaky_module.ir

# Test with AI assistance (requires local LLM)
python lisa_lifter.py examples/leaky_module.c --verbose
```

## Expected Results

When analyzed with LISA-LLM, these examples should demonstrate:

1. **`leaky_module.c`**: Multiple semantic operations indicating potential issues
2. **`simple_extension.c`**: Clean semantic operations with proper reference handling

The semantic lifter should inject appropriate `new-ref`, `decr-ref`, `borrow-ref`, and `error-check` operations into the intermediate representation.