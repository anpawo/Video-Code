/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Main
*/

#include <iostream>
#include <opencv2/opencv.hpp>

#include "opencv2/highgui.hpp"
#include "vm/LiveWindow.hpp"

int test()
{
    // Open the video file
    cv::VideoCapture cap("video/v.mp4"); // Replace with your video file path

    // Check if the video is opened
    if (!cap.isOpened()) {
        std::cerr << "Error: Could not open video file!" << std::endl;
        return -1;
    }

    // Load the image to insert
    cv::Mat image = cv::imread("video/ECS.png"); // Replace with your image file path
    if (image.empty()) {
        std::cerr << "Error: Could not load image!" << std::endl;
        return -1;
    }

    double totalFrames = cap.get(cv::CAP_PROP_FRAME_COUNT);

    std::cout << "Total number of frames: " << totalFrames << std::endl;

    // int frameWidth = static_cast<int>(cap.get(cv::CAP_PROP_FRAME_WIDTH));
    // int frameHeight = static_cast<int>(cap.get(cv::CAP_PROP_FRAME_HEIGHT));
    // cv::resize(image, image, cv::Size(frameWidth, frameHeight));
    int insertFrameIndex = 20;
    int frameCount = 0;

    // std::cout << cv::getBuildInformation() << std::endl;

    bool running = true;

    cv::Mat frame;
    while (true) {
        // Capture a new frame
        if (running) {
            cap >> frame;

            // Check if the frame is empty (end of video)
            if (frame.empty()) {
                std::cout << "Video has finished." << std::endl;
                break;
            }

            if (frameCount >= insertFrameIndex) {
                frame = image.clone(); // Replace the current frame with the image
            }
            frameCount++;
            cv::imshow("v", frame);
        }
        // Display the frame

        // Display the frame

        int key = cv::waitKey(96);
        std::cout << ";" << (char)(key) << ";" << std::endl;

        if (key == 'a') {
            running = false;
        } else if (key == 'e') {
            running = true;
        }

        // // Wait for 1 ms for user input, and check if the 'q' key is pressed to quit
        // if (key == 'q') {
        //     break;
        // } else if (key == 'r') {
        //     std::cout << "Video reseted by the user." << std::endl;
        //     cap.set(cv::CAP_PROP_POS_FRAMES, 0);
        // }

        if (cv::getWindowProperty("v", cv::WND_PROP_VISIBLE) < 1) {
            std::cout << "Window has been closed by the user." << std::endl;
            break;
        }
    }

    // Release the video capture object
    cap.release();
    cv::destroyAllWindows(); // Close all OpenCV windows

    return 0;
}

int main()
{
    LiveWindow win(1920, 1080);

    win.run();
}
