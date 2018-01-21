# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import DropItem

class NetkeibaScraperPipeline(object):

    def process_item(self, item, spider):

        # 競走中止のデータを弾く #
        if item['rank'] == '中':
            raise DropItem('race exclusion data')

        return item
