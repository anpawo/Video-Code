#include <gtest/gtest.h>
#include "utils/Exception.hpp"
#include <string>

class ExceptionTests : public ::testing::Test {};

TEST_F(ExceptionTests, ErrorConstructsWithMessage) {
    const std::string message = "Test error message";
    Error error(message);
    EXPECT_STREQ(error.what(), (std::string("Error: ") + message).c_str());
}

TEST_F(ExceptionTests, ErrorMessagePersists) {
    const std::string message = "Persistent error message";
    Error error(message);

    // Store the message before potentially throwing
    std::string stored_message = error.what();
    EXPECT_EQ(stored_message, std::string("Error: ") + message);

    // Test exception throwing and catching
    try {
        throw error;
    } catch (const Error& caught_error) {
        EXPECT_EQ(std::string(caught_error.what()), std::string("Error: ") + message);
    }
}