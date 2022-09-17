import argparse
import json
from multiprocessing import Pool
import multiprocessing
from termcolor import colored
import os
import wget
import time
import urllib
import traceback
import logging


def _wget_download(url, path):
    retry = True
    while retry:
        try:
            wget.download(url, path)
            retry = False
        except urllib.error.ContentTooShortError:
            print(colored('Download', 'red'), url, colored('failed, retrying...', 'red'))
            retry = True
        except Exception as e:
            logging.error(traceback.format_exc())
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download you-know-what from kemono.party with metadata')
    parser.add_argument('metadata_dir', type=str, help="Metadata file directory")
    parser.add_argument('-r', '--resource', type=str, help="""Download resource type""", default="cfi")
    parser.add_argument('-c', '--check_only', help="Check-only, not to download", action='store_true')
    parser.add_argument('-n', '--n_threads', help="Thread num", default=multiprocessing.cpu_count())

    args = parser.parse_args()
    meta_data_path = os.path.join(args.metadata_dir, 'meta.json')
    resource_type_str = args.resource
    check_only_mode = args.check_only
    threads_num = int(args.n_threads)

    download_content_resources = False
    download_file_resources = False
    download_image_resources = False
    if 'c' in resource_type_str:
        print('Will download content resources')
        download_content_resources = True

    if 'f' in resource_type_str:
        print('Will download file resources')
        download_file_resources = True

    if 'i' in resource_type_str:
        print('Will download image resources')
        download_image_resources = True

    if check_only_mode:
        print("Run in check-only mode")

    with open(meta_data_path, 'r', encoding='utf-8') as f:
        meta_data = json.load(f)

    download_lists = []
    for item in meta_data["details"]:
        if download_content_resources:
            for file, link in item["content resources"].items():
                file_path = os.path.join(item["dir name"], file)
                if not os.path.exists(file_path):
                    download_lists.append((link, file_path))

        if download_file_resources:
            for file, link in item["file resources"].items():
                file_path = os.path.join(item["dir name"], file)
                if not os.path.exists(file_path):
                    download_lists.append((link, file_path))

        if download_file_resources:
            for file, link in item["image resources"].items():
                file_path = os.path.join(item["dir name"], file)
                if not os.path.exists(file_path):
                    download_lists.append((link, file_path))

        with open(os.path.join(item["dir name"], 'meta.json'), 'w', encoding='utf-8') as f:
            json.dump({
                "title": item["title"],
                "time": item["time"],
                "link": item["link"],
                "update time": meta_data["update time"],
                "content resources": item["content resources"],
                "file resources": item["file resources"],
                "image resources": item["image resources"]
            }, f, ensure_ascii=False, indent=4)

    for link, file_path in download_lists:
        print(colored("Will download file:", "green"), file_path, colored(",from link:", "green"), link)

    if not check_only_mode:
        with Pool(threads_num) as p:
            for link, file_path in download_lists:
                print(colored("Downloading file:", "blue"), file_path, colored(",from link:", "blue"), link)
                p.apply_async(_wget_download, args=(link, file_path))
                while p._taskqueue.qsize() > threads_num:
                    time.sleep(1)

            p.close()
            p.join()
