# coding:utf8

"""
 Created by YR on 2017/5/1.

"""

if __name__ == '__main__':
    from scrapy import cmdline

    # cmdname参数是一个数组，所以要split
    cmdline.execute("scrapy crawl weibo".split())
