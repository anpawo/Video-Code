# Copilot Instructions for Video-Code

## Project context
- `Video-Code` is a hybrid C++ and Python project for programmatic video generation.
- Main C++ entrypoint is `src/Main.cpp` and build output binary is `video-code`.
- Python API lives under `videocode/` and top-level usage examples exist in `video.py` and `test/`.

## Scope and change philosophy
- Prefer minimal, targeted edits that directly satisfy the user request.
- Preserve existing public APIs and naming unless change is explicitly requested.
- Do not refactor unrelated modules while addressing a focused task.

## Build and run workflow
- Prefer existing project commands and CMake flow:
  - Configure/build via `make cmake` (uses CMake + Ninja + vcpkg flags).
  - Debug build via `make debug`.
  - Clean via `make clean` / `make fclean`.
- CI uses Ubuntu, GCC 13, Qt 6.2.4, and CMake configure/build in `build/`.
- If a change impacts runtime behavior, validate by building and (when reasonable) running `./video-code --generate`.

## Testing expectations
- Run the smallest relevant validation first (targeted build/test), then broader checks only if needed.
- C++ tests are under `tests/cpp/`; Python tests/helpers are under `tests/python/`.
- Do not attempt to repair unrelated failing tests; mention them separately if encountered.

## File and directory safety
- Treat generated/artifact paths as non-source unless explicitly requested:
  - `build/`, `htmlcov/`, `__pycache__/`, `vcpkg_installed/`, generated videos/images.
- Do not edit CI/CD workflows unless task explicitly asks for pipeline changes.

## Coding conventions
- Follow local style in touched files (indentation, includes/import ordering, naming).
- Avoid adding new dependencies unless necessary; when needed, wire them through existing tooling (`vcpkg.json`, CMake, or Python requirements) consistently.
- Avoid one-letter variable names and avoid inline comments unless they add real value.

## Documentation updates
- When behavior, setup, or developer workflow changes, update relevant docs (`README.md` or `docs/`) in the same change.

## Agent behavior
- Before destructive actions (deletions, large refactors, security-sensitive changes), ask for confirmation.
- Explain assumptions briefly when requirements are ambiguous and choose the simplest valid implementation path.
