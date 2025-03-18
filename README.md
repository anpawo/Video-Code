# Video-Code
The initial goal of this project is to create videos from code.<br>
I've always wanted to create millimetric videos and I will be able to, soon enough.

The second thought is that such thing can be used to automate the generation of video.<br>
AI have a hard time with designs, they are better with code, they could potentially take advantage of this project to generate videos with a good quality and a logical flow.

Thirdly, I want the program to have a visual interface like any other video editing app but I want it to be automatically generated from the Python API.<br>
With a code and a visual interface, anyone can make videos according to their liking.

Below is an example of the last feature added (code) and the result (video).



```py
from videocode.VideoCode import *

x = 700
y = 10

# text: Video-Code
t = text("Video-Code", 3).apply(translate(x, y), repeat(24 * 4))
t[: 24 * 3].apply(fadeIn(LEFT))
t.add()
t.keep()

# text: Made by
t = text("made by", 3).apply(translate(x, y + 80), repeat(24 * 4))
t[: 24 * 3].apply(fadeIn(LEFT))
t.add()
t.keep()


# Me
v = video("video/v.mp4").apply(translate(x, y + 175))
v[0:20].apply(fadeIn())
v.add()
v.keep()
```

<img src="docs/readme/example.gif" style="width: 50%;">

## Getting Started with Video-Code

### Installation

1. **Clone the repository:**
    ```sh
    git clone git@github.com:anpawo/Video-Code.git
    cd video-code
    ```

2. **Install dependencies:**
    Ensure you have 'python3' and 'pip' installed. Then run:
    ```sh
    pip install -r requirements.txt
    ```

    Ensure you have `vcpkg` installed and set up. Then run:
    ```sh
    vcpkg install opencv4 nlohmann-json
    ```

3. **install qt6**

go to [qt6](https://www.qt.io/download) and download the latest version of qt6.
   - Select the components you need (e.g., Qt 6.x.x, CMake, etc.).
   - Follow the installation instructions.
   - Make sure to add the Qt installation path to your system's PATH environment variable.
   - Set the `Qt6_DIR` to the Qt installation path
   - For example:
     ```sh
     export Qt6_DIR="path/to/qt6/6.x.x/gcc_64/lib/cmake/Qt6"
     ```

4. **Build the project:**
    Ensure you have CMake installed. Then run:
    ```sh
    cmake -B build
    make -C build
    cp build/video-code vc
    ```

### Launch

To launch the project, run:
```sh
./vc --sourceFile path/to/your/script.py
```
If you want to generate a video directly, use:
```sh
./vc --sourceFile path/to/your/script.py --generate
```

### Usage

To create a video with Video-Code, you need to write some simple code in Python. The flow of the video comes from the **Inputs** that you first import or create, then modify with **Transformations**, and finally add to the **timeline**.

For more detailed usage instructions, refer to the [user documentation](docs/user/user.md).

You can also check the [development documentation](docs/dev/dev.md) for more technical details.

## Patch Notes

<details>
    <summary><code>Inputs</code></summary>
<br>

- `image`
- `video`
- `text`

</details>

<br>

<details>
    <summary><code>Transformations</code></summary>
<br>

- `fade`
- `grayscale`

<br>

- `translate`
- `move`

<br>

- `overlay`
- `repeat`

</details>

<br>

<details>
    <summary><code>Patchs</code></summary>
<br>

- `transformation`: grayscale (18/03/25)
- `feature`: keep last frame of input on screen (06/03/25)
- `rework`: one stack (06/03/25)
- `transformation`: repeat (03/03/25)
- `input`: text (03/03/25)
- `rework`: position of the frames (02/03/25)
- `transformation`: move (02/03/25)

</details>
