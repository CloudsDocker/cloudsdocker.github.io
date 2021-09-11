---
title: google analysis
layout: posts
---

# How Page Value is calculated

## At a glance
Page Value is the average value for a page that a user visited before landing on the goal page or completing an Ecommerce transaction (or both). This value is intended to give you an idea of which page in your site contributed more to your site's revenue. If the page wasn't involved in an ecommerce transaction for your website in any way, then the Page Value for that page will be $0 since the page was never visited in a session where a transaction occurred.

Below is the equation you can follow to calculate Page Value. Please note that the unique pageview statistic represents the number of individual users who have loaded a given page per session. Each user is counted only once per session, no matter how many pages are opened by the same user.

Ecommerce Revenue + Total Goal Value
Number of Unique Pageviews for Given Page

## In depth

The first example above illustrates how Page Value works. Let's say you want to know the Page Value for Page B, and you know the following factors:

Goal page D: $10 (Remember, you assign the value of the Goal page when you first create a goal in the Analytics Settings page)
Receipt Page E: $100 (This page is where the user makes an ecommerce transaction of $100)
Unique pageview for Page B: One

You would then set up your Page Value equation like this:

Ecommerce Revenue ($100) + Total Goal Value ($10) 
Number of Unique Pageviews for Page B (1)

Page Value for Page B is $110 since a user visits Page B only once before the goal page during this session.


Now let's explore how Page Value for Page B is affected when we combine the data from two different sessions. You can see that Page B is viewed only once during Session 1, but during Session 2 it gets two pageviews (we're assuming the two pageviews are from the same user). The total Ecommerce revenue stays the same during both sessions. Although there were two unique pageviews, there was still only one Ecommerce transaction total for both sessions.

Goal page D: $10
Receipt Page E: $100
Unique pageview for Page B: Two

Your Page Value calculation should be adjusted to look like this:

Ecommerce Revenue ($100) + Total Goal Value ($10 x 2 sessions) 
Number of Unique Pageviews for Page B (2)

Page Value for Page B across two sessions is then $60, or $120 divided by two sessions.

# Code snippet about setting up GA in your site

```html
<script>
        window.ga=window.ga||function(){(ga.q=ga.q||[]).push(arguments)};ga.l=+new Date;
                ga('create', 'UA-xxxx-1', 'auto');

                        var hostName = window.location.host;
                                var ga_script = document.createElement('script');
                                        ga_script.setAttribute('async',true);
                                                if (['localhost:9000','test','uat'].some(function(hostItem){return hostName.indexOf(hostItem)>-1})) {
                                                                // non-production
                                                                            ga_script.setAttribute('src','https://www.google-analytics.com/analytics_debug.js');
                                                                                        window.ga_debug = {trace: true};
                                                                                                }else {
                                                                                                                ga_script.setAttribute('src','https://www.google-analytics.com/analytics.js');
                                                                                                                        }
                                                                                                                                document.head.appendChild(ga_script);
                                                                                                                                        ga('send', 'pageview');
                                                                                                                                            </script>
                                                                                                                                            ```

                                                                                                                                            ```javascript
                                                                                                                                            $rootScope.$on('$stateChangeSuccess', function() {
                                                                                                                                                                $window.ga('send', 'pageview', $location.path());
                                                                                                                                                                                $window.scrollTo(0, 0);
                                                                                                                                                                                            });
                                                                                                                                            ```


                                                                                                                                            Alternative async tracking snippet
                                                                                                                                            While the JavaScript tracking snippet described above ensures the script will be loaded and executed asynchronously on all browsers, it has the disadvantage of not allowing modern browsers to preload the script.
                                                                                                                                            The alternative async tracking snippet below adds support for preloading, which will provide a small performance boost on modern browsers, but can degrade to synchronous loading and execution on IE 9 and older mobile browsers that do not recognize the async script attribute. Only use this tracking snippet if your visitors primarily use modern
                                                                                                                                            browsers to access your site.

                                                                                                                                            <!-- Google Analytics -->
                                                                                                                                            <script>
                                                                                                                                            window.ga=window.ga||function(){(ga.q=ga.q||[]).push(arguments)};ga.l=+new Date;
                                                                                                                                            ga('create', 'UA-XXXXX-Y', 'auto');
                                                                                                                                            ga('send', 'pageview');
                                                                                                                                            </script>
                                                                                                                                            <script async src='https://www.google-analytics.com/analytics.js'></script>
                                                                                                                                            <!-- End Google Analytics -->

                                                                                                                                            From <https://developers.google.com/analytics/devguides/collection/analyticsjs/> 
                                                                                                                                            What data does the tracking snippet capture?
                                                                                                                                            When you add either of these tracking snippets to your website, you send a pageview for each page your users visit. Google Analytics processes this data and can infer a great deal of information including:
                                                                                                                                            • The total time a user spends on your site.
                                                                                                                                            • The time a user spends on each page and in what order those pages were visited.
                                                                                                                                            • What internal links were clicked (based on the URL of the next pageview).
                                                                                                                                            In addition, the IP address, user agent string, and initial page inspection analytics.js does when creating a new tracker is used to determine things like the following:
                                                                                                                                            • The geographic location of the user.
                                                                                                                                            • What browser and operating system are being used.
                                                                                                                                            • Screen size and whether Flash or Java is installed.
                                                                                                                                            • The referring site.

                                                                                                                                            From <https://developers.google.com/analytics/devguides/collection/analyticsjs/#alternative_async_tracking_snippet> 


                                                                                                                                            How analytics.js Works

                                                                                                                                            From <https://developers.google.com/analytics/devguides/collection/analyticsjs/how-analyticsjs-works> 

                                                                                                                                            The ga command queue
                                                                                                                                            The JavaScript tracking snippet defines a global ga function known as the "command queue". It's called the command queue because rather than executing the commands it receives immediately, it adds them to a queue that delays execution until the analytics.js library is fully loaded.
                                                                                                                                            In JavaScript, functions are also objects, which means they can contain properties. The tracking snippet defines a q property on the ga function object as an empty array. Prior to the analytics.js library being loaded, calling the ga() function appends the list of arguments passed to the ga()function to the end of the q array.
                                                                                                                                            For example, if you were to run the tracking snippet and then immediately log the contents of ga.qto the console, you'd see an array, two items in length, containing the two sets of arguments already passed to the ga() function:

                                                                                                                                            console.log(ga.q);

                                                                                                                                            // Outputs the following:
                                                                                                                                            // [
                                                                                                                                            //   ['create', 'UA-XXXXX-Y', 'auto'],
                                                                                                                                            //   ['send', 'pageview']
                                                                                                                                            // ]
                                                                                                                                            Once the analytics.js library is loaded, it inspects the contents of the ga.q array and executes each command in order. After that, the ga() function is redefined, so all subsequent calls execute immediately.
                                                                                                                                            This pattern allows developers to use the ga() command queue without having to worry about whether or not the analytics.js library has finished loading. It provides a simple, synchronous-looking interface that abstracts away most of the complexities of asynchronous code.

                                                                                                                                            From <https://developers.google.com/analytics/devguides/collection/analyticsjs/how-analyticsjs-works> 

                                                                                                                                            Adding commands to the queue
                                                                                                                                            All calls to the ga() command queue share a common signature. The first parameter, the "command", is a string that identifies a particular analytics.js method. Any additional parameters are the arguments that get passed to that method.
                                                                                                                                            The method a particular command refers to can be a global method, like create, a method on the ga object, or it can be an instance method on a tracker object, like send. If the ga() command queue receives a command it doesn't recognize, it simply ignores it, making calls to the ga()function very safe, as they will almost never result in an error.
                                                                                                                                            For a comprehensive list of all commands that can be executed via the command queue, see the ga() command queue reference.

                                                                                                                                            From <https://developers.google.com/analytics/devguides/collection/analyticsjs/how-analyticsjs-works> 

                                                                                                                                            Command parameters
                                                                                                                                            Most analytics.js commands (and their corresponding methods) accept parameters in a number of different formats. This is done as a convenience to make it easier to pass commonly used fields to certain methods.
                                                                                                                                            As an example, consider the two commands in the JavaScript tracking snippet:

                                                                                                                                            ga('create', 'UA-XXXXX-Y', 'auto');
                                                                                                                                            ga('send', 'pageview');
                                                                                                                                            In the first command, create accepts the fields trackingId, cookieDomain, and name to optionally be specified as the second, third, and fourth parameters, respectively. The sendcommand accepts an optional hitType second parameter.
                                                                                                                                            All commands accept a final fieldsObject parameter that can be used to specify any fields as well. For example, the above two commands in the tracking snippet could be rewritten as:

                                                                                                                                            ga('create', {
                                                                                                                                                  trackingId: 'UA-XXXXX-Y',
                                                                                                                                                    cookieDomain: 'auto'
                                                                                                                                            });
                                                                                                                                            ga('send', {
                                                                                                                                                  hitType: 'pageview'
                                                                                                                                            });
                                                                                                                                            See the ga() command queue reference for a comprehensive list of the optional parameters allowed for each of the commands.

                                                                                                                                            From <https://developers.google.com/analytics/devguides/collection/analyticsjs/how-analyticsjs-works> 


                                                                                                                                            Creating Trackers
                                                                                                                                            • Contents
                                                                                                                                            • The create method
                                                                                                                                            • Naming trackers
                                                                                                                                            • Specifying fields at creation time
                                                                                                                                            • Working with multiple trackers
                                                                                                                                            • Running commands for a specific tracker
                                                                                                                                            • Next steps
                                                                                                                                            Tracker objects (also known as "trackers") are objects that can collect and store data and then send that data to Google Analytics.
                                                                                                                                            When creating a new tracker, you must specify a tracking ID (which is the same as the property ID that corresponds to one of your Google Analytics properties) as well as a cookie domain, which specifies how cookies are stored. (The recommended value 'auto' specifies automatic cookie domain configuration.)
                                                                                                                                            If a cookie does not exist for the specified domain, a client ID is generated and stored in the cookie, and the user is identified as new. If a cookie exists containing a client ID value, that client ID is set on the tracker, and the user is identified as returning.
                                                                                                                                            Upon creation, tracker objects also gather information about the current browsing context such as the page title and URL, and information about the device such as screen resolution, viewport size, and document encoding. When it's time to send data to Google Analytics, all of the information currently stored on the tracker gets sent.

                                                                                                                                            From <https://developers.google.com/analytics/devguides/collection/analyticsjs/creating-trackers> 

                                                                                                                                            Running commands for a specific tracker
                                                                                                                                            To run analytics.js commands for a specific tracker, you prefix the command name with the tracker name, followed by a dot. When you don't specify a tracker name, the command is run on the default tracker.
                                                                                                                                            To send pageviews for the above two trackers, you'd run the following two commands:

                                                                                                                                            ga('send', 'pageview');
                                                                                                                                            ga('clientTracker.send', 'pageview');
                                                                                                                                            Future guides will go into more detail on the syntax for running specific commands. You can also refer to the command queue reference to see the full command syntax for all analytics.js commands.

                                                                                                                                            From <https://developers.google.com/analytics/devguides/collection/analyticsjs/creating-trackers> 

                                                                                                                                            Getting trackers via ga Object methods
                                                                                                                                            If you're not using a default tracker, or if you have more than one tracker on the page, you can access those trackers via one of the ga object methods.
                                                                                                                                            Once the analytics.js library is fully loaded, it adds additional methods to the ga object itself. Two of those methods, getByName and getAll, are used to access tracker objects.
                                                                                                                                            Note: ga object methods are only available when analytics.js has fully loaded, so you should only reference them inside a ready callback.
                                                                                                                                            getByName
                                                                                                                                            If you know the name of the tracker you want to access, you can do so using the getByNamemethod:

                                                                                                                                            ga('create', 'UA-XXXXX-Y', 'auto', 'myTracker');

                                                                                                                                            ga(function() {
                                                                                                                                                  // Logs the "myTracker" tracker object to the console.
                                                                                                                                                    console.log(ga.getByName('myTracker'));
                                                                                                                                            });

                                                                                                                                            From <https://developers.google.com/analytics/devguides/collection/analyticsjs/accessing-trackers> 

                                                                                                                                            The last line of the JavaScript tracking snippet adds a send command to the ga() command queue to send a pageview to Google Analytics:

                                                                                                                                            ga('create', 'UA-XXXXX-Y', 'auto');
                                                                                                                                            ga('send', 'pageview');
                                                                                                                                            The object that is doing the sending is the tracker that was scheduled for creation in the previous line of code, and the data that gets sent is the data stored on that tracker.
                                                                                                                                            This guide describes the various ways to send data to Google Analytics and explains how to control what data gets sent.

                                                                                                                                            From <https://developers.google.com/analytics/devguides/collection/analyticsjs/sending-hits> 

                                                                                                                                            Hits, hit types, and the Measurement Protocol
                                                                                                                                            When a tracker sends data to Google Analytics it's called sending a hit, and every hit must have a hit type. The JavaScript tracking snippet sends a hit of type pageview; other hit types include screenview, event, transaction, item, social, exception, and timing. This guide outlines the concepts and methods common to all hit types. Individual guides
                                                                                                                                            for each hit type can be found under the section Tracking common user interactions in the left-side navigation.
                                                                                                                                                The hit is an HTTP request, consisting of field and value pairs encoded as a query string, and sent to the Measurement Protocol.

                                                                                                                                                From <https://developers.google.com/analytics/devguides/collection/analyticsjs/sending-hits> 

                                                                                                                                                The simplest way to use the send command, that works for all hit types, is to pass all fields using the fieldsObjectparameter. For example:

                                                                                                                                                ga('send', {
                                                                                                                                                      hitType: 'event',
                                                                                                                                                        eventCategory: 'Video',
                                                                                                                                                          eventAction: 'play',
                                                                                                                                                            eventLabel: 'cats.mp4'
                                                                                                                                                });
                                                                                                                                                For convenience, certain hit types allow commonly used fields to be passed directly as arguments to the sendcommand. For example, the above send command for the "event" hit type could be rewritten as:

                                                                                                                                                ga('send', 'event', 'Video', 'play', 'cats.mp4');
                                                                                                                                                For a complete list of what fields can be passed as arguments for the various hit types, see the "parameters" section of the send method reference.


                                                                                                                                                From <https://developers.google.com/analytics/devguides/collection/analyticsjs/sending-hits> 

