cmake_minimum_required(VERSION 3.12)

project(armsim)

option(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS "Export all non-static symbols on Win32" ON)

# define the core set of source/object files that make up the "kernel" logic/API
add_library(kernel OBJECT ask.c)

# (make sure they are built "position-independent" as required for ELF shared objects)
set_property(TARGET kernel PROPERTY POSITION_INDEPENDENT_CODE 1)

# define a public shared library (libask.{so,dll}) built from the kernel object files
add_library(ask SHARED $<TARGET_OBJECTS:kernel>)

