/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Slice
*/

#include "input/composite/Slice.hpp"

#include <iterator>
#include <memory>

#include "input/IInput.hpp"

Slice::Slice(std::shared_ptr<IInput> base, int begin, int end)
    : _base(base)
    , _begin(begin < 0 ? begin + base->size() : begin)
    , _end(end < 0 ? end + base->size() + 1 : end)
    , _beginIt(base->begin() + _begin)
    , _endIt(base->begin() + _end)
    , _size(_end - _begin)
{
}

///< Deep copy of `this`
IInput* Slice::copy()
{
    return (new Slice(std::shared_ptr<IInput>(_base->copy()), _begin, _end));
}

///< Iteration
std::vector<Frame>::iterator Slice::begin()
{
    return _beginIt;
}

std::vector<Frame>::iterator Slice::end()
{
    return _endIt;
}

Frame& Slice::back()
{
    ///< TODO: not sure
    return *std::prev(_endIt);
}

void Slice::repeat([[maybe_unused]] size_t n)
{
    /// TODO: maybe add std::vector<Frame&> instead of iterators so we can duplicate the ref
}

///< Size
size_t Slice::size()
{
    return _size;
}
