#define USE_OS_TZDB 0
#define _WIN32 1
#include <iostream>
#include <fstream>
#include <string>
#include <algorithm>
#include <format>
#include "tz.h"

constexpr date::sys_seconds start_tp = date::sys_days(date::year{ 1800 } / date::January / date::day{ 1 });
constexpr date::sys_seconds end_tp = date::sys_days(date::year{ 2039 } / date::January / date::day{ 1 });

void write_zone(
	std::ofstream& output,
	const std::string& output_name,
	const date::time_zone& zone,
	bool is_first_zone)
{
	std::cout << "Writing zone: " << output_name << std::endl;

	if (!is_first_zone)
	{
		output << "," << std::endl;
	}

	output << std::format(R"(  {{
	"tzName":"{}",
	"transitions":[
)", output_name);

	bool is_first_transition = true;
	auto cursor = start_tp;

	while (cursor < end_tp)
	{
		const auto info = zone.get_info(cursor);
		if (start_tp < info.end)
		{
			if (!is_first_transition)
			{
				output << "," << std::endl;
			}
			is_first_transition = false;

			output << std::format(
				R"(      [
		"{}",
		{},
		{},
		{},
		{}
	  ])",
				info.abbrev,
				info.begin.time_since_epoch().count(),
				info.end.time_since_epoch().count(),
				info.offset.count(),
				info.save.count());
		}
		cursor = info.end;
	}

	output << std::endl << "]" << std::endl << "}";
}

int main(int argc, char* argv[])
{
	if (argc != 2)
	{
		std::cerr << "Usage: tzdb_HH_file_dump <tzdb_install_path>" << std::endl;
		return 1;
	}

	date::set_install(argv[1]);
	const auto& tzdb = date::reload_tzdb();

	std::ofstream output("tzdb_transitions_dump.json", std::ios::binary | std::ios::trunc);
	output << "[" << std::endl;

	bool is_first_zone = true;

	for (const auto& zone : tzdb.zones)
	{
		write_zone(output, zone.name(), zone, is_first_zone);
		is_first_zone = false;
	}

	for (const auto& link : tzdb.links)
	{
		const auto* target_zone = tzdb.locate_zone(link.target());
		std::cout << std::format(R"(Writing link: {} -> {})", link.name(), link.target()) << std::endl;
		write_zone(output, link.name(), *target_zone, false);
	}

	output << std::endl << "]" << std::endl;

	std::cout << std::format("Wrote tzdb_transitions_dump.json for {} entries (zones + links).", tzdb.zones.size() + tzdb.links.size());
	return 0;
}
