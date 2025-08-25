import scrapy

class YCBoatSpider(scrapy.Spider):
    name = "yc_boat"
    start_urls = [
        'https://resa3.yeu-continent.fr/passages.php?date_debut=01/09/2025&type=mois'
    ]

    def parse(self, response):
        title = response.css('title::text').extract()
        yield {'title_debug' : title}