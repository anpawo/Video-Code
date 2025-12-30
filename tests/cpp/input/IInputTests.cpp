#include <gtest/gtest.h>

#include "input/IInput.hpp"

TEST(IInputSanity, HeaderCompiles)
{
    // Ensure the IInput header compiles and the type is available.
    std::shared_ptr<IInput> p = nullptr;
    EXPECT_EQ(p, nullptr);
}
