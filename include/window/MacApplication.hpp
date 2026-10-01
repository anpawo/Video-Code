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

    // bringToFront() — make this the FRONTMOST application, not merely the key
    // window.
    //
    // Qt's QWindow::requestActivate() is not enough: QCocoaWindow's
    // implementation is makeFirstResponder + makeKeyWindow and nothing else, so
    // a process launched from a terminal draws a key-looking window while the
    // terminal stays frontmost. macOS gives the menu bar, the key events and
    // the CURSOR to the frontmost application, so in that state ⌘-shortcuts do
    // nothing and no MouseArea can change the pointer. Only this raises it.
    // No-op off macOS, where a window that is activated is already in front.
    void bringToFront();

    // sendMenuKey() — ⌘<key> handed to the native menu bar the way AppKit hands
    // it a key equivalent, true when an item took it. For a windowless run: a
    // synthetic QKeyEvent never reaches the menu bar, which is where ⌘1..4 live.
    // False off macOS.
    bool sendMenuKey(const QString& key);
} // namespace VC
