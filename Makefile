##
## EPITECH PROJECT, 2024
## video-code
## File description:
## Makefile
##

# >>> Variables <<<

BINARY_NAME		=	video-code
BUILD_DIR		=	build
DOCKER_IMG_NAME =   ubuntu-lts-img
VCPKG_VOLUME    =   video_code_vcpkg_cache

CMAKE_FLAGS		=	-G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
VCPKG_FLAGS		= \
	-DCMAKE_TOOLCHAIN_FILE=$$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake \
	-DVCPKG_INSTALLED_DIR=$(PWD)/vcpkg_installed \
	-DWITH_FFMPEG=ON

DEBUG_FLAG		=	-DDEBUG=ON


# >>> Rules <<<

.PHONY: all
all: cmake


.PHONY: cmake
cmake:
	cmake -B $(BUILD_DIR) $(VCPKG_FLAGS) $(CMAKE_FLAGS)
	cmake --build $(BUILD_DIR)
	@ cp -f $(BUILD_DIR)/$(BINARY_NAME) .
	@ cp -f $(BUILD_DIR)/compile_commands.json .


.PHONY: debug
debug:
	cmake -B $(BUILD_DIR) $(DEBUG_FLAG) $(VCPKG_FLAGS) $(CMAKE_FLAGS)
	cmake --build $(BUILD_DIR)
	cp $(BUILD_DIR)/$(BINARY_NAME) .


.PHONY: clean
clean:
	@ $(RM) vgcore*


.PHONY: fclean
fclean: clean
	@ $(RM) -r $(BUILD_DIR)
	@ $(RM) -r vcpkg_installed
	@ $(RM) $(BINARY_NAME)


.PHONY: format
format:
	clang-format -i **/*.cpp **/*.hpp


.PHONY: docs
docs: cmake
docs: docvid
docs: docdoc


.PHONY: docvid
docvid:
	./$(BINARY_NAME) --generate


# 1. Generate the Readme
# 2. Copies the generated video to example.gif
.PHONY: docdoc
docdoc:
	./docs/readme/generate.sh


# Doesn't work
.PHONY: docker
docker:
	$(MAKE) fclean
	docker build -t $(DOCKER_IMG_NAME) .
	docker run --rm -it \
		-v "$(PWD):/work" \
		$(DOCKER_IMG_NAME)
