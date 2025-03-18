# Developer Documentation

Welcome to the developer documentation for the Video-Code project. This documentation is intended to help developers understand the internal workings of the project and how to contribute effectively.

## Introduction

This section provides an overview of the Video-Code project, its goals, and its architecture.

## Project Structure

The project is organized into several directories, each serving a specific purpose:

- `src/`: Contains the source code for the project.
- `include/`: Contains the header files.
- `docs/`: Contains the documentation files.
- `tests/`: Contains the test cases.

## Architecture

The architecture of the Video-Code project is designed to be modular and extensible. It consists of the following main components:

- **Inputs**: These are the basic building blocks of the video, such as images, videos, and text. Inputs are defined in the `videocode/input` directory.
- **Transformations**: These are operations that modify the inputs, such as translating, fading, and overlaying. Transformations are defined in the `videocode/transformation` directory.
- **Timeline**: This is the sequence of frames that make up the video. Inputs are added to the timeline, and transformations are applied over time.

## Adding New Features
To add a new feature, follow these different documentation files:
- **[transformations](addEffect.md)**
