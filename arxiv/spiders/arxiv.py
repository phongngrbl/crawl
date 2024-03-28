import os.path

import scrapy
from datetime import datetime, timedelta
import re
import time
from scrapy.loader import ItemLoader
from scrapy.http import FormRequest
from items import ArxivItem
import requests
from scrapy.crawler import CrawlerProcess

src = '/home/rb025/PycharmProjects/Data/arxiv_crawler/output'
class ArxivSpider(scrapy.Spider):
    name = "arxiv"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        

        self.base_url = 'https://arxiv.org'

        self.url = self.base_url
        self.start_urls = [self.url]
        self.tot_papers = 0
        self.date = ['2401','2402','2403']

    def parse(self, response):
        for selector in response.css("li"):
            page_id = selector.css("a::attr(id)").extract_first()
            if page_id is not None:
                page = selector.css("a::attr(href)").extract_first()
                catagory = selector.css("a::text").extract_first()
                if catagory == 'Computing Research Repository':
                    for p,c in zip (selector.css("li").css("a::attr(href)"), selector.css("a::text")):
                        catagory = c.root
                        page = p.root
                        if 'cs.' in page and 'recent' in page:
                            date_cs = ['recent', 'new']
                            for date in date_cs:
                                url = self.url + page.replace('recent',date)
                                yield scrapy.Request(url, callback=self.parse_page, meta={'catagory': catagory})
                else:
                    for date in self.date:
                        url = self.url + page.replace('archive','list') + '/' + date
                        yield scrapy.Request(url, callback=self.parse_page, meta={'catagory': catagory})

    def parse_page(self, response):
        catagory = response.meta.get('catagory')
        os.makedirs(os.path.join(src,catagory),exist_ok=True)
        dst_folder = os.path.join(src,catagory)
        for paper in response.css("dt"):
            pdf_paper = paper.css('a[title="Download PDF"]::attr(href)').extract_first()
            pdf_url = self.url + pdf_paper
            self.tot_papers += 1
            pdf_file = os.path.join(dst_folder, pdf_url.split('/')[-1])
            if not os.path.isfile(pdf_file):
                with open(pdf_file, 'wb') as f:
                    pdf_response = requests.get(pdf_url)
                    f.write(pdf_response.content)

crawler = CrawlerProcess()
crawler.crawl(ArxivSpider)
crawler.start()