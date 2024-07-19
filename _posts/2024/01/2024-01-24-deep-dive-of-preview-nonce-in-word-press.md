---
title: Deep dive for word press preview nonce
header:
    image: /assets/images/Deep_dive_for_word_press_preview_nonce.jpg
date: 2024-01-24
tags:
- WordPress

permalink: /blogs/tech/en/Deep_dive_for_word_press_preview_nonce
layout: single
category: tech
---
> One must learn by doing the thing; for though you think you know it, you have no certainty, until you try. —Sophocles

# Deep dive for word press preview nonce


## What is nonce

In the context of WordPress or web development in general, a nonce (Number Used Once) is a security token that is used to protect against certain types of attacks, such as Cross-Site Request Forgery (CSRF).

A nonce is typically a random or unique value that is generated for each request and included in the form or URL parameters. The server checks the validity of the nonce when processing the request, ensuring that the request is legitimate and not a result of malicious activity.

In WordPress, nonces are often used to protect against CSRF attacks. For example, when a user submits a form that makes changes to their account settings, a nonce is generated and included in the form. When the form is submitted, the server checks the nonce to verify that the request is legitimate and was initiated by the same user session.

The wp_create_nonce function in WordPress is used to generate these nonces. It creates a unique token based on various parameters like the action being performed, the user ID, and a time-dependent variable. This nonce is then included in the form or URL to ensure the integrity of the request.

## Summary of nonce usage
The function wp_create_nonce is a part of WordPress, a popular content management system (CMS) used to build websites. This function is used to create a unique security token, which is a string of characters that verifies the authenticity of requests and data submissions in WordPress.

Let's break down how this function works:

The function accepts an optional parameter $action. This is a unique identifier for the action we're securing. If no action is provided, it defaults to -1.

```
function wp_create_nonce( $action = -1 ) {
```

The function then retrieves the current user with wp_get_current_user(), and gets the user ID. If the user ID doesn't exist (which means the user is not logged in), it applies a filter nonce_user_logged_out to the user ID.

```
$user = wp_get_current_user();
$uid  = (int) $user->ID;
if ( ! $uid ) {
  $uid = apply_filters( 'nonce_user_logged_out', $uid, $action );
}
```
Next, it gets the session token for the current user session with wp_get_session_token(). 
```
$token = wp_get_session_token();
```
Then, it calls wp_nonce_tick($action), a function that returns a time-dependent variable for nonce creation. 
```
$i = wp_nonce_tick( $action );
```
Finally, it generates the nonce by hashing a string that includes the time-dependent variable, the action, the user ID, and the session token. It then returns a substring of this hash.
```
return substr( wp_hash( $i . '|' . $action . '|' . $uid . '|' . $token, 'nonce' ), -12, 10 );
}
```
In simpler terms, wp_create_nonce is a function that generates a unique, time-limited string (nonce) that can be used to verify that a request or action was initiated by the same user session, providing a layer of security against certain types of attacks.



## Get access token


```
public static function get_access_token() {
    static $access_token = null;

    if ( is_null( $access_token ) ) {
       $response = self::http_post( self::build_query( array( 'api_key' => self::get_api_key() ) ), 'token' );

       $access_token = $response[1];
    }

    return $access_token;
}
```


## Get nonce

The selected code is a function named wp_nonce_tick in WordPress. This function is used to generate a time-dependent variable for nonce creation. A nonce, in WordPress, is a "number used once" to help protect URLs and forms from certain types of misuse, malicious or otherwise.

The function accepts an optional parameter $action which defaults to -1. This parameter is used to identify the action associated with the nonce.
```
function wp_nonce_tick( $action = -1 ) {
```
Inside the function, there's a filter applied to the lifespan of nonces. By default, the lifespan of a nonce is one day (represented by DAY_IN_SECONDS). However, this lifespan can be modified by using the nonce_life filter. The $action parameter is also passed to the filter, allowing for more targeted modifications based on the action.
```
$nonce_life = apply_filters( 'nonce_life', DAY_IN_SECONDS, $action );
```
Finally, the function returns a time-dependent variable for nonce creation. This is calculated by dividing the current time by half of the nonce lifespan and rounding up to the nearest integer. This means a nonce has a lifespan of two "ticks" or periods. Nonces in their second tick may be updated, for example, by an autosave operation.
```
return ceil( time() / ( $nonce_life / 2 ) );
```
In summary, wp_nonce_tick is a function that generates a time-dependent variable for nonce creation, providing a mechanism to secure forms and URLs in WordPress.

--HTH--