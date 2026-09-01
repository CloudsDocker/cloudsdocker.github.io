# deep dive NR and FNR in linux awk command

## Scene 1: Title Card (3 seconds)

[INTRO MUSIC - upbeat tech theme]

Welcome to this tech deep dive: **deep dive NR and FNR in linux awk command**



---

## Scene 2-N: Content Breakdown


## Scene 2: deep dive NR awk command

[TRANSITION - slide]

**deep dive NR awk command**


## Scene 3: Mastering `awk` and `NR`: Unlocking the Power of Line Processing in Linux

[TRANSITION - slide]

**Mastering `awk` and `NR`: Unlocking the Power of Line Processing in Linux**


In the world of Linux system administration and Site Reliability Engineering (SRE), efficient text processing is essential. One of the most powerful tools for this is `awk`, and at the heart of its capabilities is the `NR` variable. This guide explores how to leverage `NR` for advanced text processing, log analysis, and automation.

[PAUSE - 1 second]


## Scene 5: Understanding `NR` in `awk`

[TRANSITION - slide]

**Understanding `NR` in `awk`**


`NR` (Number of Records) is a built-in `awk` variable that represents the **current line number** being processed. It starts at `1` and increments with each new line of input.

[PAUSE - 1 second]


## Scene 7: **Basic Usage of `NR`**

[TRANSITION - slide]

****Basic Usage of `NR`****


To print each line along with its line number:

[PAUSE - 1 second]


```
awk '{print NR, $0}' file.txt
```

[CODE HIGHLIGHT ANIMATION]



---

## Scene Final: Outro (3 seconds)

[OUTRO MUSIC - fade out]

Thanks for watching! Subscribe for more tech deep dives.

[END]
