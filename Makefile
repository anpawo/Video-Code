##
## EPITECH PROJECT, 2024
## video-code
## File description:
## Makefile
##

# >>> Variables <<<

BINARY_NAME		=	video-code
BUILD_DIR		=	build

# >>> Rules <<<

.PHONY: all
all: cmake


.PHONY: cmake
cmake:
	cmake -B $(BUILD_DIR)
	$(MAKE) -C $(BUILD_DIR)
	cp $(BUILD_DIR)/$(BINARY_NAME) .


.PHONY: clean
clean:
	@ $(RM) vgcore*


.PHONY: fclean
fclean: clean
	@ $(RM) -r $(BUILD_DIR)
	@ $(RM) $(BINARY_NAME)


.PHONY: format
format:
	clang-format -i **/*.cpp **/*.hpp


.PHONY: docs
docs: cmake
docs: docdoc
docs: docvid


.PHONY: docvid
docvid:
	./$(BINARY_NAME) --generate

.PHONY: docdoc
docdoc:
	./docs/readme/generate.sh
