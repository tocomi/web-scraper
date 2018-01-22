# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class RaceRecord(scrapy.Item):

    rank = scrapy.Field()
    horse_name = scrapy.Field()
    age = scrapy.Field()
    female = scrapy.Field()
    handi = scrapy.Field()
    weight = scrapy.Field()
