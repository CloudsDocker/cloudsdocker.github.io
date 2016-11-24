## CV (Computer Vision)
最近在研究CV的一些开源库(OpenCV)，有一个体会就是在此领域，除了一些非常学术的_机器学习_, _深度学习_等概念外，其实还有一些很有趣的_现实的_应用场景。比如之前很流行的微软的 https://how-old.net, 你使用自己指定或者上传的照片进行面部识别_猜年龄_。 如下图所示：
![](http://upload-images.jianshu.io/upload_images/2380020-a20435eb05e69477.jpg?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

细想一下这个很吸引眼球的程序，其实技术本身打散了就包括两大块，一是从图片中扫描并进行面部识别，二是对找到的人脸根据算法去猜个年龄。大家可以猜猜实现第一个功能需要多少核心代码量？其实不用~~上万行~~，在这里我就使用短短**几行代码**（去除空格换行什么的，有效代码只要10行）就实现一个_高大上_面部识别的功能。在此文容我细述一下具体实现代码以及我对机器识别图像领域技术的理解。

### 面部识别,刷脸
 _人脸识别_技术大家应该都不陌生，之前大家使用的数码相机，或者现在很多手机自带的相机都有人脸识别的功能。其效果就像是下图这样。近的看，_剁手节_刚刚过了没有多久 , 背后的马老板一直在力推的刷脸支付也是一个此领域的所谓“黑科技”。比如在德国汉诺威电子展上，马云用支付宝“刷脸”买了一套纪念邮票。人脸识别应用市场也从爆发。随后，各大互联网巨头也纷纷推出了刷脸相关的应用。
 
![](http://cloudsdocker.github.io/images/iPhone-camera-face-recognition.jpg)

如果要加个定义，人脸识别又叫做人像识别、面部识别，是一种通过用摄像机或摄像头采集含有人脸的图像或视频流，并自动在图像中检测和跟踪人脸，进而对检测到的人脸进行脸部的一系列相关技术。

## 我的十行代码程序
 
OK，长话短说，先上 _干货_ ，下面就是此程序的_带注释_ 版本，完整的程序以及相关配套文件可以在 [这个github库](https://github.com/CloudsDocker/pyFacialRecognition) https://github.com/CloudsDocker/pyFacialRecognition 中找到，有兴趣可以_fork_ 下来玩玩。下面是整个程序的代码样子，后面我会逐行去解释分析。
 
![](http://upload-images.jianshu.io/upload_images/2380020-85da642858bdd76b.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)


就这短短的十行代码代码？seriously？“有图有真相”，我们先来看下运行的效果：

### 首先是原始的图片
![](http://upload-images.jianshu.io/upload_images/2380020-661f82b0ccce7339.jpg?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

### 运行程序后识别出面部并高亮显示的结果
请注意-K歌二人组- 的脸上的红色框框，这就是上面十行代码的成果。
![](http://upload-images.jianshu.io/upload_images/2380020-29ed06ac801b6462.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

## 代码解析
### 准备工作
因为此程序使用是的Python,因此你需要去安装Python。这里就不赘述了。除此之外，还需要安装 [OpenCV](http://opencv.org/downloads.html) (http://opencv.org/downloads.html)。
多说一句,这个 OpenCV正如其名，是一个开源的机器识别的深度学习框架。这是Intel（英特尔）实验室里的一个俄罗斯团队创造的，目前在开源社区非常的活跃。

特别提一下，对于Mac的用户，推荐使用brew去安装 （下面第一条语句可能会执行报错，我当时也是搞了好久。如果遇到第一条命令不过可以通过文尾的方式联系作者）
```sh
brew tap homebrew/science
brew install opencv
```

安装完成之后,在python的命令行中输入如下代码验证，如果没有报错就说明安装好了。
```sh
>>> import cv2
```

### 程序代码“庖丁解牛” 

```python
# -*- coding: utf-8 -*-
import cv2,sys
```
- 由于这里注释及窗口标题中使用了中文，因此加上utf-8字符集的支持
- 引入Opencv库以及Python的sys内建库，用于解析输入的图片参数


```python
inputImageFile=sys.argv[1]
```
- 在运行程序时将需要测试的照片文件名作为一个参数传进来


```python
faceClassifier=cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
```

- 加载OpenCV中自带预先培训好的人脸识别层级分类器 HAAR Casscade Classifier，这个会用来对我们输入的图片进行人脸判断。

这里有几个在深度学习及机器图像识别领域中的几个概念，稍微分析一下，至于深入的知识，大家可以自行搜索或者联系作者。

### Classifer 
在机器深度学习领域，针对识别不同物体都有不同的classifier,比如有的classifier来识别洗车，还有识别飞机的classifier，有classifier来识别照片中的笑容，眼睛等等。而我们这个例子是需要去做人脸识别，因此需要一个面部识别的classifier。

### 物体识别的原理
一般来说，比如想要机器学习着去识别“人脸”，就会使用大量的样本图片来事先培训，这些图片分为两大类，positive和negative的，也就是分为包“含有人脸”的图片和“不包含人脸”的图片，这样当使用程序去一张一张的分析这些图片，然后分析判断并对这些图片“分类” (classify),即合格的图片与不合格的图片，这也就其为什么叫做 _classifier_ ， 这样学习过程中积累的"知识"，比如一些判断时的到底临界值多少才能判断是positive还是negative什么的，都会存储在一个个XML文件中，这样使用这些前人经验（这里我们使用了 _哈尔_ 分类器）来对新的图片进行‘专家判断'分析，是否是人脸或者不是人脸。

### Cascade 
这里的 Cascade是 _层级分类器_ 的意思。为什么要 _分层_ 呢？刚才提到在进行机器分析照片时，其实是对整个图片从上到下，从左到右，一个像素一个像素的分析，这些分析又会涉及很多的 _特征分析_ ，比如对于人脸分析就包含识别眼睛，嘴巴等等，一般为了提高分析的准确度都需要有成千上万个特征，这样对于每个像素要进行成千上万的分析，对于整个图片都是百万甚至千万像素，这样总体的计算量会是个天文数字。但是，科学家很聪明，就想到分级的理念，即把这些特征分层，这样分层次去验证图片，如果前面层次的特征没有通过，对于这个图片就不用判断后面的特征了。这有点像是系统架构中的 _FF (Fail Fast)_,这样就提高了处理的速度与效率。


```python
objImage=cv2.imread(inputImageFile)
```
-  使用OpenCV库来加载我们传入的测试图片


```python
cvtImage=cv2.cvtColor(objImage,cv2.COLOR_BGR2GRAY)
```
- 首先将图片进行灰度化处理，以便于进行图片分析。这种方法在图像识别领域非常常见，比如在进行验证码的机器识别时就会先灰度化，去除不相关的背景噪音图像，然后再分析每个像素，以便抽取出真实的数据。不对针对此，你就看到非常多的验证码后面特意添加了很多的噪音点，线，就是为了防止这种程序来灰度化图片进行分析破解。

```python
foundFaces=faceClassifier.detectMultiScale(cvtImage,scaleFactor=1.3,minNeighbors=9,minSize=(50,50),flags = cv2.cv.CV_HAAR_SCALE_IMAGE)
```
- 执行detectMultiScale方法来识别物体，因为我们这里使用的是人脸的cascade classifier分类器，因此调用这个方法会来进行面部识别。后面这几个参数来设置进行识别时的配置，比如
 - scaleFactor: 因为在拍照，尤其现在很多都是自拍，这样照片中有的人脸大一些因为离镜头近，而有些离镜头远就会小一些，因为这个参数用于设置这个因素，如果你在使用不同的照片时如果人脸远近不同，就可以修改此参数，请注意此参数必须要大于1.0
 - minNeighbors: 因为在识别物体时是使用一个移动的小窗口来逐步判断的，这个参数就是决定是不是确定找到物体之前需要判断多少个周边的物体
 - minSize：刚才提到识别物体时是合作小窗口来逐步判断的，这个参数就是设置这个小窗口的大小



```python
print(" 在图片中找到了 {} 个人脸".format(len(foundFaces)))
```
- 显示出查找到多少张人脸，需要提到的识别物体的方法返回的一个找到的物体的位置信息的列表，因此使用 _len_ 来打印出找到了多少物体。

```python
for (x,y,w,h) in foundFaces:
    cv2.rectangle(objImage,(x,y),(x+w,y+h),(0,0,255),2)
```
- 遍历发现的“人脸”，需要说明的返回的是由4部分组成的位置数据，即这个“人脸”的横轴，纵轴坐标，宽度与高度。
- 然后使用 _OpenCV_ 提供的方法在原始图片上画出个矩形。其中 _(0,0,255)_ 是使用的颜色，这里使用的是R/G/B的颜色表示方法，比如 (0,0,0)表示黑色，(255,255,255)表示白色，有些网页编程经验的程序员应该不陌生。

```python
cv2.imshow(u'面部识别的结果已经高度框出来了。按任意键退出'.encode('gb2312'), objImage)
cv2.waitKey(0)
```
- 接下来是使用 _opencv_ 提供的imshow方法来显示这个图片，其中包括我们刚刚画的红色的识别的结果
- 最后一个语句是让用户按下键盘任意一个键来退出此图片显示窗口

# 总结
好了，上面是这个程序的详细解释以及相关的知识的讲解。其实这个只是个_抛砖引玉_的作用，还用非常多的应用场景，比如程序解析网页上的图片验证码，雅虎前几个月开源的 [NSFW](https://github.com/yahoo/open_nsfw), Not Suitable for Work (NSFW)，即判断那些不适合工作场所的图片，内容你懂的。 :-)

最后，再提一下，所有这些源代码及相关文件都开源在 https://github.com/CloudsDocker/pyFacialRecognition ，在fork并下载到本地后执行下面代码来测试运行
```sh
git clone https://github.com/CloudsDocker/pyFacialRecognition.git
cd pyFacialRecognition
./run.sh
```

如果有任何建议或者想法，请联系我。

## 联系我：
* phray.zhang@gmail.com (email/邮件，whatsapp, linkedin)
* helloworld_2000 (wechat/微信)
* 微博: cloudsdocker
* [github](https://github.com/CloudsDocker/)
* [简书 jianshu]（http://www.jianshu.com/users/a9e7b971aafc）
* 微信公众号：vibex

## Reference
- [OpenCV](http://docs.opencv.org/trunk/index.html)
- [HAAR 哈尔特征](https://zh.wikipedia.org/wiki/哈尔特征)

- [Face Detection using Haar Cascades](http://docs.opencv.org/trunk/d7/d8b/tutorial_py_face_detection.html)
- [NSFW](https://github.com/yahoo/open_nsfw)