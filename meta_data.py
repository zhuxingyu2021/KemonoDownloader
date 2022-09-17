from termcolor import colored
import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool
import multiprocessing
import re
import os
import common
import datetime

illegal_char_re_0 = re.compile(r'[\\/:*?"<>\|]')
illegal_char_re_1 = re.compile(r'(?:\.+\s*$|\.\.)')
split_re_0 = re.compile(r'Download\s*')


def parse_page(key, text, save_dir):
    save_dir = os.path.join(save_dir, grep_illegal_char(key)).strip()
    os.makedirs(save_dir, exist_ok=True)

    content_resources = {}
    file_resources = {}
    image_resources = {}

    page_soup = BeautifulSoup(text, 'html.parser')
    content_soup = page_soup.find('div', class_='post__content')
    if content_soup is not None:
        with open(os.path.join(save_dir, "content.txt"), 'w', encoding='utf-8') as f:
            f.write(content_soup.text.strip())
            content_img_list = content_soup.find_all('img')
            if len(content_img_list) > 0:
                seq_id = 0
                for content_img in content_img_list:
                    link = content_img['src']
                    if link[0] == '/':
                        link = "https://kemono.party" + link
                    extend_name = link.split('.')[-1]
                    content_resources['Content_' + str(seq_id) + '.' + extend_name] = link
                    seq_id += 1

    attachment_soup = page_soup.find('ul', class_='post__attachments')
    if attachment_soup is not None:
        attachment_list = attachment_soup.find_all('a')
        for attachment in attachment_list:
            file_name = split_re_0.split(attachment.text.strip())[-1]
            file_resources[file_name] = "https://kemono.party" + attachment['href']

    files_soup = page_soup.find('div', class_='post__files')
    if files_soup is not None:
        files_list = files_soup.find_all('a')

        seq_id = 0
        for link_soup in files_list:
            link = "https://kemono.party" + link_soup['href']
            extend_name = link.split('.')[-1]
            image_resources[str(seq_id) + '.' + extend_name] = link
            seq_id += 1

    comment_list = page_soup.find_all('article', class_='comment')
    if len(comment_list) > 0:
        with open(os.path.join(save_dir, "comment.txt"), 'w', encoding='utf-8') as f:
            for comment_soup in comment_list:
                user_id = comment_soup['id']
                user_name = comment_soup.header.find_all('a')[-1].text.strip()
                comment_reply_soup = comment_soup.find('div', class_='comment__reply')
                comment_reply = comment_reply_soup.a.text.strip() if comment_reply_soup is not None else None
                comment_message = comment_soup.find('p', class_='comment__message').text.strip()
                date_time = comment_soup.footer.text.strip()
                f.write(user_id + ' ' + user_name + ' ' + date_time + '\n')
                if comment_reply is not None:
                    f.write(comment_reply + '\n')
                f.write(comment_message + '\n\n')

    return key, save_dir, content_resources, file_resources, image_resources


def request_get_wrapper(args):
    key, url, save_dir, proxies = args
    retry = True
    while retry:
        try:
            req = requests.get(url, proxies=proxies)
            retry = False
        except:
            retry = True
    return parse_page(key, req.text, save_dir)


def grep_illegal_char(path):
    return illegal_char_re_0.sub(' ', illegal_char_re_1.sub('', path))


class MetaData:
    def __init__(self, url_first_page, save_dir, proxies):
        self.url_first_page = url_first_page
        self.save_dir = save_dir
        self.proxies = proxies
        self.page_soups = []

    def receive_page(self, url):
        req = requests.get(url, proxies=self.proxies)
        soup = BeautifulSoup(req.text, 'html.parser')
        self.page_soups.append(soup)

        paginator_soup = soup.find('div', class_='paginator')
        page_index = paginator_soup.find_all('li')
        next_page_soup = page_index[-1].find('a')
        if next_page_soup is not None:
            if next_page_soup['title'] == 'Next page':
                next_page_url = "https://kemono.party" + next_page_soup['href']
            else:
                raise "Html parse error!"
        else:
            next_page_url = None
        return next_page_url

    def receive(self):

        print("Analyzing metadata ...")
        print("Receiving pages ...")

        next_page = self.receive_page(self.url_first_page)
        while next_page is not None:
            next_page = self.receive_page(next_page)

        print("Receiving pages done")

        illustrator_name = self.page_soups[0].find('a', class_='user-header__profile').find('span',
                                                                                            itemprop='name').text.strip()

        self.item_map = {}
        for page_soup in self.page_soups:
            card_list = page_soup.find('div', class_='card-list__items')
            card_list_articles = card_list.find_all('article')
            for card_list_article in card_list_articles:
                ref = card_list_article.find('a')
                date_time = card_list_article.find('time')['datetime']
                title = ref.text.strip()
                key = date_time.split()[0] + ' ' + title
                name_id = 0
                while key in self.item_map.keys():
                    name_id += 1
                    key = date_time.split()[0] + "-%d " % name_id + title

                self.item_map[key] = (title, date_time, "https://kemono.party" + ref['href'])

        print("Receiving & Parsing card pages ...")
        results = None
        with Pool(multiprocessing.cpu_count()) as p:
            args = [(key, x[2], self.save_dir, self.proxies) for key, x in self.item_map.items()]
            results = p.map(request_get_wrapper, args)

        print("Receiving & Parsing card pages done")
        print("Analyzing metadata done")

        result_map = []
        for key, save_dir, content_resources, file_resources, image_resources in results:
            result_map.append({
                "title": self.item_map[key][0],
                "dir name": save_dir,
                "time": self.item_map[key][1],
                "link": self.item_map[key][2],
                "content resources": content_resources,
                "file resources": file_resources,
                "image resources": image_resources
            })
        result_map.reverse()

        return {
            "version": common.VERSION,
            "illustrator": illustrator_name,
            "update time": datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
            "details": result_map
        }
