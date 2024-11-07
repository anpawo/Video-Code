/*
** EPITECH PROJECT, 2024
** video-code
** File description:
** Input
*/

#pragma once

#include <string>

class Input {
public:

    Input(std::string&& filename) : _filename(std::forward<std::string>(filename)) {}

    ~Input() = default;

    Input as(std::string&& aliasname)
    {
        _aliasname = std::forward<std::string>(aliasname);
        return *this;
    }

    const std::string& getFilename() const
    {
        return _filename;
    }

    const std::string& getAlias() const
    {
        if (_aliasname != "") {
            return _aliasname;
        }
        return _filename;
    }

    bool operator==(const std::string& other) const
    {
        return other == _aliasname || other == _filename;
    }

private:

    std::string _filename;
    std::string _aliasname{};
};
