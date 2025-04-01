/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Group
*/

#pragma once

#include <nlohmann/json.hpp>

#include "input/AInput.hpp"

using json = nlohmann::json;

class Group final : public AInput
{
public:

    Group(std::vector<std::shared_ptr<IInput>>& inputs, json::object_t&& args);
    ~Group() = default;

    void apply(const std::string& name, const json::object_t& args) final;

    Frame& generateNextFrame() final;

    void overlayLastFrame(cv::Mat& background) final;

private:

    std::vector<std::shared_ptr<IInput>> _inputs;
};
