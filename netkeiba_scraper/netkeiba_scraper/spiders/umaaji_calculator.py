# -*- coding: utf-8 -*-
import scrapy

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
        print(response.css('.racedata dd h1::text').extract_first())
        for (index, horse) in enumerate(response.css('#shutuba table tr')):
            # 1行目はヘッダー #
            if index == 0:
                continue

            item = HorseData()
            item['horse_name'] = horse.css('.h_name a::text').extract_first()

            print(item)

            yield item
