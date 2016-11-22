---
layout: page
title: 用10几行代码自己写个人脸识别程序
tag:
- MachineLearning
- FacialRecognition
---
最近在研究CV的一些开源库，比如OpenCV等。发现其实除了其下的_机器学习_,_深度学习_外，还有一些很有趣的现实使用场景，比如这里就使用短短几行代码（去除空格换行什么的，有效代码只要12行）就可以实现一个平时看起来 _高大上_ 的面部识别功能。

 _人脸识别_技术大家应该都不陌生，远的看，之前大家使用的数码相机，或者现在很多手机自带的相机都有人脸识别的功能，就像是下图这样。近的年，大家刚刚过了 _剁手节_ , 背后的马老板一直在力推的刷脸支付也是一个应用场景。比如在德国汉诺威电子展上，马云用支付宝“刷脸”买了一套纪念邮票。人脸识别应用市场也从爆发。随后，各大互联网巨头也纷纷推出了刷脸相关的应用。
 
![](iPhone-camera-face-recognition.jpg)

 如果要加个定义，人脸识别又叫做人像识别、面部识别，是一种通过用摄像机或摄像头采集含有人脸的图像或视频流，并自动在图像中检测和跟踪人脸，进而对检测到的人脸进行脸部的一系列相关技术。

 OK，长话短说，先上 _干货_ ， 下面就是此程序的 _带注释_版本，完成程序以及相关配套文件可以在 [这个github库](https://github.com/CloudsDocker/pyFacialRecognition) https://github.com/CloudsDocker/pyFacialRecognition 中找到，有兴趣可以 _fork_ 下来玩玩。previ

```python
# -*- coding: utf-8 -*-
import cv2,sys

# 使用输入的测试照片的文件名
inputImageFile=sys.argv[1]

# 使用 HAAR 的机器学习积累的原始文件，这里此文件包括了人脸识别的“经验”
faceBase='haarcascade_frontalface_default.xml'

# 根据机器学习库文件创建一个 classifier
faceClassifier=cv2.CascadeClassifier(faceBase)

# 使用库 cv2 来加载图片
objImage=cv2.imread(inputImageFile)

# 首先将图片进行灰度化处理，以便于进行图片分析
cvtImage=cv2.cvtColor(objImage,cv2.COLOR_BGR2GRAY)

# 执行detectMultiScale方法来识别物体，我们这里使用的是人脸的数据，因此用于面部识别
foundFaces=faceClassifier.detectMultiScale(cvtImage,scaleFactor=1.3,minNeighbors=9,minSize=(50,50),flags = cv2.cv.CV_HAAR_SCALE_IMAGE)

print(" 在图片中找到了 {} 个人脸".format(len(foundFaces)))

# 遍历发现的人脸
for (x,y,w,h) in foundFaces:
    cv2.rectangle(objImage,(x,y),(x+w,y+h),(0,0,255),2)

#显示这个图片识别的结果
cv2.imshow(u'面部识别的结果已经高度框出来了。按任意键退出'.encode('gb2312'), objImage)
cv2.waitKey(0)
```

Facial Recognition

# 深入浅出区块链系统：第一章.
`what you should know about blockchain`如果有任何建议或者想法，请联系我。

## 联系我：
* phray.zhang@gmail.com (email/邮件，whatsapp, linkedin)
* helloworld_2000 (wechat/微信)
* [github](https://github.com/CloudsDocker/)
* [简书 jianshu]（http://www.jianshu.com/users/a9e7b971aafc）
* 微信公众号：vibex
* 微博: cloudsdocker
