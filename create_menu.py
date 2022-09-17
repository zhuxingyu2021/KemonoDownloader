from meta_data import MetaData
import argparse
import os
import json
import multiprocessing

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download metadata you-know-what from kemono.party')
    parser.add_argument('id', type=int, help="Illustrator user id")
    parser.add_argument('dir', type=str, help='save dir')
    parser.add_argument('-p', '--proxy', type=str, help="proxy ip:port")
    parser.add_argument('-i', '--iplatform', type=str, help="Illustrator platform", default="fanbox")
    parser.add_argument('-n', '--n_threads', help="Thread num", default=multiprocessing.cpu_count())

    args = parser.parse_args()
    userid = args.id
    save_dir = args.dir
    proxy = args.proxy
    platform = args.iplatform
    num_threads = int(args.n_threads)

    url = "https://kemono.party/%s/user/%d" % (platform, userid)
    if proxy is not None:
        proxies = {
            'http': proxy,
            'https': proxy
        }
    else:
        proxies = None

    os.makedirs(save_dir, exist_ok=True)

    result = MetaData(url, save_dir, num_threads, proxies).receive()
    result['url'] = url
    result['platform'] = platform
    with open(os.path.join(save_dir, "meta.json"), "w", encoding='utf-8') as write:
        json.dump(result, write, ensure_ascii=False, indent=4)
