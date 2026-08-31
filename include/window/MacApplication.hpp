/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** MacApplication
*/

#pragma once

#include <QString>

namespace VC
{
    // nameApplication() — what the application menu is CALLED on macOS.
    //
    // Cocoa names it after the executable's file, which is a filename — lower
    // case, hyphen and all — rather than the product.  No Qt call reaches it;
    // see the implementation for the three that were tried.
    //
    // False when the menu bar does not exist yet, which is the normal answer for
    // the first moments of a run: the caller retries.  Always false off macOS,
    // where there is no such menu.
    bool nameApplication(const QString& name);

    // prefersReducedMotion() — whether the person has asked the system for less
    // movement (System Settings → Accessibility → Display → Reduce motion).
    //
    // An arrangement that slides and fades is a nicety for most people and a
    // symptom for some, and the setting is how they say so once rather than
    // application by application. False off macOS, where Qt offers nothing to
    // read it from.
    bool prefersReducedMotion();
} // namespace VC
