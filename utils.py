import os
import zipfile
from filesplit.split import Split


def split_csv(filename: str, split_size: int) -> None:

    #-Creating the split object-#
    split = Split(filename, os.getcwd())

    #-Splitting the file by size-#
    split.bysize(size = split_size, newline = True, includeheader = True)


def split_sql(filename: str, split_size: int) -> None:  

    #-Creating the split object-#
    split = Split(filename, os.getcwd())

    #-Splitting the file by size-#
    split.bysize(size = split_size, newline = True)


def zip_it(file_name: str, file_ext: str) -> None:

    try:

        #-Opening a file based on the gievn filename in write mode
        with zipfile.ZipFile(f"{file_name}.zip", 'w', zipfile.ZIP_DEFLATED, compresslevel = 9) as zipf:

            #-Writing the zip file-#
            zipf.write(file_name + file_ext)

    except Exception as e:

        #-Printing out the error-#
        print(f'Error zipping {file_name + file_ext}: {e}')