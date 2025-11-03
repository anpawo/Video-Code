
#include <gtest/gtest.h>
#include "input/media/MediaInput.hpp"
#include "input/Frame.hpp"
#include <nlohmann/json.hpp>
#include <opencv2/core/mat.hpp>

using json = nlohmann::json;

class DummyMediaInput : public MediaInput {
public:
	DummyMediaInput(const json::object_t& args) : MediaInput(args) {}
	void construct() override {}
	Frame& getFrame() { return generateNextFrame(); }
};

class MediaInputTests : public ::testing::Test {
protected:
	void SetUp() override {
		validArgs = {
			{"filepath", "tests/resources/test_image.png"},
			{"width", 100},
			{"height", 100}
		};
	}
	json::object_t validArgs;
};

TEST_F(MediaInputTests, ConstructorAcceptsValidArgs) {
	EXPECT_NO_THROW({
		DummyMediaInput input(validArgs);
	});
}

TEST_F(MediaInputTests, ThrowsOnMissingFilepath) {
	auto args = validArgs;
	args.erase("filepath");
	EXPECT_THROW({
		DummyMediaInput input(args);
	}, std::exception);
}

TEST_F(MediaInputTests, ThrowsOnInvalidDimensions) {
	auto args = validArgs;
	args["width"] = -1;
	EXPECT_THROW({
		DummyMediaInput input(args);
	}, std::exception);
}

TEST_F(MediaInputTests, FrameGenerationReturnsFrame) {
	DummyMediaInput input(validArgs);
	Frame& frame = input.getFrame();
	EXPECT_FALSE(frame.mat.empty());
	EXPECT_EQ(frame.mat.cols, 100);
	EXPECT_EQ(frame.mat.rows, 100);
}

TEST_F(MediaInputTests, ArgsAccessReflectsInput) {
	DummyMediaInput input(validArgs);
	const auto& args = input.getArgs();
	EXPECT_EQ(args.at("filepath"), validArgs.at("filepath"));
	EXPECT_EQ(args.at("width"), validArgs.at("width"));
	EXPECT_EQ(args.at("height"), validArgs.at("height"));
}
