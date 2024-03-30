import os
import sys
import json
import requests
from bs4 import BeautifulSoup
import logging

src = '/home/rb025/PycharmProjects/Data/crawler_data/arxiv'
proxies = {
            'http': 'socks5://127.0.0.1:7890'
        }
def crawl(url):
    # Get current date and previous day
    date_time = ['2401','2402','2403']
    for i in range(0,501,250):
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            for selector, catagory in zip (soup.find_all("ul")[1:9], soup.find_all("h2")[1:9]):
                catagory = catagory.get_text()
                for select in selector.find_all("li"):
                    page = select.find("a", href=True)['href']
                    if catagory == 'Computer Science':
                        for p in selector.select('li a'):
                                page = p['href']
                                if 'cs.' in page and 'recent' in page:
                                    date_cs = ['recent', 'new']
                                    for date in date_cs:
                                        page_url = url + page.replace('recent', date) + f'?skip={i}&show=250'
                                        parse_page(page_url, catagory)
                    else:
                        for date in date_time:
                            page_url = url + page.replace('archive', 'list') + '/' + date + f'?skip={i}&show=250'
                            parse_page(page_url, catagory)
def parse_page(page_url, catagory):
    os.makedirs(os.path.join(src, catagory), exist_ok=True)
    dst_folder = os.path.join(src, catagory)
    response = requests.get(page_url)
    meta = {}
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        for paper, subject in zip (soup.find_all("dt"), soup.find_all("dd")):
            if paper.find('a', title="Download PDF") is not None:
                paper_soup = BeautifulSoup(requests.get(page_url[:17] + paper.find('a', title="Abstract")['href']).content, 'html.parser')
                if response.status_code == 200:
                    doi = paper_soup.find_all('td')[9].find('a')['href']
                pdf_url = page_url[:17] + paper.find('a', title="Download PDF")['href']
                id = paper.find('a', title="Download PDF")['href'].split('/')[2]
                meta['Url'] = pdf_url
                meta['ID'] = id
                meta['Doi'] = doi
                meta['Title'] = subject.find('div', class_='list-title mathjax').get_text(strip=True)
                meta['Author(s)'] = subject.find('div', class_='list-authors').get_text(strip=True)
                meta['Subjects'] = subject.find('div', class_='list-subjects').get_text(strip=True)
                meta['Topic'] = catagory
                meta['Year'] = '2024'
                out = f"{dst_folder}/{meta['ID']}.pdf"
                download(pdf_url, proxies, out)
def download(url, proxies, out):
    """Download a url to out"""
    try:
        res = requests.get(url, stream=True, proxies=proxies)
        total_length = res.headers.get('content-length')

        with open(out, "wb") as f:
            if total_length is None:
                f.write(res.content)
            else:
                download_length = 0
                total_length = int(total_length)
                bar_width = 50
                for data in res.iter_content(chunk_size=4096):
                    download_length += len(data)
                    f.write(data)
                    done_width = int(bar_width * download_length / total_length)
                    perc = int(100 * download_length / total_length)
                    sys.stdout.write("\r%3d%% [%s%s] %s/%s"
                                     % (perc, '=' * done_width,
                                        ' ' * (bar_width - done_width),
                                        download_length, total_length))
                    sys.stdout.flush()
                sys.stdout.write('\n')
                sys.stdout.flush()
        _, filename = os.path.split(out)
        logging.info(f"↓ Successfully download the url to: {out}")

    except Exception as e:
        logging.info(f"↓ Fail download the url to: {out}")
        raise (f"Error occurs when downloading {e}")

if __name__ == '__main__':
    url = 'https://arxiv.org'
    crawl(url)
