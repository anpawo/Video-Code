##
## EPITECH PROJECT, 2024
## video-code
## File description:
## Makefile
##

# >>> Variables <<<

INCLUDE_PATH	:=	$(realpath ./include)

CXX				?=	g++
CXXFLAGS		+=	-std=c++20 -Wall -Wextra -Wno-deprecated
CPPFLAGS		+=	-iquote $(INCLUDE_PATH) `pkg-config --cflags opencv4`
LDFLAGS			+=	`pkg-config --libs opencv4`

SRC				=	src/Main.cpp				\
					src/vm/LiveWindow.cpp	\
					src/input/_AInput.cpp	\
					src/input/Image.cpp		\
					src/input/Video.cpp		\


OBJ				=	$(SRC:.cpp=.o)
NAME			=	vc


# >>> Rules <<<

.PHONY: all
all: $(NAME)


$(NAME): $(OBJ)
	$(CXX) -o $@ $^ $(LDFLAGS)


.PHONY: clean
clean:
	@ $(RM) $(OBJ)
	@ $(RM) vgcore*


.PHONY: fclean
fclean: clean
	@ $(RM) $(NAME)


.PHONY: re
re: fclean
	$(MAKE) all


.PHONY: debug
debug: fclean
	$(MAKE) "CXXFLAGS = $(CXXFLAGS) -g3"
