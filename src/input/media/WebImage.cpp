/*
** EPITECH PROJECT, 2025
** video-code
** File description:
** Image
*/

#include "input/media/WebImage.hpp"

#include <curl/curl.h>
#include <opencv2/core/hal/interface.h>

#include <opencv2/core/mat.hpp>
#include <opencv2/imgcodecs.hpp>
#include <unordered_map>
#include <vector>

#include "opencv2/imgproc.hpp"
#include "utils/Exception.hpp"
#include "vulkan/MeshFactory.hpp"

static size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp)
{
    size_t total = size * nmemb;

    auto* buffer = reinterpret_cast<std::vector<uint8_t>*>(userp);
    buffer->insert(buffer->end(), (uint8_t*)contents, (uint8_t*)contents + total);

    return total;
}

WebImage::WebImage(json::object_t&& args)
    : AInput(std::move(args))
{
    std::string url = _baseArgs.at("url");

    auto it = _cache.find(url);
    if (it != _cache.end()) {
        _base = it->second;
        return;
    }

    CURL* curl = curl_easy_init();
    if (!curl) {
        throw std::runtime_error("Connection Error: Failed to initialize libcurl.");
    }

    std::vector<uint8_t> data;

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &data);
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 1L);

    CURLcode res = curl_easy_perform(curl);
    curl_easy_cleanup(curl);

    if (res != CURLE_OK) {
        throw std::runtime_error(std::string("Curl Error: ") + curl_easy_strerror(res));
    }

    _base = cv::imdecode(data, cv::IMREAD_UNCHANGED);

    if (_base.empty()) {
        throw Error("WebImage Error: Could not load: " + url);
    }

    if (_base.channels() != 4) {
        cv::cvtColor(_base, _base, cv::COLOR_BGR2BGRA);
    }

    _cache[url] = _base;
}

cv::Mat WebImage::getBaseMatrix(const json::object_t& _)
{
    return _base;
}

Mesh WebImage::getMesh(const Metadata& meta, const Config& config)
{
    float w = static_cast<float>(_base.cols);
    float h = static_cast<float>(_base.rows);

    if (meta.args.contains("width")) {
        w = meta.args.at("width").get<float>();
    }
    if (meta.args.contains("height")) {
        h = meta.args.at("height").get<float>();
    }

    MeshFactory factory({w, h}, meta, config);

    float opacity = meta.opacity / 255.f;
    uint16_t base = factory.vertexCount();
    factory.addVertex(0.f, 0.f, 0.f, 0.f, opacity);
    factory.addVertex(w, 0.f, 1.f, 0.f, opacity);
    factory.addVertex(w, h, 1.f, 1.f, opacity);
    factory.addVertex(0.f, h, 0.f, 1.f, opacity);

    factory.addIndex(base + 0);
    factory.addIndex(base + 1);
    factory.addIndex(base + 2);
    factory.addIndex(base + 0);
    factory.addIndex(base + 2);
    factory.addIndex(base + 3);

    Mesh mesh = factory.generateMesh();
    mesh.hasTexture = true;
    mesh.textureDescriptor = _descriptor;
    return mesh;
}
