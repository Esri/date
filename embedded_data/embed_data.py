import os
from collections import namedtuple
import sys
def enumify_tz_name(tz_name: str) -> str:
    return tz_name.replace('\\', '_').replace('/', '_').replace('+', '_P').replace('-', '_').replace('.', '_')

def tz_name_to_enum(tz_name: str) -> str:
    return "Timezone_file_name::" + enumify_tz_name(tz_name)

def filename_to_tz_name(file_name: str) -> str:
    return file_name.replace("\\", "/")

def filename_to_enum_entry(file_name: str, canonical_name: str) -> str:
    return f'{{R"({filename_to_tz_name(file_name)})", {tz_name_to_enum(canonical_name)} }},\n'

def canonical_filename_to_enum_entry(file_name: str) -> str:
    return filename_to_enum_entry(file_name, file_name)

def error_if_file_not_found(tzdb_path: str, filename: str, error: str):
    path = os.path.join(tzdb_path, filename)
    if not os.path.isfile(path):
       sys.exit(error)
       
def get_tzdb_path_from_arguments() -> str:
    if len(sys.argv) != 2 or sys.argv[1].lower() == "-h":
        sys.exit("Expected usage: Python embed_data.py filePathToCompiledTZDB")
    tzdb_path = sys.argv[1]

    error_if_file_not_found(tzdb_path, "CET", "Could not find CET in listed directory, are you sure this is a compiled tzdb?")
    error_if_file_not_found(tzdb_path, "windowsZones.xml", "Could not find windowsZones.xml in listed directory, please copy from source.")
    error_if_file_not_found(tzdb_path, "leapseconds", "Could not find leapseconds in listed directory, please copy from an uncompiled TZDB?")
    error_if_file_not_found(tzdb_path, "version", "Could not find version file, please copy from uncompiled tzdb")
    error_if_file_not_found(tzdb_path, "backward", "Could not find backward file, please copy from uncompiled tzdb")
    return tzdb_path

def get_file_names(tzdb_path: str) -> list:
    files = []
    for (root, dirnames, filenames) in os.walk(tzdb_path):
        dirname = root[len(tzdb_path):] 
        if len(dirname) != 0:
            dirname +='\\'
        files.extend([f'{dirname}{i}' for i in filenames if i[0] != '.' and i[:5] != "posix"  and i not in ["Factory", "iso3166", "right", "+VERSION", "version", "zone", "zone1970", "tzdata", "leap-seconds", "backward"]])
    return files

def load_leap_second_data(tzdb_path: str) -> list:
    with open(os.path.join(tzdb_path, "leapseconds"), "r") as in_file:
        leapseconds_text = "".join([line for line in in_file.readlines() if line[0] != '#' and len(line.strip()) != 0])
        return leapseconds_text.encode()

def parse_link_entry(link_line: str) -> tuple:
    LinkInfo = namedtuple("LinkInfo", "name target")
    parsed_line = link_line.split()
    return LinkInfo(parsed_line[2], parsed_line[1])#Format is LINK    TARGET    NAME

def load_backward_data(tzdb_path: str) -> list:
    with open(os.path.join(tzdb_path, "backward"), "r") as in_file:
        return [parse_link_entry(line) for line in in_file.readlines() if line[0] != '#' and len(line.strip()) != 0]

def load_file(tzdb_path: str, filename: str) -> list:
    with open(os.path.join(tzdb_path, filename), "rb") as in_file:
        return in_file.read()

def load_file_data(tzdb_path: str, files: list) -> tuple:
    FileInfo = namedtuple("FileInfo", "startIndex size")
    file_info = {}
    file_data = []
    for (filename) in files:
        initial_index = len(file_data)

        if (filename == "leapseconds"):
            file_data.extend(load_leap_second_data(tzdb_path))
        else:
            file_data.extend(load_file(tzdb_path, filename))
    
        size = len(file_data) - initial_index
        file_info[filename] = FileInfo(initial_index, size)

    return file_info, file_data

def get_version_string(tzdb_path: str) -> str:
    with open(os.path.join(tzdb_path, "version"), "r") as version_info:
        return f'"{version_info.readline().strip()}"'

def get_template_string() -> str:
     with open("embedded_file_template.cpp", "r") as template:
        return template.read()

def compile_template_string(data_file_contents: str, file_enum_contents: str, tz_to_enum_map_contents: str, tz_to_file_info_Map_contents: str, version_contents: str ):
    template = get_template_string()
    template = template.replace("//EditLocationByteArray", data_file_contents)
    template = template.replace("//EditLocationFileNameEnum", file_enum_contents)
    template = template.replace("//EditLocationStringtoFilenameMap", tz_to_enum_map_contents)
    template = template.replace("//EditLocationFileStreamInfo", tz_to_file_info_Map_contents)
    return template.replace("//EditLocationVersion", version_contents)
  
def write_CPP_file(fileContents: str):
    with open("embedded_data_file.cpp", "w") as code_file:
        code_file.write(fileContents)

def embed_compiled_TZDB(tzdb_path: str):
    files = get_file_names(tzdb_path)
    file_info, file_data = load_file_data(tzdb_path, files)

    tz_to_file_info_map_string = "fileStreamInfo"
    enum_entries_string =  ""
    tz_to_enum_map_string = ""
    for (filename) in files: #Foreach file
        enum_entries_string+= enumify_tz_name(filename) + ",\n"# Add an enum entry
        tz_to_enum_map_string += canonical_filename_to_enum_entry(filename) #add a mapping from filename string to enum name above
        info = file_info[filename] # Find the file location in the byte array
        tz_to_file_info_map_string += f'{{{info.startIndex},{info.size}}},//{enumify_tz_name(filename)}\n' #and store this info in the FileInfo Map at the files enum index.

    links = load_backward_data(tzdb_path)
    for (link) in links: #Foreach link
        tz_to_enum_map_string += filename_to_enum_entry(link.name, link.target) #add an entry to the filename map

    data_file_string = "".join([f'{str(char)}, ' for char in file_data])
    version_string = get_version_string(tzdb_path)
    cpp_string = compile_template_string(data_file_string, enum_entries_string, tz_to_enum_map_string, tz_to_file_info_map_string, version_string)
    write_CPP_file(cpp_string)

    print(f'Full file list is as follows: \n')
    print(files)
    print('\n')

    print(f'Additional links are as follows: \n')
    print([link.target for link in links])
    print('\n')

    print(f'Successfully found {len(files)} files with a resulting data size of {len(file_data)} bytes.\n')
    print(f'Output file written to {os.path.join(os.getcwd(), "embedded_data_file.cpp")}. \n')

def main() -> int:
    tzdb_path = get_tzdb_path_from_arguments()
    embed_compiled_TZDB(tzdb_path)
    return 0

if __name__ == '__main__':
    sys.exit(main())
sys.exit("This isn't intended to be run as a script.")
