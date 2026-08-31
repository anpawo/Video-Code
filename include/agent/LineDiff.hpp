/*
** EPITECH PROJECT, 2026
** video-code
** File description:
** LineDiff
*/

#pragma once

#include <QPair>
#include <QString>
#include <QStringList>
#include <QVector>

namespace VC
{
    // Longest common subsequence over LINES, which is what a diff is. Lines and
    // not characters: the pane colours whole rows, an author reads whole rows,
    // and a character-level diff of Python would paint half a keyword green.
    //
    // The table is (old+1)x(new+1) shorts — a scene is a few hundred lines, so
    // this is kilobytes and microseconds. A file large enough to matter is a
    // file this pane was never going to draw.
    inline QVector<QPair<int, QString>> lineDiff(const QStringList& before, const QStringList& after)
    {
        const int n = before.size();
        const int m = after.size();

        QVector<QVector<int>> lcs(n + 1, QVector<int>(m + 1, 0));
        for (int i = n - 1; i >= 0; --i)
            for (int j = m - 1; j >= 0; --j)
                lcs[i][j] = before[i] == after[j] ? lcs[i + 1][j + 1] + 1
                                                  : qMax(lcs[i + 1][j], lcs[i][j + 1]);

        // 0 same, -1 deleted, +1 added. Deletions come out BEFORE the additions
        // that replace them, which is the order an edited line reads in: what it
        // was, then what it became.
        QVector<QPair<int, QString>> out;
        int                          i = 0;
        int                          j = 0;
        while (i < n && j < m) {
            if (before[i] == after[j]) {
                out.append({0, before[i]});
                ++i;
                ++j;
            } else if (lcs[i + 1][j] >= lcs[i][j + 1]) {
                out.append({-1, before[i++]});
            } else {
                out.append({1, after[j++]});
            }
        }
        while (i < n)
            out.append({-1, before[i++]});
        while (j < m)
            out.append({1, after[j++]});
        return out;
    }
}
