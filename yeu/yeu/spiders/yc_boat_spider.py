import scrapy
from ..items import YeuItem
from datetime import datetime

class YCBoatSpider(scrapy.Spider):
    name = "yc_boat"

    def __init__(self, date=None, *args, **kwargs):
        """"Redefining the __init__ scrapy spider builder to dynamically construct the url according to the month of reservation checked"""
        super().__init__(*args, **kwargs) # calling parent constructor as we are redefining le __init__ localement
        if date:
            try:
                parsed_input_date = datetime.strptime(date, "%d/%m/%Y")
            except ValueError:
                raise ValueError("[!] Input Date for yc_boat spider must be in DD/MM/YYYY format")
            self.start_urls = [f'https://resa3.yeu-continent.fr/passages.php?date_debut={date}&type=mois']
        else:
            raise ValueError("[!] You must provide a date argument to yc_boat spider in DD/MM/YYYY format")
    
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

