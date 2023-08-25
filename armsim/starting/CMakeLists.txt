cmake_minimum_required(VERSION 2.6)

project(armsim)

option(BUILD_SHARED_LIBS "Create kernel as shared/dynamic library." ON)
option(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS "Export all non-static symbols on Win32" ON)

add_library(ask ask.c)

