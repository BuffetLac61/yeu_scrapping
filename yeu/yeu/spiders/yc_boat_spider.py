import scrapy
from ..items import YeuItem

class YCBoatSpider(scrapy.Spider):
    name = "yc_boat"
    start_urls = [
        'https://resa3.yeu-continent.fr/passages.php?date_debut=01/09/2025&type=mois'
    ]

    def parse(self, response):

        title = response.css('title::text').extract()
        

        sem_lines = response.css("li.ligne.mois.semaine")
        sam_lines = response.css("li.ligne.mois.weekend.samedi")
        dim_lines = response.css("li.ligne.mois.weekend.dimanche")

        all_lines = sem_lines + sam_lines + dim_lines

        for line in all_lines :
            date = line.css("p.date::text").extract()
            horaires = line.css("a.horaire")
            for horaire in horaires :
                items = YeuItem()
                link = horaire.xpath("@href").extract()
                arrival = horaire.css('span').xpath('@title').extract()

                items['title_debug'] = title
                items['date'] = date
                items['horaire_link'] = link
                items['arrival'] = arrival

                yield items

