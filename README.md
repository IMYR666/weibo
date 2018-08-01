#  抓取新浪微博评论  
爬取的是手机版的入口，由于微博不登录的话，只能看到部分微博，内容有限，所以如果要抓全量内容就得登录。另外，使用了scrapy框架，所以先简单记录一下整个框架的架构，大体分为：
引擎（engine），调度器（scheduler），爬虫(spider)，下载器(downloader)，管道(pipeline)，其中，引擎和爬虫、
下载器是可以通过中间件（middlewares）通讯。  

* 引擎（engine）：
  负责控制数据流在系统中所有组件中流动，并在相应动作发生时触发事件。
* 调度器（scheduler）：
调度器从引擎接受request并将它们入队，以便之后引擎请求它们时童工引擎。
* 下载器(downloader)：
负责获取页面数据并返回给引擎，然后提供给爬虫。
* 爬虫(spider)：
用户主要自定义的地方，主要是处理引擎给的下载数据。
* 管道(pipeline)：
引擎将爬虫传递的item传递给管道处理。典型的处理有数据清洗，验证及持久化等。
* 下载器中间件（downloadermiddlewares）：
是引擎和下载器中间的特定钩子，处理下载器传递给引擎的response。
* 爬虫中间件（spidermiddlewares）：
是引擎和爬虫中间特定的钩子，处理爬虫的输入（response）和输出（items和request）。   

**接下来具体到这个项目中展开说明：**  

首先是工程的目录结构：  
>│　scrapy.cfg  
>│　start.py  
>├─sources  
>│　　commentData.json  
>└─weibo  
>>>│　items.py  
>>>│　middlewares.py  
>>>│　pipelines.py  
>>>│　settings.py  
>>>│　\_\_init\_\_.py  
>>>└─spiders  
>>>>>>>　spider.py  
>>>>>>>　\_\_init\_\_.py   

* scrapy.cfg: 项目的配置文件
* start.py：启动爬虫的文件，里面调用了`cmdline`命令  
* sources:存放运行结果的目录  
  * commentData.json  保存评论相关信息的文件  
* weibo：存放整个项目可自定义编程Python文件的目录
  * items.py:  
    新创建的工程目录下有一个默认的items文件，我们可以更改或者新建一个或多个文件来定义自己需要的item.在创建完成后，
    就可以通过类似于词典（dictionary-like）的API和用语声明字段的简单语法。此项目中定义了`commentItem`类，item的具体含义如下：

    ```python
    class CommentItem(scrapy.Item):
      # define the fields for your item here like:
      # name = scrapy.Field()
      name = scrapy.Field()#评论者的昵称
      url = scrapy.Field()#评论者微博的url
      cont = scrapy.Field()#评论内容
    ```
 
  * middlewares.py:  中间件，目前没有涉及。
  * pipelines.py:    
    当spider成功收集到Item后，item将会被传递到Pipline中，pipeline的主要功能是：    
    验证爬取的数据  
    查重  
    将数据保存到数据库中  
    本项目只进行了将数据存储在json文件中的操作。 具体实现了`process_item`方法，如下：  

    ```python
        def process_item(self, item, spider):
          line = json.dumps(dict(item), ensure_ascii=False) + "\n"
          self.file.write(line)

          return item
    ```
  * settings.py:    
    项目的设置文件，主要功能是控制一些常用配置，此项目前的配置如下：  
    ```python
    BOT_NAME = 'weibo'  #爬虫唯一名称
    SPIDER_MODULES = ['weibo.spiders']
    NEWSPIDER_MODULE = 'weibo.spiders'
    ROBOTSTXT_OBEY = False #关闭robot协议
    ITEM_PIPELINES = { #启用pipline组件
                  'weibo.pipelines.WeiboPipeline': 300,#value是1-1000的一个数字，数字越小，优先级越高。
    }
    ```
  * spiders:    
    * spider.py:    
      Spider是整个架构中最定制化的一个部件, 负责把网页内容提取出来，而不同数据采集目标的内容结构不一样，
      几乎需要为每一类网页都做定制。此项目中由于涉及到了模拟登陆，需要`post`请求，所以复写了`start_requests`方法，如下：  
      
      ```python
        def start_requests(self):
          return [scrapy.FormRequest(
              self.loginUrl,
              formdata=self.getFormData(),
              headers=self.getHeaders(),
              meta={'cookiejar': 1},
              callback=self.checkLogin
          )]
      ```
    另外，由于需要持久化登陆，需要保持请求，所以在请求中使用`cookiejar`关键字传递cookie,它的value是一个数字，只要不重复即可，这里给的值为1。
 


