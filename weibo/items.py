# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class CommentItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # pageMax = scrapy.Field()
    name = scrapy.Field()#评论者的昵称
    url = scrapy.Field()#评论者微博的url
    cont = scrapy.Field()#评论内容
