#ifndef _PYTHON_H
#define _PYTHON_H

typedef struct _object PyObject;
typedef void (*PyCFunction)(void);
typedef int Py_ssize_t;
typedef unsigned long size_t;

/* Exception types */
extern PyObject *PyExc_TypeError;

/* Method definitions */
typedef struct PyMethodDef {
    const char  *ml_name;
    PyCFunction  ml_meth;
    int          ml_flags;
    const char  *ml_doc;
} PyMethodDef;

/* Module definitions */
typedef struct PyModuleDef {
    struct {
        void *m_base;
        const char *m_name;
        const char *m_doc;
        Py_ssize_t m_size;
        PyMethodDef *m_methods;
    } m_base;
    const char* m_name;
    const char* m_doc;
    Py_ssize_t m_size;
    PyMethodDef *m_methods;
} PyModuleDef;

#define PyModuleDef_HEAD_INIT { NULL, NULL, NULL, 0, NULL }

/* Method flags */
#define METH_VARARGS  0x0001
#define METH_KEYWORDS 0x0002
#define METH_NOARGS   0x0004
#define METH_O        0x0008

/* Additional functions */
PyObject *PyLong_FromSsize_t(Py_ssize_t v);
Py_ssize_t PyList_Size(PyObject *list);

/* Module initialization macro */
#define PyMODINIT_FUNC PyObject *

/* Object creation and destruction */
PyObject *PyLong_FromLong(long v);
PyObject *PyLong_FromUnsignedLong(unsigned long v);
PyObject *PyLong_FromLongLong(long long v);
PyObject *PyFloat_FromDouble(double v);
PyObject *PyUnicode_FromString(const char *u);
PyObject *PyUnicode_FromStringAndSize(const char *u, Py_ssize_t size);
PyObject *PyBytes_FromString(const char *v);
PyObject *PyBytes_FromStringAndSize(const char *v, Py_ssize_t len);
PyObject *PyList_New(Py_ssize_t len);
PyObject *PyTuple_New(Py_ssize_t len);
PyObject *PyDict_New(void);

/* Reference counting */
void Py_INCREF(PyObject *op);
void Py_DECREF(PyObject *op);
void Py_XINCREF(PyObject *op);
void Py_XDECREF(PyObject *op);

/* Sequence operations */
PyObject *PyList_GetItem(PyObject *list, Py_ssize_t index);
int PyList_SetItem(PyObject *list, Py_ssize_t index, PyObject *item);
int PyList_Append(PyObject *list, PyObject *item);
PyObject *PyTuple_GetItem(PyObject *tuple, Py_ssize_t index);
int PyTuple_SetItem(PyObject *tuple, Py_ssize_t index, PyObject *item);

/* Mapping operations */
PyObject *PyDict_GetItemString(PyObject *p, const char *key);
int PyDict_SetItemString(PyObject *p, const char *key, PyObject *val);
PyObject *PyDict_GetItem(PyObject *p, PyObject *key);
int PyDict_SetItem(PyObject *p, PyObject *key, PyObject *val);

/* Type checking */
int PyLong_Check(PyObject *p);
int PyFloat_Check(PyObject *p);
int PyUnicode_Check(PyObject *p);
int PyBytes_Check(PyObject *p);
int PyList_Check(PyObject *p);
int PyTuple_Check(PyObject *p);
int PyDict_Check(PyObject *p);
int PyCallable_Check(PyObject *p);

/* Argument parsing */
int PyArg_ParseTuple(PyObject *args, const char *format, ...);
int PyArg_ParseTupleAndKeywords(PyObject *args, PyObject *kw, const char *format, char **kwlist, ...);

/* Exception handling */
void PyErr_SetString(PyObject *exception, const char *string);
PyObject *PyErr_Occurred(void);
void PyErr_Clear(void);

/* Module creation */
struct PyModuleDef;
PyObject *PyModule_Create(struct PyModuleDef *def);

/* Object protocol */
PyObject *PyObject_Str(PyObject *v);
PyObject *PyObject_Repr(PyObject *v);
int PyObject_HasAttrString(PyObject *v, const char *name);
PyObject *PyObject_GetAttrString(PyObject *v, const char *name);
int PyObject_SetAttrString(PyObject *v, const char *name, PyObject *w);
PyObject *PyObject_GetAttr(PyObject *v, PyObject *name);
int PyObject_SetAttr(PyObject *v, PyObject *name, PyObject *w);

/* Number protocol */
PyObject *PyNumber_Add(PyObject *o1, PyObject *o2);
PyObject *PyNumber_Subtract(PyObject *o1, PyObject *o2);
PyObject *PyNumber_Multiply(PyObject *o1, PyObject *o2);
PyObject *PyNumber_TrueDivide(PyObject *o1, PyObject *o2);
PyObject *PyNumber_FloorDivide(PyObject *o1, PyObject *o2);
PyObject *PyNumber_Remainder(PyObject *o1, PyObject *o2);
PyObject *PyNumber_Power(PyObject *o1, PyObject *o2, PyObject *o3);
PyObject *PyNumber_Negative(PyObject *o);
PyObject *PyNumber_Positive(PyObject *o);
PyObject *PyNumber_Absolute(PyObject *o);

/* Conversion functions */
long PyLong_AsLong(PyObject *);
long long PyLong_AsLongLong(PyObject *);
double PyFloat_AsDouble(PyObject *);
char *PyUnicode_AsUTF8(PyObject *);
char *PyUnicode_AsUTF8AndSize(PyObject *, Py_ssize_t *);

/* Iterator protocol */
PyObject *PyObject_GetIter(PyObject *);
PyObject *PyIter_Next(PyObject *);

/* Memory management */
void *PyMem_Malloc(size_t size);
void *PyMem_Realloc(void *ptr, size_t newsize);
void PyMem_Free(void *ptr);
void *PyMem_Calloc(size_t nelem, size_t elsize);

#endif