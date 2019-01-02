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
        for url in response.css('.RaceList_Box dt a::attr(href)').re(r'/\?pid.*race.*'):
            yield scrapy.Request(self.make_url(url), self.parse_main)

    def make_url(self, url):
        #    http://race.netkeiba.com/?pid=race_old&id=c201805050801 #
        # -> http://race.netkeiba.com/?pid=race&id=c201805050801&mode=shutuba #
        if 'race_old' in url:
            return self.start_urls[0] + re.sub('race_old', 'race', url) + '&mode=shutuba'
        
        #    http://race.netkeiba.com/?pid=race&id=c201805050801&mode=top #
        # -> http://race.netkeiba.com/?pid=race&id=c201805050801&mode=shutuba #
        return self.start_urls[0] + re.sub('mode=top', 'mode=shutuba', url)

    def parse_main(self, response):
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
        race_data['name'] = racedata.css('h1::text').extract_first().strip()
        race_data['place'] = self.get_place(response.css('.race_otherdata p::text').extract_first())
        race_data['round'] = self.get_round(response.css('.racedata dt::text').extract_first())

        regexp = re.compile("(芝|ダ)([0-9]{4})")
        match = regexp.search(response.css('p::text').extract_first())
        race_data['ground'] = match.group(1)
        race_data['distance'] = match.group(2)

        race_data['grade'] = self.parse_grade(self.get_race_grade(response.css('.data_intro')))
        return race_data

    def get_place(self, text):
        regexp = re.compile("([0-9]{1,2}回)(.+)[0-9]{1,2}日目")
        match = regexp.search(text)
        if match:
            return match.group(2)
        return ''

    def get_round(self, text):
        regexp = re.compile("[0-9]{1,2}")
        match = regexp.search(text)
        if match:
            return match.group(0)
        return ''

    def get_race_grade(self, race_html):
        regexp = re.compile("([０-９]{3,4}|未勝利|新馬)")
        match = regexp.search(race_html.css('.racedata dd h1::text').extract_first())
        if match:
            return match.group(1)

        match = regexp.search(race_html.css('.race_otherdata p::text').extract_first())
        if match:
            return match.group(1)

        regexp = re.compile("(g1|g2|g3|op)")
        match = regexp.search(race_html.css('.racedata h1 img::attr(src)').extract_first())
        if match:
            return match.group(1).upper()

        return ''

    def get_horse_data(self, horse):
        horse_data = {}
        horse_data['name'] = horse.css('.h_name a::text').extract_first()

        horse_data['gate'] = horse.css('td')[0].css('span::text').extract_first()
        horse_data['number'] = horse.css('.umaban::text').extract_first()

        age_sex = horse.css('.txt_l')[1].css('::text').extract_first()
        regexp = re.compile("(牡|牝|セ)([0-9]{1,2})")
        match = regexp.search(age_sex)
        horse_data['sex'] = match.group(1)
        horse_data['age'] = match.group(2)

        handi = horse.css('.txt_l')[1].css('::text').extract()[1]
        horse_data['handi'] = handi.strip()

        odds = horse.css('.txt_c::text').extract_first()
        horse_data['odds'] = odds.strip()

        rank = horse.css('.txt_c::text').extract()[1]
        regexp = re.compile("[0-9]{1,2}")
        match = regexp.search(rank)
        horse_data['rank'] = match.group(0)

        horse_data['jockey'] = horse.css('.txt_l')[1].css('a::text').extract_first()

        past_races = []
        past_race_html_list = horse.css('.txt_l')[2:7]
        for past_race_html in past_race_html_list:
            past_race = {}

            past_race['name'] = past_race_html.css('.race_name a::text').extract_first()
            if past_race['name'] == None:
                past_race['name'] = past_race_html.css('.race_name::text').extract_first()
            
            past_race['grade'] = self.parse_grade(self.get_grade(past_race_html))

            condition = self.get_condition(past_race_html)
            past_race['ground'] = condition['ground']
            past_race['distance'] = condition['distance']
            past_race['time'] = condition['time']
            past_race['status'] = condition['status']

            past_race['diff'] = self.get_diff(past_race_html)

            past_races.append(past_race)

        horse_data['past_races'] = past_races

        return horse_data

    def get_grade(self, past_race_html):
        grade = past_race_html.css('.race_grade::text').extract_first()
        if grade != None:
            return grade

        grade = past_race_html.css('.race_name a::text').extract_first()
        if grade == None:
            return ''
        regexp = re.compile("([０-９]{3,4}|未勝利|新馬)")
        match = regexp.search(grade)
        return match.group(0) if match != None else ''

    replace_target = { '０': '0', '１': '1', '５': '5', '６': '6', '下': '' }
    def parse_grade(self, grade):
        if grade == '':
            return grade

        for (before, after) in self.replace_target.items():
            grade = re.sub(before, after, grade)
        
        return grade

    def get_condition(self, past_race_html):
        condition_raw = past_race_html.css('.racebox').extract_first()
        return self.parse_condition(condition_raw)
    
    def parse_condition(self, condition_raw):
        condition = { 'ground': '', 'distance': '', 'time': '', 'status': '' }
        if condition_raw == None:
            return condition

        regexp = re.compile("(芝|ダ)([0-9]{4})\xa0([0-9]{1}:[0-9]{2}.[0-9]{1})\xa0(良|稍|重|不)")
        match = regexp.search(condition_raw)
        if match == None:
            return condition

        condition['ground'] = match.group(1)
        condition['distance'] = match.group(2)
        condition['time'] = match.group(3)
        condition['status'] = match.group(4)
        return condition
    
    def get_diff(self, past_race_html):
        diff = past_race_html.css('.h_name_01::text').extract_first()
        return re.sub(r"(\(|\))", '', diff) if diff != None else diff
