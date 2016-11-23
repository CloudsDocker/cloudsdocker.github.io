---
layout: page
title: 用10几行代码自己写个人脸识别程序
tag:
- MachineLearning
- FacialRecognition
---
# CV (Computer Vision) 与面部识别
最近在研究CV的一些开源库(OpenCV)。发现其实除了一些非常学术的_机器学习_,_深度学习_外，还有一些很有趣的现实应用场景，比如之前在朋友圈很流行的使用自己的照片进行面部识别_猜年龄_。 这个看起来 很 _高大上_ 的面部识别功能，其实打散了就包括两大块，一是面部识别，二是根据算法去猜个年龄。大家可以猜猜实现第一个功能需要多少代码量？其实不用上万行，在这里就使用短短几行代码（去除空格换行什么的，有效代码只要10行）就可以实现一个面部识别的功能。

## 刷脸
 _人脸识别_技术大家应该都不陌生，远的看，之前大家使用的数码相机，或者现在很多手机自带的相机都有人脸识别的功能，就像是下图这样。近的年，大家刚刚过了 _剁手节_ , 背后的马老板一直在力推的刷脸支付也是一个应用场景。比如在德国汉诺威电子展上，马云用支付宝“刷脸”买了一套纪念邮票。人脸识别应用市场也从爆发。随后，各大互联网巨头也纷纷推出了刷脸相关的应用。
 
![](iPhone-camera-face-recognition.jpg)

 如果要加个定义，人脸识别又叫做人像识别、面部识别，是一种通过用摄像机或摄像头采集含有人脸的图像或视频流，并自动在图像中检测和跟踪人脸，进而对检测到的人脸进行脸部的一系列相关技术。

 # 我的解决方案
 
 OK，长话短说，先上 _干货_ ， 下面就是此程序的 _带注释_版本，完成程序以及相关配套文件可以在 [这个github库](https://github.com/CloudsDocker/pyFacialRecognition) https://github.com/CloudsDocker/pyFacialRecognition 中找到，有兴趣可以 _fork_ 下来玩玩。下面是整个程序的代码样子，后面我会逐行去解释分析。
 
![](facial_code_preview.png)


然后代码运行的效果如下：

## 首先是原始的图片
![](facial_oriImage.jpg)

## 运行程序后识别出面部并高度显示的结果
![](facial_postProcessImage.png)

# 代码解析
## 准备工作
因为此程序使用是的python,因此你需要去安装Python。这里就不赘述了。除此之外，需要安装 [OpenCV](http://opencv.org/downloads.html) (http://opencv.org/downloads.html),
特别提一下，对于Mac的用户，推荐使用brew去安装 （如果遇到第一条命令不过可以通过下面的方式联系作者）
```sh
brew tap homebrew/science
brew install opencv
```

安装好了,在python的命令行中输入如下代码验证，如果没有报错就说明安装好了。
```sh
>>> import cv2
```
## 程序代码 

```python
# -*- coding: utf-8 -*-
import cv2,sys
```
- 由于这里注释及显示使用了中文，因此加上utf-8字符集的支持
- 引入opencv库以及python的sys内建库，用于解析输入的图片参数


```python
inputImageFile=sys.argv[1]
```
- 使用输入的测试照片的文件名作为参数传进来


```python
faceClassifier=cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
```
- 使用 HAAR Casscade 机器学习积累的原始文件，这里此文件包括了人脸识别的“经验”，一般是在机器学习领域中对某些特定算法进行有针对性训练，比如使用positive和negative的大批量图片进行学习，这 些学习的结果存储下来就是这种文件，这样使用这些来对新的图片进行‘专家判断'分析。

```python
objImage=cv2.imread(inputImageFile)
```
-  使用OpenCV库来加载我们使用参数传入的图片


```python
cvtImage=cv2.cvtColor(objImage,cv2.COLOR_BGR2GRAY)
```
- 首先将图片进行灰度化处理，以便于进行图片分析。这种方法在图像识别领域非常常见，比如在进行验证码的机器识别时就会先灰度化，去除不相关的背景噪音图像，然后再分析每个像素，以便抽取出真实的数据。不对针对此，你就看到非常多的验证码后面特意添加了很多的噪音点，线，就是为了防止这种程序来灰度化图片进行分析破解。

```python
```

```python
```


```python
```


```python
```


```python





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
