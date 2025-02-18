/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** API
*/

#pragma once

#include <cstdio>
#include <utility>

#include "utils/Exception.hpp"
#define PY_SSIZE_T_CLEAN
#ifdef slots
#undef slots
#endif
#include <Python.h>

#include <string>

namespace python::API
{
    // Convert the C++ value to a PyObject.
    inline PyObject* convertToPythonObject(std::string&& arg)
    {
        return PyUnicode_FromString(arg.c_str());
    }

    inline PyObject* convertToPythonObject(const char*&& arg)
    {
        return PyUnicode_FromString(arg);
    }

    inline PyObject* convertToPythonObject(bool&& arg)
    {
        return PyBool_FromLong(arg);
    }

    inline PyObject* convertToPythonObject(int&& arg)
    {
        return PyLong_FromLong(arg);
    }

    inline PyObject* convertToPythonObject(double&& arg)
    {
        return PyFloat_FromDouble(arg);
    }

    inline PyObject* convertToPythonObject(float&& arg)
    {
        return PyFloat_FromDouble(arg);
    }

    // Convert the PyObject to C++ value.
    template <typename RetTy>
    RetTy convertToCppObject(PyObject* o)
    {
        if constexpr (std::is_same_v<RetTy, int>) {
            return PyLong_AsLong(o);
        } else if constexpr (std::is_same_v<RetTy, double> || std::is_same_v<RetTy, float>) {
            return PyFloat_AsDouble(o);
        } else if constexpr (std::is_same_v<RetTy, std::string>) {
            return PyUnicode_AsUTF8(o);
        }
    }

    template <typename RetTy, typename... ArgsTy>
    RetTy call(std::string&& moduleName, std::string&& functionName, ArgsTy... args)
    {
        // Initialize the Python API
        Py_Initialize();

        // Current path added to the Import Path
        PyRun_SimpleString(
            "import sys\n"
            "sys.path.append('./frontend')"
        );

        // Import the Module (file name)
        PyObject* pModule = PyImport_ImportModule(moduleName.c_str());

        if (pModule) {
            // Get the function from the module
            PyObject* pFunc = PyObject_GetAttrString(pModule, functionName.c_str());

            if (PyCallable_Check(pFunc)) {
                // Create an empty Tuple of size len(args)
                PyObject* pArgs = PyTuple_New(sizeof...(args));

                // Convert C++ arguments to Python objects
                size_t i = 0;
                ((PyTuple_SetItem(pArgs, i++, convertToPythonObject(std::forward<ArgsTy>(args)))), ...);

                // Call the function with the tuple containing the arguments
                PyObject* pValue = PyObject_CallObject(pFunc, pArgs);

                if (!pValue) {
                    Py_Finalize();
                    throw Error("Function '" + functionName + "' failed.");
                }

                if constexpr (!std::is_same_v<RetTy, void>) {
                    RetTy result = convertToCppObject<RetTy>(pValue);
                    Py_Finalize();
                    return result;
                }

            } else {
                Py_Finalize();
                throw Error("Python function '" + functionName + "' is not callable.");
            }

        } else {
            Py_Finalize();
            throw Error("Failed to load Python module: '" + moduleName + "'.");
        }
    }
};
