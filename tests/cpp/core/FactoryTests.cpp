#include <gtest/gtest.h>

#include <nlohmann/json.hpp>

#include "core/Factory.hpp"
#include "input/shape/Circle.hpp"
#include "input/shape/Rectangle.hpp"
#include "input/text/Text.hpp"
#include "utils/Exception.hpp"

using json = nlohmann::json;

namespace VC
{

    class FactoryTests : public ::testing::Test
    {
    protected:

        void SetUp() override
        {
            // Set up test environment
        }
    };

    TEST_F(FactoryTests, CreateRectangle)
    {
        auto it = Factory::existingInputs.find("Rectangle");
        ASSERT_NE(it, Factory::existingInputs.end());
        // Ensure a factory function is registered
        EXPECT_TRUE(static_cast<bool>(it->second));
    }

    TEST_F(FactoryTests, CreateCircle)
    {
        auto it = Factory::existingInputs.find("Circle");
        ASSERT_NE(it, Factory::existingInputs.end());
        // Ensure a factory function is registered
        EXPECT_TRUE(static_cast<bool>(it->second));
    }

    TEST_F(FactoryTests, CreateText)
    {
        auto it = Factory::existingInputs.find("Text");
        ASSERT_NE(it, Factory::existingInputs.end());
        // Ensure a factory function is registered
        EXPECT_TRUE(static_cast<bool>(it->second));
    }

    TEST_F(FactoryTests, InvalidCreation)
    {
        // Test error handling for invalid input type
        // Implementation depends on how Factory handles invalid requests
        EXPECT_THROW({ Factory::create("invalid_type", json::object()); }, std::out_of_range);
    }

} // namespace VC
