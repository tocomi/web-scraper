# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy_splash import SplashRequest

from netkeiba_scraper.items import HorseData

class UmaajiCalculatorSpider(scrapy.Spider):

    name = 'umaaji_calculator'
    allowed_domains = [ 'race.netkeiba.com' ]
    base_url = 'https://race.netkeiba.com/'
    start_urls = [ base_url ]

    def start_requests(self):
        yield SplashRequest(self.start_urls[0], self.parse, args={ 'wait': 5.0 })

    def parse(self, response):
        # 本日のレース一覧からレース情報URLをパース #
        # FIXME: movieへのリンクを弾く
        for url in response.css('.RaceList_Box li a::attr(href)').re(r'race/.*race_id.*'):
            if 'movie.html' in url:
                continue
            # FIXME: Splashを使うと処理が止まってしまう
            # yield SplashRequest(self.make_url(url), self.parse_main, args={ 'wait': 1.0 })
            yield scrapy.Request(self.make_url(url), self.parse_main)

    def make_url(self, url):
        #    race/result.html?race_id=202006010704&rf=race_list #
        # -> https://race.netkeiba.com/race/shutuba_past.html?race_id=202006010704&rf=shutuba_submenu #
        if 'result.html' in url:
            html_replaced_url = re.sub('result', 'shutuba_past', url)
            return self.base_url + re.sub('race_list', 'shutuba_submenu', html_replaced_url)
        
        #    http://race.netkeiba.com/?pid=race&id=c201805050801&mode=top #
        # -> http://race.netkeiba.com/?pid=race&id=c201805050801&mode=shutuba #
        return self.base_url + re.sub('mode=top', 'mode=shutuba', url)

    def parse_main(self, response):
        result = self.get_race_data(response)
        result['horses'] = []
        for (index, horse_html) in enumerate(response.css('.HorseList')):

            horse_data = self.get_horse_data(horse_html)
            if horse_data:
                result['horses'].append(horse_data)
        
        yield result

    """
    レース情報の取得
    """
    def get_race_data(self, response):
        racedata = response.css('.RaceList_NameBox')
        
        race_data = {}
        race_data['name'] = racedata.css('.RaceName::text').extract_first().strip()
        race_data['place'] = racedata.css('.RaceData02 span::text').extract()[1]
        race_data['round'] = self.get_round(racedata.css('.RaceNum::text').extract_first())

        regexp = re.compile("(芝|ダ)([0-9]{4})")
        match = regexp.search(racedata.css('.RaceData01 span::text').extract_first().strip())
        race_data['ground'] = match.group(1)
        race_data['distance'] = match.group(2)

        race_data['grade'] = self.parse_grade(self.get_race_grade(racedata))
        return race_data

    def get_place(self, text):
        regexp = re.compile("([0-9]{1,2}回)(.+?)[0-9]{1,2}日目")
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
        regexp = re.compile("([０-９]{3,4}|[１-３]勝|未勝利|新馬)")
        match = regexp.search(race_html.css('.RaceData02 span::text').extract()[4])
        if match:
            return match.group(1)

        regexp = re.compile("(1|2|3)")
        # Icon_GradeType3 #
        # -> 3 #
        match = regexp.search(race_html.css('.RaceName span::attr(class)').extract_first().split(' ')[1])
        if match:
            return 'G' + match.group(1)

        return ''

    """
    出走馬データの取得
    """
    def get_horse_data(self, horse):
        horse_data = {}
        name = horse.css('.Horse02 a::text').extract_first()

        # NOTE: 出馬表以外も取ってきてしまうのでここで弾く
        if not name:
            return {}

        horse_data['name'] = name.strip()

        horse_data['gate'] = horse.css('td::text').extract_first()
        horse_data['number'] = horse.css('.Waku::text').extract_first()

        age_sex = horse.css('.Barei::text').extract_first()
        regexp = re.compile("(牡|牝|セ)([0-9]{1,2})")
        match = regexp.search(age_sex)
        horse_data['sex'] = match.group(1)
        horse_data['age'] = match.group(2)

        handi = horse.css('.Jockey span')[1].css('::text').extract_first()
        horse_data['handi'] = handi.strip()

        # FIXME: オッズと人気順が非同期処理になっていて取得できない
        # odds = horse.css('.Popular span')[0].css('::text').extract_first()
        # horse_data['odds'] = odds.strip()

        # rank = horse.css('.txt_c::text').extract()[1]
        # regexp = re.compile("[0-9]{1,2}")
        # match = regexp.search(rank)
        # if match == None:
        #     horse_data['rank'] = ''
        # else:
        #     horse_data['rank'] = match.group(0)
        horse_data['odds'] = '0.0'
        horse_data['rank'] = '0'

        horse_data['jockey'] = horse.css('.Jockey a::text').extract_first()

        horse_data['past_races'] = self.get_past_races(horse.css('.Past, .Rest'))

        print(horse_data)
        return horse_data

    """
    過去出走データの取得
    """
    def get_past_races(self, past_race_html_list):
        past_races = []
        for past_race_html in past_race_html_list:
            past_race = {}

            name = past_race_html.css('.Data02 a::text').extract_first()
            if name == None:
                name = past_race_html.css('.Data01')[0].css('::text').extract_first()
            past_race['name'] = name.strip()
            
            past_race['grade'] = self.parse_grade(self.get_grade(past_race_html))

            date_place = self.get_date_place(past_race_html)
            past_race['place'] = date_place['place']
            past_race['date'] = date_place['date']

            condition = self.get_condition(past_race_html)
            past_race['ground'] = condition['ground']
            past_race['distance'] = condition['distance']
            past_race['time'] = condition['time']
            past_race['status'] = condition['status']

            past_race['diff'] = self.get_diff(past_race_html)

            jockey_handi = self.get_jockey_handi(past_race_html)
            past_race['jockey'] = jockey_handi['jockey']
            past_race['handi'] = jockey_handi['handi']
            
            past_races.append(past_race)
        
        return past_races
    
    def get_grade(self, past_race_html):
        grade = past_race_html.css('.Icon_GradeType::text').extract_first()
        if grade != None:
            return grade

        grade = past_race_html.css('.Data02 a::text').extract_first()
        if grade == None:
            return ''
        regexp = re.compile("([0-9]{3,4}|[1-3]勝|未勝利|新馬)")
        match = regexp.search(grade)
        return match.group(0) if match != None else ''

    replace_target = { '０': '0', '１': '1', '２': '2', '３': '3', '５': '5', '６': '6', '下': '' , 'ク': '', 'ラ': '', 'ス': ''}
    def parse_grade(self, grade):
        if grade == '':
            return grade

        if grade == 'GI':
            return 'G1'
        if grade == 'GII':
            return 'G2'
        if grade == 'GIII':
            return 'G3'

        for (before, after) in self.replace_target.items():
            grade = re.sub(before, after, grade)
        
        return grade

    def get_date_place(self, past_race_html):
        date_place = { 'date': '', 'place': '' }
        date_place_raw = past_race_html.css('.Data01 span::text').extract_first()
        if date_place_raw == None:
            return date_place
        
        date_place_array = date_place_raw.replace('\n', '').split('\xa0')
        if len(date_place_array) == 0:
            return date_place

        date_place['date'] = date_place_array[0]
        date_place['place'] = date_place_array[1]
        return date_place
    
    def get_condition(self, past_race_html):
        condition_raw = past_race_html.css('.Data05')
        return self.parse_condition(condition_raw)
    
    def parse_condition(self, condition_raw):
        condition = { 'ground': '', 'distance': '', 'time': '', 'status': '' }

        condition_text = condition_raw.css('::text').extract_first()
        if condition_text == None:
            return condition

        status_text = condition_raw.css('strong::text').extract_first()

        regexp = re.compile("(芝|ダ)([0-9]{3,4}).*([0-9]{1}:[0-9]{2}\.[0-9]{1})")
        match = regexp.search(condition_text)
        if match == None:
            return condition

        condition['ground'] = match.group(1)
        condition['distance'] = match.group(2)
        condition['time'] = match.group(3)
        condition['status'] = status_text
        return condition
    
    def get_diff(self, past_race_html):
        diff = past_race_html.css('.Data07::text').extract_first()
        return re.sub(r"(\(|\))", '', diff) if diff != None else diff
    
    def get_jockey_handi(self, past_race_html):
        jockey_handi = { 'jockey': '', 'handi': '' }
        jockey_handi_raw = past_race_html.css('.Data03::text').extract_first()
        if jockey_handi_raw == None:
            return jockey_handi

        jocket_handi_str = jockey_handi_raw.split('\xa0')[2].split(' ')

        jockey_handi['jockey'] = jocket_handi_str[1]
        jockey_handi['handi'] = jocket_handi_str[2]
        return jockey_handi
