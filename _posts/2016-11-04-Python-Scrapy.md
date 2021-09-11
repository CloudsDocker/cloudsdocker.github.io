---
layout: posts
title: Python Scraphy
tags:
- python
- scraphy
---

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




# Reference
- https://doc.scrapy.org/en/latest/intro/tutorial.html
- 
