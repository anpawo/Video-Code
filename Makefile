##
## EPITECH PROJECT, 2024
## video-code
## File description:
## Makefile
##

# >>> Variables <<<

PROJ_INCLUDE	:=	-iquote $(realpath ./include)

OPENCV_INCLUDE	=	`pkg-config --cflags opencv4`

PYTHON_INCLUDE	=	-I/usr/include/python3.12

JSON_INCLUDE	=	-I/usr/include/nlohmann

QT_INCLUDE		=	-I/usr/include/qt6					\
					-I/usr/include/qt6/QtWidgets		\
					-I/usr/include/qt6/QtGui			\
					-I/usr/include/qt6/QtCore			\
					-I/usr/lib64/qt6/mkspecs/linux-g++	\


QT_MACRO_DEF	=	-DQT_NO_DEBUG		\
					-DQT_WIDGETS_LIB	\
					-DQT_GUI_LIB		\
					-DQT_CORE_LIB		\
					-DQT_NO_KEYWORDS	\ # Fix Python Conflict


CXX				?=	g++


CXXFLAGS		+=	-std=c++20		\
					-Wall			\
					-Wextra			\
					-Wno-deprecated	\
					-pipe			\
					-O2				\
					-D_REENTRANT	\
					$(QT_MACRO_DEF)	\


CPPFLAGS		+=	$(PROJ_INCLUDE)					\
					$(OPENCV_INCLUDE)				\
					$(PYTHON_INCLUDE)				\
					$(JSON_INCLUDE)					\
					$(QT_INCLUDE)					\

OPENCV_LIB		=	`pkg-config --libs opencv4`

PYTHON_LIB		=	-lpython3.12

QT_LIB			=	/usr/lib64/libQt6Widgets.so	\
					/usr/lib64/libQt6Gui.so		\
					/usr/lib64/libQt6Core.so	\
					-lpthread					\
					-lGLX						\
					-lOpenGL					\


LDFLAGS			+=	$(OPENCV_LIB)		\
					$(PYTHON_LIB)		\
					$(QT_LIB)			\


LFLAGS			=	-O1 -Wl,-rpath-link,/usr/lib64

SRC				=	$(SRC_MAIN)			\
					$(SRC_VM)			\
					$(SRC_INPUT)		\


SRC_MAIN		=	src/Main.cpp
SRC_VM			=	src/vm/LiveWindow.cpp
SRC_INPUT		=	src/input/_AInput.cpp	\
					src/input/Image.cpp		\
					src/input/Video.cpp		\
					src/input/List.cpp		\
					src/input/Slice.cpp		\


OBJ				=	$(SRC:.cpp=.o)
NAME			=	vc


# >>> Rules <<<

.PHONY: all
all: $(NAME)


$(NAME): $(OBJ)
	$(CXX) -o $@ $^ $(LDFLAGS) $(LFLAGS)


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
