# coding:utf8

"""
 Created by YR on 2017/4/1.

"""
import json
import re

import scrapy

from weibo.items import CommentItem


class WeiboSpider(scrapy.Spider):
    name = 'weibo'

    # allowed_domains = ['weibo.cn']
    # start_urls = ['http://weibo.cn']

    def __init__(self, name=None, **kwargs):
        super(WeiboSpider, self).__init__(name, **kwargs)
        self.loginUrl = 'https://passport.weibo.cn/sso/login'
        self.rootUrl = 'https://weibo.cn'
        self.headers = self.getHeaders()
        self.username = 'yourweibo'
        self.password = 'yourpassword'

    def parse(self, response):
        pass

    def getFormData(self):
        formData = {
            'username': self.username,
            'password': self.password,
            'savestate': '1',
            'ec': '0',
            'entry': 'mweibo',
            'mainpageflag': '1'
        }

        return formData

    @staticmethod
    def getHeaders():
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
                        (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36',
            'Host': 'passport.weibo.cn',
            'Origin': 'https://passport.weibo.cn',
            'Referer': 'https://passport.weibo.cn/signin/login',
        }

        return headers

    def start_requests(self):
        return [scrapy.FormRequest(
            self.loginUrl,
            formdata=self.getFormData(),
            headers=self.getHeaders(),
            meta={'cookiejar': 1},
            callback=self.checkLogin
        )]

    def checkLogin(self, response):
        loginJson = json.loads(response.text)
        # print json.dumps(loginJson, sort_keys=True, indent=4, separators=(',', ': '))
        if loginJson['retcode'] == 20000000:
            print "登录成功！"
            return self.afterLogin(response)
        else:
            raise ValueError("登录失败！")

    def afterLogin(self, response):
        findUrl = "https://weibo.cn/find/user"
        nickName = u"微博搞笑排行榜"
        # print nickName
        data1 = {"keyword": nickName,
                 "suser": "2"
                 }
        return scrapy.FormRequest(
            findUrl,
            formdata=data1,
            meta={'cookiejar': response.meta['cookiejar'],
                  'nickName': nickName},
            callback=self.findResult
        )

    def findResult(self, response):
        # print response.meta['nickName']
        if u'没有结果' in response.body:
            raise ValueError("没有找到 %s !" % response.meta['nickName'])
        else:
            print "找到 %s ！" % response.meta['nickName']
            url = response.xpath('//table[1]/tr/td[2]/a/@href')[0].extract()
            # print url
            return scrapy.Request(self.rootUrl + url,
                                  callback=self.personalPage,
                                  meta={'cookiejar': response.meta['cookiejar']
                                        },
                                  )

    def personalPage(self, response):
        infos = self.getPersonalInfo(response)
        indexBlog = 0
        # ktBlog 置顶微博；cmBlog 普通微博
        (ktBlog, cmBlog) = self.getBlogs(response)
        # print json.dumps(ktBlog, ensure_ascii=False, indent=2, separators=(',', ': '))
        # print json.dumps(cmBlog, ensure_ascii=False, indent=2, separators=(',', ': '))
        neededBlog = []
        if indexBlog == 0:
            neededBlog = ktBlog
        elif cmBlog:
            neededBlog = cmBlog[(indexBlog - 1) % 10]
        else:
            print "no blogs!!"
        print neededBlog["content"]

        # 默认评论总页数
        cmtPageMax = 2
        cmtPageNum = 1
        while cmtPageNum <= cmtPageMax:
            print u"%d/%d" % (cmtPageNum, cmtPageMax)
            # 评论的url
            cmtPageNum += 1
            commentUrl = "%s/comment/%s?uid=%s&page=%d" % (self.rootUrl, neededBlog["bID"], infos["uid"], cmtPageNum)
            yield scrapy.Request(commentUrl,
                                 callback=self.getCommentsOfOnePage,
                                 dont_filter=True,
                                 meta={'cookiejar': 1})

    def getPersonalInfo(self, response):
        # 根据需求，存储博主的部分信息
        print response.text
        infos = {}
        tmp = response.xpath("//div[@class='u']/div/a[2]/@href")[0].extract()
        uid = re.sub("/(\d+)/.+", "\\1", tmp)

        infos["fansList"] = "%s%s" % (self.rootUrl, tmp)  # 粉丝列表链接
        infos["fansNum"] = response.xpath("//body/div[3]/div/a[2]/text()")[0].extract()  # 粉丝数量
        infos["uid"] = uid  # 博主ID

        return infos

    @staticmethod
    def getBlogs(response):
        ktBlog = {
            'isKeeptop': True,
            "isTurn": False,
            'bID': "a",
            "content": 1,
            "attitude": -1,
            "repost": -1,
            "comment": -1,
            "time": 0,
            "from": "Home"
        }
        cmBlog = []

        blogs = response.xpath("//body/div[@class='c' and @id]")

        for blog in blogs:
            tmpBlog = {}
            blogInfo = blog.xpath(".//div[1]/span[@class='kt']")
            if blogInfo:
                ktBlog["content"] = blog.xpath(".//div[1]/span[@class='ctt']/text()")[0].extract()
                print blog.xpath('@id').extract()
                ktBlog["bID"] = re.sub('._(.+)', '\\1', blog.xpath('@id')[0].extract())
                print ktBlog["bID"]
                continue

            tmpBlog['content'] = blog.xpath(".//div/span[@class='ctt']").xpath('string(.)')[0] \
                .extract().replace('\n', '').replace(' ', '')

            tmpBlog["bID"] = re.sub('._(.+)', '\\1', blog.xpath('@id')[0].extract())
            cmBlog.append(tmpBlog)

        # print cmBlog
        #     exit()
        return (ktBlog, cmBlog)

    def getCommentsOfOnePage(self, response):
        print response.body
        pageStu = response.xpath(u"//body/div[@id='pagelist']/form/div")
        if pageStu:
            pageInfo = pageStu.xpath('string(.)')[0].extract().replace('\n', '') \
                .replace(' ', '').replace(' ', '')
            ma = re.match(u".+(\d+)/(\d+)页", pageInfo)
            cmtPageMax = ma.group(2)
        else:
            # self.printWarningLog(u"评论出现空页，找不到总页码信息！\n")
            raise ValueError("评论为空，找不到总页码信息！")

        comments = response.xpath("//body/div[@class='c']/span[@class='ctt']")
        item = CommentItem()

        for comment in comments:
            try:
                name = comment.xpath("../a[1]/text()")[0].extract()
                url = self.rootUrl + comment.xpath("../a[1]/@href")[0].extract()
                #             mainHtml = session.get(weiboRoot + name.attrib["href"])
                #             maininfo = parseMainPage(mainHtml.content)
                cont = comment.xpath("string(.)")[0].extract().replace("\n", ''). \
                    replace(' ', '')
                item['name'] = name
                item['url'] = url
                item['cont'] = cont
            except ValueError, e:
                print e
                continue

            yield item


if __name__ == '__main__':
    pass
