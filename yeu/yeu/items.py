# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class YeuItem(scrapy.Item):
    title_debug = scrapy.Field()
    date = scrapy.Field()
    horaire_link = scrapy.Field()
    arrival = scrapy.Field()
    pass
