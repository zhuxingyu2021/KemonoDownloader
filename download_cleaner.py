import os
import argparse
import re
import json
from datetime import datetime
import shutil

tmpfile_re = re.compile(r'.tmp$')
txt_json_re = re.compile(r'.txt$|.json$')

def clean_tmp(path):
    for root, _, files in os.walk(path):
        for file_name in files:
            if tmpfile_re.search(file_name) is not None:
                file_path = os.path.join(root, file_name)

                print("Delete file: %s" % file_path)
                os.remove(file_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Clean .tmp and expired files')
    parser.add_argument('dir', type=str, help='save dir')
    parser.add_argument('-t', '--time', type=str, help="expired time")

    args = parser.parse_args()
    dir_name = args.dir
    expired_time = datetime.strptime(args.time, "%Y-%m-%d-%H:%M:%S") if args.time is not None else None

    rm_dir_list = []
    rm_file_list = []
    for sub_dir_name in os.listdir(dir_name):
        sub_dir_path = os.path.join(dir_name, sub_dir_name)
        if os.path.isdir(sub_dir_path):
            clean_tmp(sub_dir_path)

            sub_dir_meta_path = os.path.join(sub_dir_path, "meta.json")
            if os.path.exists(sub_dir_meta_path):
                with open(sub_dir_meta_path, "r", encoding='utf-8') as read:
                    meta = json.load(read)

                if expired_time is not None:
                    file_time = datetime.strptime(meta['update time'], "%Y-%m-%d %H:%M:%S")
                    if file_time < expired_time:
                        rm_dir_list.append(sub_dir_path)

                all_file = meta['image resources'].keys() | meta['file resources'].keys() | meta['content resources'].keys()
                for file_name in os.listdir(sub_dir_path):
                    file_path = os.path.join(sub_dir_path, file_name)
                    if os.path.isfile(file_path):
                        if txt_json_re.search(file_name) is None:
                            if file_name not in all_file:
                                rm_file_list.append(file_path)

            else:
                rm_dir_list.append(sub_dir_path)


    if len(rm_dir_list) > 0 or len(rm_file_list) > 0:
        for rm_dir in rm_dir_list:
            print(rm_dir)

        for rm_file in rm_file_list:
            print(rm_file)

        print("Will remove all above dirs & files, continue? (Y/n)")
        if input().upper() == "Y":
            for rm_dir in rm_dir_list:
                shutil.rmtree(rm_dir)

            for rm_file in rm_file_list:
                os.remove(rm_file)
