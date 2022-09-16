import zipfile
import argparse
import os
import re

zipfile_re = re.compile(r'.zip$')

def unzip(path):
    for root, _, files in os.walk(path):
        for file_name in files:
            if zipfile_re.search(file_name) is not None:
                extract_name = zipfile_re.sub('', file_name)
                file_path = os.path.join(root, file_name)
                extract_path = os.path.join(root, extract_name)
                print("Unzip file: %s to %s" % (file_path, extract_path))

                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)

                print("Delete file: %s" % file_path)
                os.remove(file_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Unzip all zip files in a directory")
    parser.add_argument('dir', type=str, help='directory path')

    args = parser.parse_args()
    path = args.dir

    unzip(path)
