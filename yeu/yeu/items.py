# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

#test
class YeuItem(scrapy.Item):
    # Raw extrated fields
    title_debug = scrapy.Field()
    date = scrapy.Field()
    horaire_link = scrapy.Field()
    arrival = scrapy.Field()

    # Nouveau computed fields
    departure_time = scrapy.Field()
    arrival_time = scrapy.Field()
    nb_transfers = scrapy.Field()