---
title: 谷歌地图里面照片的评论和照片在华为手机里面显示不出来
header:
    image: /assets/images/HD_google_map_no_reviews_huawai.jpg
date: 2022-10-18
tags:
 - Google
 - Maps
 - Huawei
layout: posts
---
> 枝上柳棉吹又少, 天涯何处无芳草. --苏轼

# 简介

我发现我的华为HuaWei安卓手机的应用“ Google Maps”出现了一个奇怪的问题。那就是当您在Google地图中搜索某个地点（例如“中央公园”）时，理想情况下，此应用应该向您显示该公园的照片和评论列表。例如，某人可能发布了该公园的草坪或河流的照片，并添加了一些评论，例如位置便利，易于停车等。但是，我的Google Apps中没有任何内容。



# 故障排除和解决方案
为了解决这个问题，我用谷歌搜索了可能的解决方案，这是找到最符合的结果。
https://support.google.com/googleplay/answer/7431675?hl=zh_CN

简而言之，您应该在Google Play中更改“国家/地区”，因为某些国家/地区存在内容限制。因此，您可以将其更改为某些限制最少的国家/地区，例如我更改为“澳大利亚”。

不幸的是，此更改仍然无法正常工作。



## 终极解决方案

通过进一步深入Google Map设置，并检查日志，不幸的是还是没有解决。到了最后，我通过“卸载并从Google Play重新下载”来解决了这个问题。事实证明，我安装的Google地图来自非官方的Google Play，但来自Huawei华为应用商店。也就是说这是个**阉割版**的 Google Maps.

--End--
