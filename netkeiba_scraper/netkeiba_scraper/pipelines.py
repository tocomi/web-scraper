# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import DropItem

from netkeiba_scraper.spiders.race_tendency import RaceTendencySpider

class NetkeibaScraperPipeline(object):

    def process_item(self, item, spider):

        if isinstance(spider, RaceTendencySpider):
            # 競走中止のデータを弾く #
            if item['rank'] == '中' or item['rank'] == '取':
                raise DropItem('race exclusion data')

        return item
