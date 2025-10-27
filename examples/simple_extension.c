/*
 * Simple Python Extension Example
 *
 * This is a well-behaved Python C extension module that demonstrates
 * proper reference counting and memory management practices.
 * It serves as a positive example for the LISA lifter analysis.
 */

#include <Python.h>

/*
 * Add two integers and return the result.
 * Returns a new reference or NULL on failure.
 */
static PyObject*
simple_add(PyObject* self, PyObject* args)
{
    long a, b;
    PyObject* result;

    if (!PyArg_ParseTuple(args, "ll", &a, &b)) {
        return NULL;  // Error already set
    }

    result = PyLong_FromLong(a + b);  // New reference
    return result;
}

/*
 * Create a list of squares from 0 to n-1.
 * Returns a new reference or NULL on failure.
 */
static PyObject*
create_squares(PyObject* self, PyObject* args)
{
    int n;
    PyObject* list;
    PyObject* item;
    int i;

    if (!PyArg_ParseTuple(args, "i", &n)) {
        return NULL;
    }

    list = PyList_New(n);  // New reference
    if (!list) {
        return NULL;
    }

    for (i = 0; i < n; i++) {
        item = PyLong_FromLong(i * i);  // New reference
        if (!item) {
            Py_DECREF(list);  // Clean up on failure
            return NULL;
        }

        // PyList_SetItem steals the reference to item
        if (PyList_SetItem(list, i, item) < 0) {
            Py_DECREF(list);  // Clean up on failure
            return NULL;
        }
    }

    return list;
}

/*
 * Check if an object is a list and return its length.
 * Returns an integer (new reference) or NULL on failure.
 */
static PyObject*
list_length(PyObject* self, PyObject* obj)
{
    Py_ssize_t length;

    if (!PyList_Check(obj)) {
        PyErr_SetString(PyExc_TypeError, "Expected a list");
        return NULL;
    }

    length = PyList_Size(obj);
    if (length < 0) {
        return NULL;  // Error already set
    }

    return PyLong_FromSsize_t(length);  // New reference
}

/*
 * Module method table
 */
static PyMethodDef SimpleExtensionMethods[] = {
    {"add", simple_add, METH_VARARGS,
     "Add two integers"},
    {"create_squares", create_squares, METH_VARARGS,
     "Create a list of squares"},
    {"list_length", list_length, METH_O,
     "Get the length of a list"},
    {NULL, NULL, 0, NULL}
};

/*
 * Module definition
 */
static struct PyModuleDef simpleextension = {
    PyModuleDef_HEAD_INIT,
    "simple_extension",
    "Simple example Python extension with proper memory management",
    -1,
    SimpleExtensionMethods
};

/*
 * Module initialization
 */
PyMODINIT_FUNC
PyInit_simple_extension(void)
{
    return PyModule_Create(&simpleextension);
}