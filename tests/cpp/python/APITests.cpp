#include <gtest/gtest.h>
#include "python/API.hpp"

TEST(PythonAPISanity, HeaderCompiles) {
    // Including the Python API header should compile; we avoid calling into
    // the Python C API here to keep tests lightweight and not require a
    // running Python interpreter during the C++ unit test build.
    EXPECT_TRUE(true);
}
