##
## EPITECH PROJECT, 2024
## video-code
## File description:
## Makefile
##

# >>> Variables <<<

INCLUDE		:=	$(realpath ./include)

CXX			?=	g++
CXXFLAGS	+=	-std=c++20 -Wall -Wextra
CPPFLAGS	+=	-iquote $(INCLUDE)


SRC			=	src/Main.cpp			\
				src/basicFunction.cpp	\


OBJ			=	$(SRC:.cpp=.o)
NAME		=	vc


# >>> Rules <<<

.PHONY: all
all: $(NAME)


$(NAME): $(OBJ)
	$(CXX) -o $@ $^


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
	$(MAKE) all CXXFLAGS="-g3"

