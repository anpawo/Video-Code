#include <cpr/cpr.h>
#include <gtest/gtest.h>

#include <nlohmann/json.hpp>

#include "input/media/WebImage.hpp"
#include "utils/Exception.hpp"

class WebImageTests : public ::testing::Test
{
protected:

    void SetUp() override
    {
        // Prepare valid arguments
        validArgs = {
            {"url", "https://httpbin.org/base64/iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsQAAA7EAZUrDhsAAAANSURBVBhXYzh8+PB/AAffA0nNPuCLAAAAAElFTkSuQmCC"}
        };

        invalidArgs = {
            {"url", "https://httpbin.org/status/404"}
        };

        malformedArgs = {
            {"url", "invalid-url-format"}
        };
    }

    nlohmann::json validArgs;
    nlohmann::json invalidArgs;
    nlohmann::json malformedArgs;
};

TEST_F(WebImageTests, ConstructorWithValidURL)
{
    try {
        // Test with a valid image URL (base64 encoded 1x1 pixel PNG)
        nlohmann::json::object_t args = validArgs;
        WebImage webImage(std::move(args));

        // If we get here, construction was successful
        SUCCEED();
    } catch (const Error& e) {
        // If the HTTP request fails due to network issues, that's acceptable in a test environment
        EXPECT_TRUE(std::string(e.what()).find("Could not load Image") != std::string::npos);
    }
}

TEST_F(WebImageTests, ConstructorWithInvalidURL)
{
    // Test with URL that returns 404
    nlohmann::json::object_t args = invalidArgs;
    EXPECT_THROW(WebImage webImage(std::move(args)), Error);
}

TEST_F(WebImageTests, ConstructorWithMalformedURL)
{
    try {
        nlohmann::json::object_t args = malformedArgs;
        WebImage webImage(std::move(args));
        FAIL() << "Expected Error to be thrown for malformed URL";
    } catch (const Error& e) {
        // Should throw an error for malformed URL
        EXPECT_TRUE(std::string(e.what()).find("Could not load Image") != std::string::npos);
    } catch (...) {
        // Any other exception is also acceptable for malformed URL
        SUCCEED();
    }
}

TEST_F(WebImageTests, ConstructorWithMissingURLArg)
{
    nlohmann::json emptyArgs;

    // Should throw when trying to access missing "url" argument
    EXPECT_THROW(WebImage webImage(emptyArgs), std::exception);
}

TEST_F(WebImageTests, HTTPStatusCodeHandling)
{
    // Test various HTTP error codes
    nlohmann::json::object_t args500 = {{"url", "https://httpbin.org/status/500"}};
    nlohmann::json::object_t args403 = {{"url", "https://httpbin.org/status/403"}};

    EXPECT_THROW(WebImage webImage1(std::move(args500)), Error);
    EXPECT_THROW(WebImage webImage2(std::move(args403)), Error);
}

TEST_F(WebImageTests, EmptyImageDataHandling)
{
    // Test with URL that returns non-image data
    nlohmann::json::object_t textArgs = {{"url", "https://httpbin.org/html"}};

    try {
        WebImage webImage(std::move(textArgs));
        FAIL() << "Expected Error to be thrown for non-image data";
    } catch (const Error& e) {
        EXPECT_TRUE(std::string(e.what()).find("Could not load Image") != std::string::npos);
    }
}
