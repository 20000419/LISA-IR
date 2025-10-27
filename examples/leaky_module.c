/*
 * Leaky Module Example
 *
 * This C Python extension module demonstrates various memory management issues
 * that can occur when working with the Python/C API. It contains intentional
 * reference counting bugs and memory leaks that the LISA lifter should detect.
 *
 * This file serves as a test case for the LISA semantic lifter to demonstrate
 * its ability to identify and analyze potential security vulnerabilities in
 * Python extension modules.
 */

#include <Python.h>

/*
 * Creates a new Python list and fills it with integers.
 * Returns a new reference or NULL on failure.
 *
 * BUG: Leaks reference if PyList_SetItem fails
 */
PyObject*
create_int_list(int size)
{
    PyObject* list;
    PyObject* item;
    int i;

    // Create new list - returns new reference
    list = PyList_New(size);
    if (!list) {
        return NULL;  // NULL indicates error
    }

    // Fill list with integers
    for (i = 0; i < size; i++) {
        item = PyLong_FromLong(i);  // Returns new reference
        if (!item) {
            // BUG: Should decref list here
            return NULL;
        }

        // PyList_SetItem steals reference to item
        if (PyList_SetItem(list, i, item) < 0) {
            // BUG: Should decref both item and list here
            Py_DECREF(item);  // This is correct, but list is leaked
            return NULL;
        }
    }

    return list;  // Returns new reference
}

/*
 * Gets an item from a dictionary and returns it.
 * Returns borrowed reference, should not be decremented by caller.
 *
 * BUG: Incorrectly decrements borrowed reference
 */
PyObject*
dict_get_borrowed(PyObject* dict, const char* key)
{
    PyObject* py_key;
    PyObject* value;

    py_key = PyUnicode_FromString(key);  // New reference
    if (!py_key) {
        return NULL;
    }

    value = PyDict_GetItem(dict, py_key);  // Borrowed reference
    Py_DECREF(py_key);  // Clean up key

    if (!value) {
        return NULL;
    }

    // BUG: This is wrong - shouldn't decref borrowed reference
    Py_DECREF(value);  // This will cause issues!

    return value;  // Returns potentially invalid reference
}

/*
 * Appends an item to a list without stealing the reference.
 * Returns 0 on success, -1 on failure.
 *
 * BUG: Leaks reference if PyList_Append fails
 */
int
list_append_no_steal(PyObject* list, PyObject* item)
{
    int result;

    // PyList_Append does NOT steal the reference
    result = PyList_Append(list, item);
    if (result < 0) {
        // BUG: Should not decref item here since we don't own it
        Py_DECREF(item);  // This is wrong!
        return -1;
    }

    return 0;
}

/*
 * Creates a new tuple from a list of values.
 * Returns new reference or NULL on failure.
 *
 * BUG: Incorrect reference handling for arguments
 */
PyObject*
create_tuple_from_list(PyObject* values[], int count)
{
    PyObject* tuple;
    int i;

    tuple = PyTuple_New(count);
    if (!tuple) {
        return NULL;
    }

    for (i = 0; i < count; i++) {
        // PyTuple_SetItem steals the reference
        if (PyTuple_SetItem(tuple, i, values[i]) < 0) {
            // BUG: values[i] reference is already stolen on failure
            // but we're trying to decref it again
            Py_DECREF(values[i]);  // This could cause double-free
            Py_DECREF(tuple);
            return NULL;
        }
    }

    return tuple;
}

/*
 * Processes a sequence and returns a new list.
 * Demonstrates complex control flow with error handling.
 * Returns new reference or NULL on failure.
 */
PyObject*
process_sequence(PyObject* seq)
{
    PyObject* result;
    PyObject* item;
    PyObject* processed_item;
    Py_ssize_t i, length;

    // Get sequence length
    length = PySequence_Length(seq);
    if (length < 0) {
        return NULL;
    }

    // Create result list
    result = PyList_New((Py_ssize_t)length);
    if (!result) {
        return NULL;
    }

    // Process each item
    for (i = 0; i < length; i++) {
        item = PySequence_GetItem(seq, i);  // New reference
        if (!item) {
            Py_DECREF(result);
            return NULL;
        }

        // Process the item (just double it for this example)
        if (PyLong_Check(item)) {
            long value = PyLong_AsLong(item);
            if (value == -1 && PyErr_Occurred()) {
                Py_DECREF(item);
                Py_DECREF(result);
                return NULL;
            }
            processed_item = PyLong_FromLong(value * 2);  // New reference
        } else {
            // For non-integers, just return the original
            processed_item = item;
            Py_INCREF(processed_item);  // Need new reference for result
        }

        Py_DECREF(item);  // Done with original item

        // Add to result list
        if (PyList_SetItem(result, i, processed_item) < 0) {
            Py_DECREF(processed_item);  // Clean up on failure
            Py_DECREF(result);
            return NULL;
        }
    }

    return result;
}

/*
 * Complex function with multiple error paths.
 * Demonstrates nested error handling and resource cleanup.
 */
PyObject*
complex_processing(PyObject* args)
{
    PyObject* input_dict;
    PyObject* key_list;
    PyObject* result_list;
    PyObject* key, *value, *processed_value;
    Py_ssize_t i, num_keys;

    // Parse arguments
    if (!PyArg_ParseTuple(args, "O!", &PyDict_Type, &input_dict)) {
        return NULL;
    }

    // Get dictionary keys
    key_list = PyDict_Keys(input_dict);  // New reference
    if (!key_list) {
        return NULL;
    }

    num_keys = PyList_Size(key_list);
    if (num_keys < 0) {
        Py_DECREF(key_list);
        return NULL;
    }

    // Create result list
    result_list = PyList_New(num_keys);
    if (!result_list) {
        Py_DECREF(key_list);
        return NULL;
    }

    // Process each key-value pair
    for (i = 0; i < num_keys; i++) {
        key = PyList_GetItem(key_list, i);  // Borrowed reference

        value = PyDict_GetItem(input_dict, key);  // Borrowed reference
        if (!value) {
            // This shouldn't happen, but handle it
            Py_DECREF(key_list);
            Py_DECREF(result_list);
            return NULL;
        }

        // Process the value (convert to string if not already)
        if (PyUnicode_Check(value)) {
            processed_value = value;
            Py_INCREF(processed_value);  // Need new reference
        } else {
            processed_value = PyObject_Str(value);  // New reference
            if (!processed_value) {
                Py_DECREF(key_list);
                Py_DECREF(result_list);
                return NULL;
            }
        }

        // Add to result list
        if (PyList_SetItem(result_list, i, processed_value) < 0) {
            Py_DECREF(processed_value);
            Py_DECREF(key_list);
            Py_DECREF(result_list);
            return NULL;
        }
    }

    // Clean up intermediate objects
    Py_DECREF(key_list);

    return result_list;
}

/*
 * Module method table
 */
static PyMethodDef LeakyModuleMethods[] = {
    {"create_int_list", create_int_list, METH_VARARGS,
     "Create a list of integers (with intentional bugs)"},
    {"dict_get_borrowed", dict_get_borrowed, METH_VARARGS,
     "Get item from dictionary (with reference counting bug)"},
    {"list_append_no_steal", list_append_no_steal, METH_VARARGS,
     "Append item to list (with memory leak)"},
    {"create_tuple_from_list", create_tuple_from_list, METH_VARARGS,
     "Create tuple from list (with double-free bug)"},
    {"process_sequence", process_sequence, METH_O,
     "Process a sequence and return new list"},
    {"complex_processing", complex_processing, METH_VARARGS,
     "Complex processing with multiple error paths"},
    {NULL, NULL, 0, NULL}
};

/*
 * Module definition
 */
static struct PyModuleDef leakymodule = {
    PyModuleDef_HEAD_INIT,
    "leaky_module",
    "Example module with intentional memory management bugs",
    -1,
    LeakyModuleMethods
};

/*
 * Module initialization
 */
PyMODINIT_FUNC
PyInit_leaky_module(void)
{
    return PyModule_Create(&leakymodule);
}