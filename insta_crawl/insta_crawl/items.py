# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class InstaCrawlItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    link = scrapy.Field()
    page = scrapy.Field()
    content = scrapy.Field()
    title = scrapy.Field()
    id = scrapy.Field()
    shortcode = scrapy.Field()
    display_url = scrapy.Field()
    caption = scrapy.Field()
    loc_id = scrapy.Field()
    loc_lat = scrapy.Field()
    loc_lon = scrapy.Field()
    loc_name = scrapy.Field()
    owner_id = scrapy.Field()
    owner_name = scrapy.Field()
    taken_at_timestamp = scrapy.Field()
    pass