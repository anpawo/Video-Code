##
## EPITECH PROJECT, 2024
## video-code
## File description:
## Makefile
##


INCLUDE		:=	./

CXX			?=	g++
CXXFLAGS	+=	-std=c++20 -Wall -Wextra -Wno-deprecated-enum-enum-conversion $(shell pkg-config --cflags opencv4)
CPPFLAGS	+=	-iquote $(INCLUDE)
LDFLAGS		+=	$(shell pkg-config --libs opencv4)


SRC			=	src/Main.cpp	\


OBJ			=	$(SRC:.cpp=.o)
NAME		=	a.out



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
	$(MAKE) all CXXFLAGS="-g3"

