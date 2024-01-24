---
title: Deep dive for word press preview nonce
header:
    image: /assets/images/Deep_dive_for_word_press_preview_nonce.jpg
date: 2024-01-24
tags:
- WordPress

permalink: /blogs/tech/en/Deep_dive_for_word_press_preview_nonce_chn
layout: single
category: tech
---
> One must learn by doing the thing; for though you think you know it, you have no certainty, until you try. —Sophocles

# Deep dive for word press preview nonce

# wp_create_nonce 函数详解

`wp_create_nonce` 函数是WordPress的一部分，这是一个用于构建网站的流行内容管理系统（CMS）。该函数用于创建一个唯一的安全令牌，这是一个字符串，用于验证WordPress中的请求和数据提交的真实性。

让我们来详细了解这个函数的工作原理：

该函数接受一个可选参数 `$action`。这是我们正在保护的操作的唯一标识符。如果未提供任何操作，默认为 -1。

```php
function wp_create_nonce( $action = -1 ) {
```
然后，该函数使用wp_get_current_user()检索当前用户，并获取用户ID。如果用户ID不存在（这意味着用户未登录），则将一个过滤器nonce_user_logged_out应用于用户ID。

```php
$user = wp_get_current_user();
$uid  = (int) $user->ID;
if ( ! $uid ) {
  $uid = apply_filters( 'nonce_user_logged_out', $uid, $action );
}
```

接下来，它使用wp_get_session_token()获取当前用户会话的会话令牌。

```php
$token = wp_get_session_token();
```

然后，它调用wp_nonce_tick($action)，这是一个返回用于生成nonce的时间相关变量的函数。

```php
$i = wp_nonce_tick( $action );
```

最后，它通过对包含时间相关变量、操作、用户ID和会话令牌的字符串进行哈希处理来生成nonce。然后，它返回该哈希的子字符串。

```php
return substr( wp_hash( $i . '|' . $action . '|' . $uid . '|' . $token, 'nonce' ), -12, 10 );
}
```

简单来说，wp_create_nonce是一个生成唯一的、有时限的字符串（nonce）的函数，用于验证请求或操作是否由相同的用户会话发起，提供了一层对某些类型攻击的安全性。

## 获取访问令牌

```php
public static function get_access_token() {
    static $access_token = null;

    if ( is_null( $access_token ) ) {
       $response = self::http_post( self::build_query( array( 'api_key' => self::get_api_key() ) ), 'token' );

       $access_token = $response[1];
    }

    return $access_token;
}
```
## 获取nonce
所选代码是WordPress中的一个名为wp_nonce_tick的函数。此函数用于生成用于创建nonce的时间相关变量。在WordPress中，nonce是用于保护URL和表单免受某些类型滥用的“一次性数字”。

该函数接受一个可选参数$action，默认为-1。此参数用于标识与nonce相关联的操作。

```php
function wp_nonce_tick( $action = -1 ) {
```

在函数内部，对nonce寿命应用了一个过滤器。默认情况下，nonce的寿命为一天（用DAY_IN_SECONDS表示）。然而，通过使用nonce_life过滤器，可以修改这个寿命。$action参数也传递给过滤器，允许基于操作进行更有针对性的修改。

```php
$nonce_life = apply_filters( 'nonce_life', DAY_IN_SECONDS, $action );
```

最后，函数返回用于创建nonce的时间相关变量。这是通过将当前时间除以nonce寿命的一半并向上取整来计算的。这意味着nonce有两个“ticks”或期间的寿命。例如，第二个tick的nonce可能会被自动保存操作更新。

```php
return ceil( time() / ( $nonce_life / 2 ) );
```

总之，wp_nonce_tick是一个生成用于创建nonce的时间相关变量的函数，提供了在WordPress中保护表单和URL的机制。

--HTH--