import os
import re
import json
import sqlite3
import requests
from bs4 import BeautifulSoup

# Function to crawl and parse the webpage
def crawl_page(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        for book in soup.select('tr > td:nth-child(3) > a[href^="book/index.php"]'):
            book_url = 'https://libgen.rs/' + book['href']
            parse_book(book_url)

# Function to parse book information
def parse_book(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        book_info = ('Title: ', 'Author(s):', 'Publisher:', 'City:', 'Year:', 'Language:', 'Pages (biblio\\tech):', 'ID:', 'Library:', 'Size:', 'Extension:', 'Topic:')
        total_infor = {}
        for row in soup.select('tr[valign="top"]'):
            try:
                path_title = row.select_one('td:nth-of-type(2) nobr font')
                path_info1 = row.select_one('td:nth-of-type(1) nobr font')
                path_info2 = row.select_one('td:nth-of-type(3) nobr font')
                if path_title is not None:
                    path_title = path_title.get_text()
                elif path_info1 is not None:
                    path_info1 = path_info1.get_text()
                elif path_info2 is not None:
                    path_info2 = path_info2.get_text()

                # Kiểm tra xem các thông tin có trong danh sách book_info không
                if path_title in book_info or path_info1 in book_info or path_info2 in book_info:
                    if path_title == 'Title: ':
                        total_infor[path_title.split(':')[0]] = row.select_one('td:nth-of-type(3) a').get_text(
                            strip=True)
                        total_infor['Url'] = row.select_one('td:nth-of-type(1) a')['href']
                    else:
                        if path_info1 == 'Author(s):':
                            infor = row.select_one('td:nth-of-type(2) b').get_text(strip=True)
                            total_infor[path_info1.split(':')[0]] = infor
                        elif path_info1 != 'Author(s):' and path_info1 is not None:
                            infor = row.select_one('td:nth-of-type(2)').get_text(strip=True)
                            total_infor[path_info1.split(':')[0]] = infor
                        elif path_info2 is not None:
                            infor = row.select_one('td:nth-of-type(4)').get_text(strip=True)
                            total_infor[path_info2.split(':')[0]] = infor

            except:
                print('pass')

        # Check if the book ID has been downloaded before
        if 'ID' in total_infor:
            conn = sqlite3.connect('downloaded_ids.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM downloaded_ids WHERE id=?', (total_infor['ID'],))
            result = cursor.fetchone()
            if result:
                print(f"ID {total_infor['ID']} has been downloaded before. Skipping...")
            else:
                # Check if the book meets the conditions and save it to JSON file
                year = check_year(total_infor['Year'])
                if int(year) > 2010 and total_infor['Language'] == 'English':
                    with open(f"/home/rb025/PycharmProjects/Data/arxiv_crawler/arxiv/output/{total_infor['ID']}.json",
                              'w', encoding='utf-8') as f:
                        json.dump(total_infor, f, ensure_ascii=False)
                cursor.execute('INSERT INTO downloaded_ids (id) VALUES (?)', (total_infor['ID'],))
                conn.commit()
            conn.close()
def check_year(year):
    if year.isdigit():
        return year
    else:
        year_match = re.search(r'\b\d{4}\b', year)
        if year_match:
            return year_match.group()
        else:
            return 1

if __name__ == '__main__':
    # Crawl multiple pages
    for i in range(0, 301):
        for j in range (1,10):
        # for _ in range (0,10):
            url = f'https://libgen.rs/search.php?&req=topicid{i}&phrase=1&view=simple&column=def&sort=year&sortmode=DESC&page={j}'
            crawl_page(url)
