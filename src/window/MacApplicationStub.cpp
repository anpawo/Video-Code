/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** MacApplicationStub
*/

#include "window/MacApplication.hpp"

// Only macOS has an application menu to name; everywhere else the window title
// is the whole of it, and Qt already owns that.
bool VC::nameApplication(const QString&)
{
    return false;
}

bool VC::prefersReducedMotion()
{
    return false;
}
