import os
import json
import scrapy
import requests
import sqlite3

from scrapy.crawler import CrawlerProcess
src = '/home/rb025/PycharmProjects/Data/arxiv_crawler/output'

class LibgenSpider(scrapy.Spider):
    name = 'libgen'
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_urls = [f'https://libgen.rs/search.php?&req=topicid{204}&phrase=1&view=simple&column=def&sort=year&sortmode=DESC' for i in range(0,301)]
    def parse(self, response):

        for book in response.xpath('//tr/td[3]/a/@href').extract():
            if book.startswith('book/index.php'):
                url = 'https://libgen.rs/' + book
                yield scrapy.Request(url, callback=self.parse_page)
    def parse_page(self, response):
        conn = sqlite3.connect('downloaded_ids.db')
        cursor = conn.cursor()
        book_info = ('Title: ', 'Author(s):', 'Publisher:', 'City:', 'Year:', 'Language:', 'Pages (biblio\\tech):', 'ID:', 'Library:', 'Size:', 'Extension:', 'Topic:')
        total_infor = {}
        for path in response.xpath('//tr[@valign="top"]'):
            try:
                path_title = path.xpath('td[2]/nobr/font/text()').extract_first()
                path_info1 = path.xpath('td[1]/nobr/font/text()').extract_first()
                path_info2 = path.xpath('td[3]/nobr/font/text()').extract_first()
                if path_title in book_info or path_info1 in book_info or path_info2 in book_info:
                    if path_title == 'Title: ':
                        total_infor[path_title.split(':')[0]] = path.xpath('td[3]//a/text()').extract_first()
                        total_infor['Url'] = path.xpath('td[1]/a/@href').extract_first()

                    else:
                        if path_info1 == 'Author(s):':
                            infor = path.xpath('td[2]/b/text()').extract_first()
                            total_infor[path_info1.split(':')[0]] = infor
                        elif path_info1 != 'Author(s):' and path_info1 is not None:
                            infor = path.xpath('td[2]/text()').extract_first()
                            total_infor[path_info1.split(':')[0]] = infor
                        elif path_info2 is not None :
                            infor = path.xpath('td[4]/text()').extract_first()
                            total_infor[path_info2.split(':')[0]] = infor
                            if path_info2 == 'ID:':
                                cursor.execute('SELECT id FROM downloaded_ids WHERE id=?', (infor,))
                                result = cursor.fetchone()
                                if result:
                                    self.logger.info(f"ID {infor} has been downloaded before. Skipping...")
                                    break
                                cursor.execute('INSERT INTO downloaded_ids (id) VALUES (?)', (infor,))
                                conn.commit()
            except:
                print('pass')
            self.logger.info(total_infor)

            # Output dictionary chứa thông tin sách
            yield total_infor
        if int(total_infor['Language']) > 2020 and total_infor['Language'] == 'English':
            with open(f"/home/rb025/PycharmProjects/Data/arxiv_crawler/arxiv/output/{total_infor['ID']}.json", 'w', encoding='utf-8') as f:
                # Ghi dữ liệu JSON vào file
                json.dump(total_infor, f, ensure_ascii=False)
        conn.close()

    # Lấy link của trang tiếp theo (nếu có) và gọi hàm parse một lần nữa
    #     next_page = response.css('.next a::attr(href)').get()
    #     if next_page is not None:
    #         yield response.follow(next_page, self.parse)

crawler = CrawlerProcess()
crawler.crawl(LibgenSpider)
crawler.start()