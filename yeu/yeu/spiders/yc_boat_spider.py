import scrapy

class YCBoatSpider(scrapy.Spider):
    name = "yc_boat"
    start_urls = [
        'https://resa3.yeu-continent.fr/passages.php?date_debut=01/09/2025&type=mois'
    ]

    def parse(self, response):
        title = response.css('title::text').extract()
        

        sem_line = response.css("li.ligne.mois.semaine")
        sam_line = response.css("li.ligne.mois.weekend.samedi")
        dim_line = response.css("li.ligne.mois.weekend.dimanche")

        sem_date = sem_line.css("p.date::text").extract()
        sam_date = sam_line.css("p.date::text").extract()
        dim_date = dim_line.css("p.date::text").extract()

        sem_line_horaire = sem_line.css("a.horaire")
        sam_line_horaire = sam_line.css("a.horaire")
        dim_line_horaire = dim_line.css("a.horaire")

        sem_line_horaire_link = sem_line_horaire.xpath("@href").extract()
        sam_line_horaire_link = sam_line_horaire.xpath("@href").extract()
        dim_line_horaire_link = dim_line_horaire.xpath("@href").extract()

        yield {
            'title_debug' : title,
            'sem_date': sem_date,
            'sem_line_horaire': sem_line_horaire_link,
            'sam_date': sam_date,
            'sam_line_horaire': sam_line_horaire_link,
            'dim_date': dim_date,
            'dim_line_horaire': dim_line_horaire_link
               }

