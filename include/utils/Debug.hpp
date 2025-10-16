/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Debug
*/

#pragma once

#include <iostream>

#ifdef VC_DEBUG_ON
    #define VC_LOG_DEBUG(x)              \
        do {                             \
            std::cout << x << std::endl; \
        } while (0);
#else
    #define VC_LOG_DEBUG(x)
#endif
