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
#include <utility>
#include <vector>

#include "opencv2/imgproc.hpp"
#include "utils/Exception.hpp"

WebImage::WebImage(json::object_t&& args)
    : AInput(
          std::move(args),
          {
              "url",
          }
      )
{
    construct();
}

static size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp)
{
    size_t total = size * nmemb;

    auto* buffer = reinterpret_cast<std::vector<uint8_t>*>(userp);
    buffer->insert(buffer->end(), (uint8_t*)contents, (uint8_t*)contents + total);

    return total;
}

void WebImage::construct()
{
    std::string url = _args.at("url");

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

    cv::Mat mat = cv::imdecode(data, cv::IMREAD_UNCHANGED);

    if (mat.empty()) {
        throw Error("WebImage Error: Could not load: " + url);
    }

    if (mat.channels() != 4) {
        cv::cvtColor(mat, mat, cv::COLOR_BGR2BGRA);
    }

    setBase(std::move(mat));
}
