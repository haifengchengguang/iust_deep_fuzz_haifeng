# -*- coding: utf-8 -*-
"""
File name: pdf_object_extractor_3.py
Created on Mon Jan  8 15:13:22 2018 (1396-10-16)
Last update on Mars 15, 2023

Changelog:
Version 3 bugs fixed
Version 2 of pdf_pdf_object_extractor.py
Version 2 new change set:
 - The code is now more portable

Version 1:
This file use to extract data object in (set of) PDF files.
We use `mutool` a subprogram of `mupdf` an open source pdf library, readers and tools.

"""

__author__ = 'Morteza Zakeri'
__version__ = '0.3.0'

import sys
import subprocess
import re
import os

# Set MUTOOL_PATH
MUTOOL_PATH = r'D:/afl/mupdf-1.21.0-windows/mutool.exe'

# Set PDF_DIR_PATH
PDF_DIR_PATH = r'C:/Users/Morteza/Desktop/pdf_test/under_test'


# change mutool_path to point the location of mupdf
def get_pdf_xref(pdf_file_path=None,
                 mutool_path=MUTOOL_PATH,
                 mutool_command='show -e',
                 mutool_object_number='xref'):
    """
    command line to get xref size
    :param pdf_file_path:
    :param mutool_path:
    :param mutool_command:
    :param mutool_object_number:
    :return:
    """

    cmd = f'"{mutool_path}" {mutool_command} "{pdf_file_path}" {mutool_object_number}'
    # cmd = 'D:\\afl\\mupdf-1.11-windows\\mutool.exe show -e  D:\\afl\\mupdf-1.11-windows\\input\\pdftc_100k_2708.pdf x'
    print(f'Executing {cmd}')

    returned_value_in_byte = subprocess.check_output(cmd, shell=True, )

    return_value_in_string = returned_value_in_byte.decode()  # The output is like:
    """ 
        xref
        0 1458
        00000: 0000000000 00000 f
    """
    # print command line output to see it in python console
    # print(return_value_in_string)

    start_index_string = ''
    end_index_string = ''
    index = 6
    while return_value_in_string[index].isdigit():
        start_index_string += return_value_in_string[index]
        index += 1
    index += 1  # passing the space
    while return_value_in_string[index].isdigit():
        end_index_string += return_value_in_string[index]
        index += 1

    start_index_integer = int(start_index_string)
    end_index_integer = int(end_index_string)
    print(start_index_integer, end_index_integer)
    return start_index_integer, end_index_integer


def get_pdf_object_numbers(pdf_file_path=None,
                           mutool_path=MUTOOL_PATH,
                           mutool_command='show -e',
                           mutool_object_number='xref'):
    cmd = f'"{mutool_path}" {mutool_command} "{pdf_file_path}" {mutool_object_number}'
    # cmd = 'D:\\afl\\mupdf-1.11-windows\\mutool.exe show -e  D:\\afl\\mupdf-1.11-windows\\input\\pdftc_100k_2708.pdf x'
    print(f'Executing {cmd}')

    result = subprocess.run(cmd,
                            # capture_output=True,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            returncode=result.returncode,
            cmd=result.args,
            stderr=result.stderr
        )

    objects_ids_available = []  # Include objects ids with flags`n` and `o` in the xref table
    if result.stdout:
        xref_table_string = result.stdout.decode('utf-8')
        # print(f"Command Result:\n{xref_table_string}")

        xref_table_list = xref_table_string.split('\r\n')
        # print(f'{xref_table_list}')

        start_and_end_object_number = re.findall(r'\d+', xref_table_list[1])
        start_index_integer = int(start_and_end_object_number[0])
        end_index_integer = int(start_and_end_object_number[1])
        # print(start_index_integer, end_index_integer)

        # return start_index_integer, end_index_integer

        for object_description in xref_table_list[2:-1]:

            object_id = int(object_description.split(':')[0])
            if 'n' in object_description.split(':')[1]:  # or 'o' in object_description.split(':')[1]:
                # print(object_description)
                objects_ids_available.append(object_id)
        print(len(objects_ids_available))
        return objects_ids_available
    else:
        return None


def get_pdf_object(pdf_file_path=None,
                   mutool_path=MUTOOL_PATH,
                   mutool_command='show -b -e',
                   mutool_object_number='x'):
    """
    Get a single object with id ' x'
    """

    cmd = f'"{mutool_path}" {mutool_command} "{pdf_file_path}" {mutool_object_number}'
    print(f'Executing {cmd}')

    # Execute the cmd command and return output of command e.g. pdf objects

    returned_value_in_byte = subprocess.check_output(cmd, shell=True)

    # Convert output to string
    return_value_in_string = returned_value_in_byte.decode()
    return return_value_in_string


def get_pdf_objects(pdf_file_path=None,
                    mutool_path=MUTOOL_PATH,
                    mutool_command='show -e',
                    mutool_object_number='x'):
    """
    Get all object with id 'x1, x2, x3, ..., xn'
    """

    cmd = f'"{mutool_path}" {mutool_command} "{pdf_file_path}" {mutool_object_number}'
    # cmd = 'D:\\afl\\mupdf-1.11-windows\\mutool.exe show -e  D:\\afl\\mupdf-1.11-windows\\input\\pdftc_100k_2708.pdf '
    # print(f'Executing {cmd}')

    # Execute the cmd command and return output of command e.g. pdf objects
    returned_value_in_byte = subprocess.check_output(cmd, shell=True)

    # Convert output to string
    return_value_in_string = returned_value_in_byte.decode()

    # Below we sanitize the output and just keep text in new_seq variable (4 total steps)
    new_seq = returned_value_in_byte

    # Can I use regexp for sanitize? It seems not yet!
    # return_value = re.sub(r'stream.*endstream', 'stream', return_value_in_string, flags=re.DOTALL)
    # print(return_value_in_string)

    # regexp to match all streams exist in sequence
    # regex = re.compile(r'stream\b(?:(?!endstream).)*\bendstream', flags=re.DOTALL)
    # match = regex.findall(return_value_in_string)

    # Step 1: Eliminate all binary stream within the data object body by using below loop instead of above regexp
    stream_start = 0
    # stream_end = 0
    # while return_value_in_string.find('endstream', stream_end+9) != -1:
    #     stream_start = return_value_in_string.find('stream', stream_end+9)
    #     new_seq += return_value_in_string[stream_end:stream_start+6]
    #     stream_end = return_value_in_string.find('endstream', stream_end+9)
    #   if(stream_start != -1 and stream_end != -1):
    #       for i in range(stream_start+6,stream_end):
    #           return_value_in_list.(i)
    #   print(stream_start, stream_end)
    # new_seq += return_value_in_string[stream_end:len(return_value_in_string)]

    # Step 2: Mark the places that exist a binary stream with keyword stream and put it in the final output
    # new_seq = new_seq.replace('streamendstream', 'stream')
    # print(new_seq)

    # Step 3: Eliminate all numbers before object using regexp (e.g '12 0 obj' ==> 'obj')
    # new_seq = re.sub(r'\d+ \d+ obj', b'obj', new_seq)
    # print(new_seq)

    # Step 4: We also eliminate all \r to reduce size of corpus (optional phase of elimination)
    new_seq = new_seq.replace(b'\r', b'')

    # Return final sequence include all pdf data objects in a single file (pdf_file_path)
    return new_seq


# Main program to call above functions
def main(argv):
    # Counter to keep total number of object that extract from a given directory
    total_extracted_object = 0

    # pdf_directory_path = r'D:/iust_pdf_corpus/corpus_garbage/all_00_10kb/'  # 'Dir 1 of IUST corpus' 0-10 kb / == \\
    # pdf_directory_path = 'D:/iust_pdf_corpus/corpus_garbage/drive_deh_10_100kb/'  # 'Dir 2 of IUST corpus' 10-100 kb
    # pdf_directory_path = 'D:/iust_pdf_corpus/corpus_garbage/drive_h_100_900kb/'  # 'Dir 3 of IUST corpus' 100-900 kb
    # pdf_directory_path = 'D:/iust_pdf_corpus/corpus_garbage/mozilla/'  # 'Dir 4 of IUST corpus' mozilla corpus
    pdf_directory_path = PDF_DIR_PATH
    object_directory_path = os.path.join(pdf_directory_path, 'extracted_objs')

    if not os.path.exists(object_directory_path):
        os.makedirs(object_directory_path)

    files = [f for f in os.listdir(pdf_directory_path) if
             os.path.isfile(os.path.join(pdf_directory_path, f)) and f.endswith(".pdf")]

    print(f'Extracting objects for {len(files)} PDF files:')
    for i, filename in enumerate(files):
        try:
            # Find minimum and maximum object id existed in the file `filename`
            # start_index_integer, end_index_integer = get_pdf_xref(os.path.join(pdf_directory_path, filename))
            objects_ids_n = get_pdf_object_numbers(os.path.join(pdf_directory_path, filename))
            if objects_ids_n is None:
                print(f'No object id with flag n is found for {filename}')
                continue

            # Convert list to sublist of ids
            seq_step = 500
            ids_subList = [objects_ids_n[n:n + seq_step] for n in range(0, len(objects_ids_n), seq_step)]

            object_seqs = []
            for obj_ids in ids_subList:
                # mutool_object_number += str(obj_id) + ' '
                object_seq1 = get_pdf_objects(pdf_file_path=os.path.join(pdf_directory_path, filename),
                                              mutool_object_number=' '.join(map(str, obj_ids)))
                object_seqs.append(object_seq1)

            filename_object = f'{filename}_{str(len(objects_ids_n))}_obj.txt'
            filename_object_path = os.path.join(object_directory_path, filename_object)

            with open(filename_object_path, 'wb') as new_file:
                new_file.writelines(object_seqs)

            total_extracted_object += len(objects_ids_n)
            print(f'{i}: Objects from "{filename}" successfully was extracted to "{filename_object}".')
        except Exception as e:
            print(f'{i}: Extraction from "{filename}" was failed.', file=sys.stderr)
            print(str(e), file=sys.stderr)
            # finally:

    print('total_extracted_object: %s' % total_extracted_object)


if __name__ == "__main__":
    main(sys.argv)
