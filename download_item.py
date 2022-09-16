import time
import urllib.error

import requests
import wget
from bs4 import BeautifulSoup
import os
import re
import sys
import multiprocessing
from termcolor import colored

illegal_char_re_0 = re.compile(r'[\\/:*?"<>|]')
illegal_char_re_1 = re.compile(r'\.+\s*$')
split_re_0 = re.compile(r'Download\s*')

def bar_progress(current, total, width=80):
  progress_message = "Downloading: %d%% [%d / %d] bytes" % (current / total * 100, current, total)
  # Don't use print() as it will print in new line every time.
  sys.stdout.write("\r" + progress_message)
  sys.stdout.flush()

def _wget_download(url, path):
    retry = True
    while retry:
        try:
            wget.download(url, path)
            retry = False
        except urllib.error.ContentTooShortError:
            retry = True

class ItemDownloader:
    def __init__(self, title, url,  save_dir_parent, proxies, pool):
        self.save_dir = None
        self.title = title
        self.proxies = proxies
        self.url = url
        self.pool = pool

        page_req = requests.get(url, proxies=self.proxies)

        self.page_soup = BeautifulSoup(page_req.text, 'html.parser')

        self.time_str = self.page_soup.find('div', class_='post__published').text.strip()
        date = self.time_str.split(' ')[0]

        self.save_dir = os.path.join(save_dir_parent, date + ' ' + illegal_char_re_0.sub(' ', illegal_char_re_1.sub('', self.title))).strip()
        os.makedirs(self.save_dir, exist_ok=True)

    def download_link(self, url, file_name):
        extend_name = url.split('.')[-1]
        download_path = os.path.join(self.save_dir, file_name)

        if os.path.exists(download_path):
            print(colored('Link %s has already downloaded, file:%s ' % (url, file_name), 'yellow'))
            return

        print(colored('Downloading link: %s to %s' % (url, file_name), 'blue'))

        retry = True
        while retry:
            try:
                wget.download(url, download_path, bar=bar_progress)
                retry = False
            except urllib.error.ContentTooShortError:
                retry = True
                print(colored('\nDownloading link: %s to %s Failed, Retrying...' % (url, file_name), 'red'))

        print('')

    def download_link_in_pool(self, url, file_name):
        extend_name = url.split('.')[-1]
        download_path = os.path.join(self.save_dir, file_name)

        if os.path.exists(download_path):
            print(colored('Link %s has already downloaded, file:%s ' % (url, file_name), 'yellow'))
            return

        print(colored('Downloading link: %s to %s' % (url, file_name), 'blue'))
        self.pool.apply_async(_wget_download, args=(url, download_path))

        while self.pool._taskqueue.qsize() > multiprocessing.cpu_count():
            time.sleep(1)

    def download(self):
        print(colored('Downloading %s in url %s' % (self.title, self.url), 'cyan'))

        with open(os.path.join(self.save_dir, "content.txt"), 'w', encoding='utf-8') as f:
            f.write(self.time_str + '\n\n')

            content_soup = self.page_soup.find('div', class_='post__content')
            if content_soup is not None:
                f.write(content_soup.text)
                content_img_list = content_soup.find_all('img')
                if len(content_img_list) > 0:
                    seq_id = 0
                    for content_img in content_img_list:
                        link = content_img['src']
                        if link[0] == '/':
                            link = "https://kemono.party"+link
                        extend_name = link.split('.')[-1]
                        self.download_link_in_pool(link, 'Content_' + str(seq_id) + '.' + extend_name)
                        seq_id += 1

        attachment_soup = self.page_soup.find('ul', class_='post__attachments')
        if attachment_soup is not None:
            attachment_list = attachment_soup.find_all('a')
            args_list = []
            for attachment in attachment_list:
                file_name = split_re_0.split(attachment.text.strip())[-1]
                args_list.append(("https://kemono.party" + attachment['href'], file_name))

            for args in args_list:
                self.download_link(*args)

        files_soup = self.page_soup.find('div', class_='post__files')
        if files_soup is not None:
            files_list = files_soup.find_all('a')

            links = []
            for link_soup in files_list:
                links.append("https://kemono.party" + link_soup['href'])

            seq_id = 0
            for link in links:
                extend_name = link.split('.')[-1]
                self.download_link_in_pool(link, str(seq_id) + '.' + extend_name)
                seq_id += 1

        comment_list = self.page_soup.find_all('article', class_='comment')
        if len(comment_list) > 0:
            with open(os.path.join(self.save_dir, "comment.txt"), 'w', encoding='utf-8') as f:
                for comment_soup in comment_list:
                    user_name = comment_soup.header.a.text
                    comment_content = comment_soup.section.text.strip()
                    date_time = comment_soup.footer.text.strip()
                    f.write(user_name + ' ' + date_time + '\n')
                    f.write(comment_content + '\n\n')
