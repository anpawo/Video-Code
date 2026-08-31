/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** MacApplication
*/

#include "window/MacApplication.hpp"

#import <AppKit/AppKit.h>

// The bold title next to the Apple is not something Qt can set, and three
// obvious attempts all fail:
//
//   · QCoreApplication::setApplicationName() and setApplicationDisplayName()
//     name the window and the Dock tile, never this menu;
//   · writing CFBundleName into the main bundle's info dictionary does nothing,
//     because a binary run outside a bundle gets a fresh dictionary on each
//     call — the write lands in a copy;
//   · [NSProcessInfo setProcessName:] does change the process name, and the
//     menu keeps showing the executable's filename regardless.
//
// What the menu actually draws is the title of the SUBMENU of the first item of
// [NSApp mainMenu] — the item itself is the Apple menu. Setting that works, but
// only once Cocoa has built the bar, which happens well after the QMenuBar is
// filled: called too early, [NSApp mainMenu] is still nil and the write is lost.
// Hence the answer, rather than a fixed delay: try, and say whether it took.
bool VC::nameApplication(const QString& name)
{
    @autoreleasepool {
        NSMenu* bar = [NSApp mainMenu];
        if (bar.numberOfItems == 0)
            return false;

        NSMenu* application = [bar itemAtIndex:0].submenu;
        if (!application)
            return false;

        application.title = name.toNSString();
        return true;
    }
}


bool VC::prefersReducedMotion()
{
    @autoreleasepool {
        return [[NSWorkspace sharedWorkspace] accessibilityDisplayShouldReduceMotion];
    }
}
