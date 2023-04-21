import os
from typing import NamedTuple
import sys
class FileParsingInfo(NamedTuple):
    data: bytes
    output: str
    bytes_parsed: int

def get_tzif_path_from_arguments() -> str:
    if len(sys.argv) != 2 or sys.argv[1].lower() == "-h":
        sys.exit("Expected usage: Python export_annotated_tzif_file.py filePathToTzifFile")
    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
       sys.exit( f'Error, could not find TZIF file at: "{file_path}"')
    return file_path

def load_file_data(filename: str) -> bytes:
    with open(filename, "rb") as in_file:
        return in_file.read()
        
def readable_hex_dump(file: bytes) -> str:
    dump = file.hex(sep=" ")
    return '\n'.join(dump[i:i+24] + f' [{(i/3)}]'for i in range(0, len(dump), 24)) 

def annotate_bytes(file: FileParsingInfo, bytes_to_pop: int, annotation: str) -> FileParsingInfo:
    output = file.output + f'{file.data[0 : bytes_to_pop].hex(sep=" ")} [{file.bytes_parsed}] {annotation}\n'
    return FileParsingInfo(file.data[bytes_to_pop: len(file.data)], output, file.bytes_parsed + bytes_to_pop) 
    
def parse_and_annotate_null_terminated_string(file: FileParsingInfo, name: str) -> tuple([FileParsingInfo, str]):
    null_termination_index = file.data.find(0)
    string_val = file.data[0:null_termination_index+1].decode()
    return annotate_bytes(file, null_termination_index+1, f'{name}: {string_val}'), string_val


def twos_complement_of_int(value: int, sign_bit: int) -> int:
    if (value & (1 << (sign_bit - 1))) !=0:
        return value - (1 << sign_bit)
    return value

def parse_and_annotate_signed_int(file: FileParsingInfo, length: int, name: str) -> tuple([FileParsingInfo, int]):
    num = twos_complement_of_int(int.from_bytes(file.data[0:length], 'big'), length*8)
    return annotate_bytes(file, length, f'{name}: {num}'), num

def parse_and_annotate_unsigned_int(file: FileParsingInfo, length: int, name: str) -> tuple([FileParsingInfo, int]):
    num = int.from_bytes(file.data[0:length], 'big')
    return annotate_bytes(file, length, f'{name}: {num}'), num

def parse_tzif_header_and_body(file: FileParsingInfo, time_size: int) -> FileParsingInfo:
    if file.data.startswith('TZif'.encode()) == False:
        sys.exit("Error, TZIF header not found")
    file = annotate_bytes(file, 0, "Header: ")
    file = annotate_bytes(file, 5, file.data[0:5].decode())
    file = annotate_bytes(file, 15, "Reserved Bytes")
    
    file, isutcnt = parse_and_annotate_unsigned_int(file, 4, "isutcnt")
    file, isstdcnt = parse_and_annotate_unsigned_int(file, 4, "isstdcnt")
    file, leapcnt = parse_and_annotate_unsigned_int(file, 4, "leapcnt")
    file, timecnt = parse_and_annotate_unsigned_int(file, 4, "timecnt")
    file, typecnt = parse_and_annotate_unsigned_int(file, 4, "typecnt")
    file, charcnt = parse_and_annotate_unsigned_int(file, 4, "charcnt")
    file = annotate_bytes(file, 0, "Datablock: ")
    for x in range(timecnt):
        file,_ = parse_and_annotate_signed_int(file, time_size, f'Transition Epoch {x}')

    for x in range(timecnt):
        file,_ = parse_and_annotate_signed_int(file, 1, f'Transition Type {x}')

    for x in range(typecnt):
        file,_ = parse_and_annotate_signed_int(file, 4, f'Local Offset {x}')
        file,_ = parse_and_annotate_unsigned_int(file, 1, f'Is DST? {x}')
        file,_ = parse_and_annotate_unsigned_int(file, 1, f'Timezone Designator ID {x}')

    chars_read = 0
    index = 0
    while (chars_read < charcnt):
        file, tz_name = parse_and_annotate_null_terminated_string(file, f'Timezone Designation {index}')
        chars_read += len(tz_name)
        index+=1

    for x in range(leapcnt):
        file,_ = parse_and_annotate_signed_int(file, time_size, f'Leap Occurrence {x}')
        file,_ = parse_and_annotate_signed_int(file, 4, f'Leap Correction {x}')
        
    for x in range(isstdcnt):
        file,_ = parse_and_annotate_unsigned_int(file, 1, f'Standard Indicator {x}')

    for x in range(isutcnt):
        file,_ = parse_and_annotate_unsigned_int(file, 1, f'UTC Indicator {x}')
    return file

def parse_tzif_footer(file: FileParsingInfo) -> FileParsingInfo:
    footer_str = file.data[1:-1].decode()
    return annotate_bytes(file, len(file.data), f'Footer: {footer_str}')

def annotated_hex_dump(file: bytes) -> str:
    parsingInfo = FileParsingInfo(file, "", 0)
    parsingInfo = parse_tzif_header_and_body(parsingInfo, 4)
    parsingInfo = parse_tzif_header_and_body(parsingInfo, 8)
    parsingInfo = parse_tzif_footer(parsingInfo)
    return parsingInfo.output

def main() -> int:
    tzif_path = get_tzif_path_from_arguments()
    tzif_file = load_file_data(tzif_path)
    output_text =  f'Filename: "{tzif_path}" \nHex_dump: \n{readable_hex_dump(tzif_file)}\n\nAnnotated Dump: \n{annotated_hex_dump(tzif_file)}\n'
    print(output_text)
    return 0

if __name__ == '__main__':
    sys.exit(main())
sys.exit("This isn't intended to be run as a script.")
