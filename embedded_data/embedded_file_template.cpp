#include "date/embedded_data_file.h"
#include <optional>
#include <unordered_map>
namespace date
{

enum class Timezone_file_name
{
  //EditLocationFileNameEnum
};

const std::string version = //EditLocationVersion;

  const uint8_t embedded_tzif_file_data[]{
    //EditLocationByteArray
  };

static const std::unordered_map<std::string, Timezone_file_name> string_to_tz_file_name_map{
  //EditLocationStringtoFilenameMap
};

std::optional<Timezone_file_name> get_filename(const std::string& filename)
{
  const auto name_itr = string_to_tz_file_name_map.find(filename);
  return (name_itr != string_to_tz_file_name_map.cend()) ? std::optional(name_itr->second) : std::nullopt;
}

std::string get_embedded_tzdb_version()
{
  return version;
}

struct fileStreamInfo
  {
    size_t startIndex;
    size_t size;
  };
  static const fileStreamInfo fileToInfoMap[]{
    //EditLocationFileStreamInfo
  };
  
imemstream get_stream(Timezone_file_name file)
{
  const auto info = fileToInfoMap[static_cast<size_t>(file)];
  return imemstream(embedded_tzif_file_data, info.startIndex, info.size);
}

imemstream get_stream(const std::string& filename)
{
  const auto file = get_filename(filename);
  if (!file)
  {
    throw std::runtime_error("Failed to find file in TZDB data: " + filename);
  }
  return get_stream(*file);
}

imemstream get_leapseconds_file()
{
  return get_stream(Timezone_file_name::leapseconds);
}

imemstream get_windowsZonesXML_file()
{
  return get_stream(Timezone_file_name::windowsZones_xml);
}

std::vector<std::string> get_available_file_names()
{
  auto result = std::vector<std::string>();
  result.reserve(string_to_tz_file_name_map.size());
  for (const auto& [filename, _] : string_to_tz_file_name_map)
  {
    result.emplace_back(std::move(filename));
  }
  return result;
}
} // namespace date
