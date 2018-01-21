"""
# 重賞レースの過去結果取得スクリプト

TARGET_URLにデータを取得したい重賞のURLを指定．
いずれはレースIDを引数で渡す形にしたい．

- アクセス先: netkeiba.com
"""

import scrapy
import sys, re

from netkeiba_scraper.items import RaceRecord

# idは重賞によって変わる #
TARGET_URL = 'http://race.netkeiba.com/?pid=special&id=0007'

class RaceTendencySpider(scrapy.Spider):

    name = 'race_tendency'
    allowed_domains = ['netkeiba.com']
    start_urls = [TARGET_URL]

    # まずこのメソッドが呼ばれる #
    def parse(self, response):
        # 過去レースのリンクURLを抽出し一つずつパース #
        for url in response.css('.race_table_old a::attr(href)').re(r'http://db.netkeiba.com/race.*'):
            yield scrapy.Request(url, self.parse_race_result)

    def parse_race_result(self, response):
        for (index, content) in enumerate(response.css('.race_table_01 tr')):
            # 1行目はヘッダー #
            if index == 0:
                continue

            # 項目毎データ取得 #
            item = RaceRecord()
            item['rank'] = content.css('td::text').extract()[0] # 着順
            item['horse_name'] = content.css('td a::text').extract()[0] # 馬名
            # text要素までcssメソッドで抜き出すと，各tdのtext有無でindexがずれてしまう #
            # td要素で抽出してからhtmlタグを取り除く #
            item['weight'] = self.remove_html_tag(content.css('td').extract()[14]) # 馬体重

            yield item

    def remove_html_tag(self, target):
        regexp = re.compile(r"<[^>]*?>")
        return regexp.sub("", target)
