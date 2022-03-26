---
header:
    image: /assets/images/hd_front_end.jpg
title:  Pearls in Front end development
date: 2022-03-19
tags:
 - FrontEnd
 - JavaScript
 - Programing
 
permalink: /blogs/tech/en/pearls_in_front_end_dev
layout: single
category: tech
---

> Be happy in front of people who don't like you, it kills them.




# CSS Style related

## NormalizeStyles
Normalize.css makes browsers render all elements more consistently and in line with modern standards. It precisely targets only the styles that need normalizing.

```JavaScript
import NormalizeStyles from './NormalizeStyles';

const App = () => (
  <Fragment>
    <NormalizeStyles />
    <BaseStyles />
    <Toast />
    <Routes />
  </Fragment>
);
```

## Lodash: Awesome helper library 

```JavaScript
import _ from "lodash";
if (!_.isEmpty(res)) {
 _.isEqual(current, next) ? current : next;

```

--End--



