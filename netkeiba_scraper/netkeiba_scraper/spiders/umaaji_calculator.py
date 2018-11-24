# -*- coding: utf-8 -*-
import scrapy
import re

from netkeiba_scraper.items import HorseData

class UmaajiCalculatorSpider(scrapy.Spider):

    name = 'umaaji_calculator'
    allowed_domains = ['race.netkeiba.com']
    start_urls = ['http://race.netkeiba.com/']

    def parse(self, response):
        # 本日のレース一覧からレース情報URLをパース #
        for url in response.css('.RaceList_Box dt a::attr(href)').re(r'/\?pid.*'):
            yield scrapy.Request(self.start_urls[0] + url, self.parse_race)

    def parse_race(self, response):
        # レース情報から馬柱へのリンクをパース #
        for url in response.css('.sub_menu a::attr(href)').re(r'/\?pid.*mode=shutuba'):
            yield scrapy.Request(self.start_urls[0] + url, self.parse_horse)


    def parse_horse(self, response):
        result = self.get_race_data(response)
        result['horses'] = []
        for (index, horse) in enumerate(response.css('#shutuba table tr')):
            # 1行目はヘッダー #
            if index == 0:
                continue

            horse_data = self.get_horse_data(horse)
            result['horses'].append(horse_data)
        
        yield result

    def get_race_data(self, response):
        racedata = response.css('.racedata dd')
        
        race_data = {}
        race_data['race_name'] = racedata.css('h1::text').extract_first()
        race_data['race_ground'] = response.css('p::text').extract_first()
        return race_data

    def get_horse_data(self, horse):
        horse_data = {}
        horse_data['horse_name'] = horse.css('.h_name a::text').extract_first()

        past_races = []
        past_race_html_list = horse.css('.txt_l')[2:7]
        for past_race_html in past_race_html_list:
            past_race = {}
            diff = past_race_html.css('.h_name_01::text').extract_first()
            past_race['diff'] = re.sub(r"(\(|\))", '', diff) if diff != None else diff
            past_races.append(past_race)

        horse_data['past_races'] = past_races

        return horse_data
