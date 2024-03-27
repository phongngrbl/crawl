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

    def __init__(self, search_query = "machine learning", field = 'all' , start = 0, \
                 date_from = '', date_to = '', filter_date = '', **kwargs):
        super().__init__(**kwargs)
        
        try:
            self.search_query_or = search_query
            if len(search_query.split(' '))>1:
                search_query = re.sub(' ', '+', search_query)
            self.search_query = '%22'+search_query+'%22'
        except NameError:
            raise ValueError('Please enter a valid search query.')
        
        if not date_from and not date_to:
            self.date_to = time.strftime('%Y-%m-%d')
            self.date_from = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            self.filter_date='all_dates'
        else:
            self.date_to = date_to
            self.date_from = date_from
            self.filter_date = 'date_range'
        
        self.start = start
        self.field = field
        
        self.base_url = 'https://arxiv.org'

        self.url = self.base_url
        self.start_urls = [self.url]
        self.tot_papers = 0
        self.date = ['2401','2402','2403']
        self.date_cs = ['new', 'recent']
        print('\n Url to scrape: \n %s \n ' %self.url)
        print('Date_from = %s \n ' %self.date_from)
        print('Date_to = %s \n ' %self.date_to)
        print('Filter_date = %s \n \n' %self.filter_date)

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


    def parse_abs_page(self, response):
        """
        From arXiv abstract page, fetches: 
        - submisison date and time
        - all categories including cross-references
        """
        
        new = ItemLoader(item=ArxivItem(), response=response, parent=response.meta['item']) 
        
        # all arXiv categories
        other_cat_full_cont = response.css('td[class*=subjects]').extract()[0].split('</span>;')
        if len(other_cat_full_cont)>1:
            other_cats = other_cat_full_cont[1]
            other_cats_list = [x.strip('\(').strip('\)') for x in re.findall('\(.*?\)', other_cats)]
        else: other_cats_list = []
            
        main_cat = re.findall('\(.*?\)', response.css('div.metatable span::text').extract()[0])[0].strip('\(').strip('\)')
        all_cats =[main_cat]+other_cats_list
        new.add_value('all_cat', all_cats)
        
        # submission date
        new.add_value('date', response.css('div.submission-history::text').extract()[-2])
        
        yield new.load_item()

crawler = CrawlerProcess()
crawler.crawl(ArxivSpider)
crawler.start()