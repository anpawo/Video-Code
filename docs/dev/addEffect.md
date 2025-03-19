# Adding a New Effect/Transformation

This document explains how to add a new effect/transformation to the Video-Code project. Follow these steps to integrate a new effect into the system.

## Step 1: Define the Effect in Python

1. Create a new Python file for your effect in the appropriate directory under [videocode/transformation](../../videocode/transformation/NewEffect.py).
2. Define a class for your effect that inherits from `Transformation`.

Example:
```python
from videocode.transformation.Transformation import Transformation

class newEffect(Transformation):
    def __init__(self, param1: int, param2: float) -> None:
        self.param1 = param1
        self.param2 = param2
```

3. Add the new effect to [_AllTransformation.py](../../videocode/transformation/_AllTransformation.py):
```python
# ...existing code...
from videocode.transformation.other.NewEffect import *
# ...existing code...
```

## Step 2: Implement the Effect in C++

1. Create a new C++ file for your effect in the appropriate directory under [src/transformation](../../src/transformation/other/newEffect.cpp).
2. Implement the effect function.

Example:
```cpp
#include <memory>
#include "input/IInput.hpp"
#include "transformation/transformation.hpp"

void transformation::newEffect(std::shared_ptr<IInput> input, Register &reg, const json::object_t &args)
{
    int param1 = args.at("param1");
    float param2 = args.at("param2");
    // Implement the effect logic here
}
```


3. Register the new effect in the transformation map [transformation.cpp](../../include/transformation/transformation.hpp)
```cpp
// ...existing code...
namespace transformation
{
    // ...existing code...
    transformation(newEffect);
    // ...existing code...
    static const std::map<std::string, std::function<void(std::shared_ptr<IInput>, Register &, const json::object_t &)>> map{
        // ...existing code...
        {"newEffect", newEffect},
        // ...existing code...
    };
}
```
