import argparse
import os
import json
import re
import shutil

filter_re = re.compile(r'.*\.(?:jpe?g?|png|gif|bmp|webp|mp4)$')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dest', type=str, help='destination dir')
    parser.add_argument('source', nargs='+')

    args = parser.parse_args()
    dest = args.dest
    source_list = args.source

    os.makedirs(dest, exist_ok=True)

    for src_dir in source_list:
        print("Processing %s ..." % src_dir)

        with open(os.path.join(src_dir, 'meta.json'), 'r', encoding='utf-8') as read:
            meta = json.load(read)

        illu = meta['illustrator']
        os.makedirs(os.path.join(dest, illu), exist_ok=True)
        fid = 0
        for root, _, files in os.walk(src_dir):
            for file in files:
                if filter_re.match(file) is not None:
                    ext = file.split('.')[-1]
                    src_path = os.path.join(root, file)
                    dst_path = os.path.join(os.path.join(dest, illu), "%s_%s.%s" % (illu, str(fid).zfill(6), ext))
                    shutil.copyfile(src_path, dst_path)
                    fid += 1
                else:
                    print("Skip %s" % file)