# Python Scraphy

'https://www.seek.com.au/jobs-in-information-communication-technology?highpay=True&salaryrange=150000-999999&salarytype=annual'

scrapy shell httxxxx
scrapy extrac 
>>> response.css('title::text').re(r'Quotes.*')
['Quotes to Scrape']

>>> response.css('title::text')[0].extract()
'Quotes to Scrape'

>>> response.xpath('//title')


view(response)



如果有任何建议或者想法，请联系我。

## 联系我：
* phray.zhang@gmail.com (email/邮件，whatsapp, linkedin)
* helloworld_2000 (wechat/微信)
* [github](https://github.com/CloudsDocker/)
* [简书 jianshu]（http://www.jianshu.com/users/a9e7b971aafc）
* 微信公众号：vibex
* 微博: cloudsdocker


# Reference
- https://doc.scrapy.org/en/latest/intro/tutorial.html
- 