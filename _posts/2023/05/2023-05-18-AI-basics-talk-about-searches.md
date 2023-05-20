---
title: AI Basics: Talk About Searches
header:
    image: /assets/images/AI-basics-talk-about-searches.jpg
date: 2023-05-18
tags:
- AI
- Game theory

permalink: /blogs/tech/en/AI-basics-talk-about-searches
layout: single
category: tech
---
> "What you seek is seeking you." — Rumi



## UNINFORMED SEARCH STRATEGIES

This section covers several search strategies that come under the heading of uninformed search (also called blind search). 
The term means that the strategies have no additional information about states beyond that provided in the problem definition. 
All they can do is generate successors and distinguish a goal state from a non-goal state. 
All search strategies are distinguished by the order in which nodes are expanded. 
Strategies that know whether one non-goal state is "more promising" than another are called informed search or heuristic search strategies.

### Breadth-First Search hell
![img.png](/assets/images/ai_basics_talk_about_searches/img.png)


Two lessons can be learned from above Figure . 
 - First, the memory requirements are a bigger problem for breadth-first search than is the execution time. One might wait 13 days for the solution to an important problem with search depth 12, but no personal computer has the petabyte of memory it would take. Fortunately, other strategies require less memory.
 - The second lesson is that time is still a major factor. If your problem has a solution at depth 16, then (given our assumptions) it will take about 350 years for breadth-first search (or indeed any uninformed search) to find it. In general, exponential-complexity search problems cannot be solved by uninformed methods for any but the smallest instances.

--HTH--
