import requests
import argparse
import os
from bs4 import BeautifulSoup
from download_item import ItemDownloader
from termcolor import colored
from multiprocessing import Pool
import multiprocessing

def download(url, save_dir, proxies, pool):
    print(colored("Downloading page: %s" % url, "green"))

    first_page_req = requests.get(url, proxies=proxies)

    first_page_soup = BeautifulSoup(first_page_req.text, 'html.parser')
    paginator = first_page_soup.find('div', class_='paginator')
    page_index = paginator.find_all('li')
    next_page_soup = page_index[-1].find('a')
    if next_page_soup is not None:
        if next_page_soup['title'] == 'Next page':
            next_page_url = "https://kemono.party" + next_page_soup['href']
        else:
            raise "Html parse error!"
    else:
        next_page_url = None

    item_lists = []

    card_list = first_page_soup.find('div', class_='card-list__items')
    card_list_articles = card_list.find_all('article')
    for card_list_article in card_list_articles:
        ref = card_list_article.find('a')
        item_lists.append(("https://kemono.party" + ref['href'], ref.text.strip()))

    for item in item_lists:
        sub_url, title = item
        ItemDownloader(title, sub_url, save_dir, proxies, pool).download()

    if next_page_url is not None:
        download(next_page_url, save_dir, proxies, pool)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download you-know-what from kemono.party')
    parser.add_argument('id', type=int, help="Illustrator user id")
    parser.add_argument('dir', type=str, help='save dir')
    parser.add_argument('-p', '--proxy', type=str, help="proxy ip:port")
    parser.add_argument('-i', '--iplatform', type=str, help="Illustrator platform", default="fanbox")

    args = parser.parse_args()
    userid = args.id
    save_dir = args.dir
    proxy = args.proxy
    platform = args.iplatform

    url = "https://kemono.party/%s/user/%d" % (platform, userid)
    if proxy is not None:
        proxies = {
            'http': proxy,
            'https': proxy
        }
    else:
        proxies = None

    os.makedirs(save_dir, exist_ok=True)

    with Pool(multiprocessing.cpu_count()) as p:
        download(url, save_dir, proxies, p)
        p.close()
        p.join()
