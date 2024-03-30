import requests
from bs4 import BeautifulSoup

class SciencedirectSpider:
    def __init__(self):
        self.start_urls = ['https://www.sciencedirect.com/browse/journals-and-books?contentType=JL&contentType=BK&subject=mathematics&acceptsSubmissions=true']

    def parse(self):                                                    
        for start_url in self.start_urls:
            response = requests.get(start_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Crawl journals and books
                journal_links = soup.select(".JournalTitle")
                for journal_link in journal_links:
                    journal_url = journal_link['href']
                    yield from self.parse_journal(journal_url)

    def parse_journal(self, journal_url):
        response = requests.get(journal_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Crawl issues and volumes
            issue_links = soup.select(".volumeIssueText > a")
            for issue_link in issue_links:
                issue_url = issue_link['href']
                yield from self.parse_issue(issue_url)

    def parse_issue(self, issue_url):
        response = requests.get(issue_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Crawl articles
            article_links = soup.select(".anchor.article-content-title")
            for article_link in article_links:
                article_url = article_link['href']
                yield from self.parse_article(article_url)

    def parse_article(self, article_url):
        response = requests.get(article_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            item = {}
            item['title'] = ''.join(soup.select_one("#screen-reader-main-title .title-text").text)
            item['doi'] = soup.select_one("#doi-link a").get('href')
            item['journal'] = soup.select_one("#publication-title a").text
            vol = soup.select_one("#publication div:nth-of-type(2) div:nth-of-type(1) a").text
            suppl = soup.select_one("#publication div:nth-of-type(2) div.text-xs").text
            item['vol'] = vol + suppl
            item['abstract'] = soup.select_one(".abstract.author div p").text
            keywords = soup.select(".keyword span")
            item['keywords'] = '; '.join(keyword.text for keyword in keywords)
            item['base_url'] = response.url
            yield item

# Usage
spider = SciencedirectSpider()
for item in spider.parse():
    print(item)
