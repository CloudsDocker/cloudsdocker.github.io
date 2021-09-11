---
layout: posts
title: A Facial Recognition utility in a dozen of LOC
tags:
- DeepLearning
- MachineLearning
- FacialRecognition
- Python
- Face Recongnition
date: 2020-06-28 06:40:12
---

# A Facial Recognition utility in a dozen of python LOC (Lines Of Code)

## CV (Computer Vision)
I have been soak myself in open sourced libraries, such as OpenCV. I gradually came to discern concepts such as _Machine Learning_ , _Deep Learning_ are not academic standing water. As a matter of fact, those elusive topics and certain pragmatic use cases could coalesce in a amount of interesting products. For instance, in past couple of months, there were a hype of _guess-ages-by-photo_, below screenshot depicts such.

![](http://cloudsdocker.github.io/images/facial_howold.jpg)

What a seductive one! Initially been attracted by such funky features, after second thoughts, I found at the heart of it is two cohesive parts, the first one is how to locate _human faces_ from background and whole picture, consequently to have a ballpark _age_ guess for the recognized the faces. You may guess how difficult to codify a program to implement the 1st feature. Actually no need chunks of code, at here purely a dozen of lines of code are necessitated (actually only 10 lines of code, excluding space line and comments). I'd like to piggyback on such tiny utility to elaborate advanced topics of Computer Visions.

### Faces recognition
Actually _face recognition_ is not new to us, this feature prevailing in so-called _auto focus_ in DC (Digital Camera) and many main stream smart phone built-in cameras. Just like below photo. You can get a sense of how _commonplace_ of face recognition , which is becoming a widely used technology around us.

![](http://cloudsdocker.github.io/images/iPhone-camera-face-recognition.jpg)

Theoretically speaking, face recognition is also called _face detection_, it's a type of technology/program to electronically identify human frontal faces in digital images, such as photos, camera or surveillance. Further more, face detection is kind of objects detection in computer vision area. Which will locate object (e.g. human face) and get the size.

## My '10 LOC program'
First of all, let's have some visual and concrete feeling of this program, below screenshot is the source code.

![](http://cloudsdocker.github.io/images/facial_code_preview.png)

The whole program source code can be found at  [this github repository](https://github.com/CloudsDocker/pyFacialRecognition) https://github.com/CloudsDocker/pyFacialRecognition . Please feel free to _fork_ , check it out and have a try. I'll walk through this program one line by one line at this blog.

"You serious? This is all the problem, just aforementioned 10 lines?" Let's first take a look at the actual run output.

### Here is the origional image
![](http://cloudsdocker.github.io/images/facial_oriImage.jpg)

### Below is the result of execution of this tiny utility
Please be advised the red rectangle around faces.
![](http://cloudsdocker.github.io/images/facial_postProcessImage_en.png)


## Souce Code
### Prerequite
First of first, as you know, this program is composed by **python**,therefore, make sure you work station or laptop equiped with python, vesrion is irrelavant for this program.

In addition, this utility is built upon [OpenCV](http://opencv.org/downloads.html) (http://opencv.org/downloads.html), therefore please install this component as well. Just as its name suggested, it is an open source framework focus on computer vision related deep learning, surfaced decades ago. This is one Intel lab built by Rusian, which is a very active community.

Particulary, if you are Mac users, it's recommended to use *brew* to setup OpenCV. Below is sample commands(The 1st line of following command may raise some errors, in that case please contact me via the link at the rear of this blog):
```sh
brew tap homebrew/science
brew install opencv
```

Upon completion of preceding scripts, you can execute following scripts to verify whether it's installed success or not, e.g. it means all fine if no exception/errors raised
```sh
>>> import cv2
```

### Souce Code Dissection
Let's dissect file **recognizeFace_loose_en.py** as one example

```python
import cv2,sys
```
- To import library of OpenCV and python built-in system library, which is used to parse input arguments.

```python
inputImageFile=sys.argv[1]
```
- To read the **1st** argument, which to be the file name of the image to be parsed, e.g. _test.jpg_

```python
faceClassifier=cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
```

- To load HAAR Casscade Classifier, the human face recognition cascade categorizer which shipped with OpenCV. Which will do the _actual_ computation, logic to recognize and size human faces from any given images.


### Expansion of computer vision knowledge
We stop here not reading further code, avoiding perplex you, I'll walk through certain CV topics pertaining to this blog. As for more deep concepts, please feel free to contact me or goole by yourself.

#### Classifier
In arena of computer vision and machine learning, a variaty of classifiers been and being built, to assemle special _domain_ knowledge to recognize corresponding objects. For example, there are particular **classifier** to recognize cars, there are _plane_ classifier, and classifiers to recognize smile, eyes, etc. For our case, we need a specific classifier help us to detect and locate human faces.

#### Conceps of objects recognize
Generally speaking，, to recognize one object (such as human faces) means finding and identifying objects in an image or video sequence. However, it's neccessitate tons of sample/specimen to **train** machine to learn, for instance, it's likely thousands of hundreds of digital images/video will be prepared as learning material, while all of specimen should be categorized to two mutax type,  _positive_ or _negative_. e.g. phots containss *human face* and ones **without** *human face*. When machine read one photo, it was told this is either a positive one or negative one, then machine could gradually analysys and induce some **common facets** and persist to files for future usages, e.g. when given a new photo, the machine can **classify** it whether it's a positive or negative. That's why it's called **_classifier_**.

#### Cascade
Your feeling is right, just as it's name suggrested, cascade implies propagating something. In this case, it's specifically means **Cascade classifier**. Intuitively the next question is *why* cascade is required? Let me try to articulate the underlying logic, as you know, at the heart of digital images, which is the raw material of computer vision, are pixel。For one CV process, it need to scan each pixel per pixel, while in contemporary world, size of image tend to incresing more than we expected, e.g. normall one photo taken by smart phone tend to contains millions of pixels. At the meanwhile, to fine tune and get a more accuate result of one object recognition, it tend to lots of *classifiers* to work from different point of views of the underlying photo. Therefore these two factors interwhirled together, the final number would be astronomical. Therefore, one innovative solution is *cascade*, in a nutshell, all classifiers will be splited to multiple layers, one photo will be examined by classifiers on 1st layer at the very begining, if failed, the whole CV can retain **_negative_** immediately, with fewest efforts and time cost, while majority of other classifiers won't be executed in actual. This should significantely accelerate the whole process of CV. This is similar to **_FF(Fail Fast)_** in other areas,severed for sake of running efficiency.


```python
objImage=cv2.imread(inputImageFile)
```
-  To create one OpenCV image object by loading the input digital file via OpenCV


```python
cvtImage=cv2.cvtColor(objImage,cv2.COLOR_BGR2GRAY)
```
- Firstly, convert the digital colorful image to grayscale one, which easy the task to scan and analyse the image. Actually this is quite common in image analys area. e.g. this could eliminate those *noisy* pixel from the picture.

```python
foundFaces=faceClassifier.detectMultiScale(cvtImage,scaleFactor=1.3,minNeighbors=9,minSize=(50,50),flags = cv2.cv.CV_HAAR_SCALE_IMAGE)
```
- Call method **detectMultiScale** to recongnize object, i.e. human face in this case. The parameters overview as below:
 - scaleFactor: For a photo, particualy from selpie, some faces are shows bigger than rest of others, due to the distance between each faces and lens. Therefore this parameter is used to config the factor, please be advised this _double_ should greater than 1.0
 - minNeighbors: Because it need to gradually scan the photo by a certain _window_, i.e. a rectangle. So this parameter is telling how many other object in the vacinity to be detected, before making final decision that it's positive or negative.
 - minSize：For aforementioend _window_, this parameter is setting the size of this rectangle.

```python
print(" Found {} human faces in this image".format(len(foundFaces)))
```
- To print how many faces detected, be reminded returned value is a list, each item is the actual position of every faces. Therefore, using  _len_  to print total number of ojects found.

```python
for (x,y,w,h) in foundFaces:
    cv2.rectangle(objImage,(x,y),(x+w,y+h),(0,0,255),2)
```
- Traverese all faces detected, please be noted returning object is consist of 4 parts, i.e. the horizontal and vertial position, width and height.
- Consequently to draw a rectangle by an off-the-shelf method from _OpenCV_. Be advised _(0,0,255)_ represents color of the rectangel. It use R/G/B mode, e.g. black is (0,0,0)，white is (255,255,255)，etc. Well versed web programmer should be familiar with it.

```python
cv2.imshow('Detected human faces highlighted. Press any key to exit. ', objImage)
cv2.waitKey(0)
```
- To display this image via _opencv_ provided method imshow, together with the rectangles we draw previously
- The last one is one user hint, remind you can quit the applicaiton by press any key on the image display window

# In summary
We've skimmed source codes and pertaining knowledge. This is just scratched the surface of this framework, hope this can open the door to more advanced topics and insights, such as hack of CAPTCHA, newly open sourced project form Yahoo, [NSFW](https://github.com/yahoo/open_nsfw), Not Suitable for Work (NSFW)，to detect images with pornagraphy, etc.

Finally，please be reminded all related source are open sourced at github repository https://github.com/CloudsDocker/pyFacialRecognition ，please fork and sync to your local disk, check it out and paly it.
```sh
git clone https://github.com/CloudsDocker/pyFacialRecognition.git
cd pyFacialRecognition
./run.sh
```

You can access [my blog](http://cloudsdocker.github.io/2016/12/11/2016-11-22-Facial-Recognition_en/). Any comments/suggestions, feel free to contact me.

## Contact me：
* phray.zhang@gmail.com (email，whatsapp, linkedin)
* helloworld_2000 (wechat)
* weibo: cloudsdocker
* [github](https://github.com/CloudsDocker/)
* [jianshu](http://www.jianshu.com/users/a9e7b971aafc)
* wechat：vibex

## Reference
- [Object recognition](https://www.mathworks.com/discovery/object-recognition.html)
- [OpenCV](http://docs.opencv.org/trunk/index.html)
- [HAAR features](https://en.wikipedia.org/wiki/Haar-like_features)
- [Face Detection using Haar Cascades](http://docs.opencv.org/trunk/d7/d8b/tutorial_py_face_detection.html)
- [NSFW](https://github.com/yahoo/open_nsfw)
