/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Main
*/

#include <iostream>
#include <opencv2/opencv.hpp>

int main()
{
    // Open the video file
    cv::VideoCapture video("./video/v.mp4");

    // Check if the video opened successfully
    if (!video.isOpened()) {
        std::cerr << "Error: Could not open video file." << std::endl;
        return -1;
    }

    // Get the frame rate of the video
    double fps = video.get(cv::CAP_PROP_FPS);
    if (fps == 0) {
        std::cerr << "Error: Could not retrieve frame rate." << std::endl;
        return -1;
    }

    // Calculate the frame index for 2 seconds
    int desiredTimeInSeconds = 2;
    int frameIndex = static_cast<int>(fps * desiredTimeInSeconds);

    // Set the video position to the desired frame index
    video.set(cv::CAP_PROP_POS_FRAMES, frameIndex);

    // Read the frame from the video
    cv::Mat frame;
    if (!video.read(frame)) {
        std::cerr << "Error: Could not read frame from video." << std::endl;
        return -1;
    }

    // Display the frame in a window
    cv::imshow("Frame at 2 seconds", frame);

    // Wait for a key press indefinitely
    cv::waitKey(0);

    // Release the video file
    video.release();

    return 0;
}
