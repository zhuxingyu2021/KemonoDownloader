import argparse
import os
import re

tmpfile_re = re.compile(r'.tmp$')

def clean(path):
    for root, _, files in os.walk(path):
        for file_name in files:
            if tmpfile_re.search(file_name) is not None:
                file_path = os.path.join(root, file_name)

                print("Delete file: %s" % file_path)
                os.remove(file_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Unzip all zip files in a directory")
    parser.add_argument('dir', type=str, help='directory path')

    args = parser.parse_args()
    path = args.dir

    clean(path)