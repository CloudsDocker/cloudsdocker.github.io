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


Just type `irb` (Interactive Ruby) in your terminal, you'll get get a Ruby interactive environment, so just type "hello world", you'll see the result directly.
![](/assets/images/ruby_irb.png)

Or just run "puts todd" it will output it to console.

# Call functions in primitive variable
One difference to Java, you can invoke function on primitive variables, e.g. call method `times` on int as below

```ruby
3.times do
  print 'Welcome '
end
```

# Call a function directly, no need parenthesis
In other language, such as Java, you have to suffix `()` even there is no any arguments. However in Ruby, it's save your time for such boilerplate
```ruby
"todd".reverse
"todd".length
"todd"*5
```

To call a function of String on integeger won't work, so suffix `to_s` after number and try 
```ruby
168.to_s.reverse
```
Similarly, you can call `to_i` to convert to integer and `to_a` convert to array

# Functions on list 

```ruby
[12,52,26].max
```

# ! is another syntax sugar
Please see the big exclamation at end of a method `ticket.sort!`, this means the call method will alter the variable for good. On the other hand, no `!` means leave original variable *NOT* changed

```ruby
ticket=[15,6,98,55]
puts ticket
puts "======"
ticket.sort!
puts ticket
```

# Methods chain
You can join multiple methods calls in a chain
```ruby
puts poem.lines.reverse.join
```

# hash map in Ruby

```ruby
books={}
books["Gravitys Rainbow"]=:splendid
```

Did you realized the `:` in front of *splendid*? This is actually indicate it's a **symbol**

When you place a colon in front of a simple word, you get a symbol. Symbols are cheaper than strings (in terms of computer memory.) If you use a word over and over in your program, use a symbol. Rather than having thousands of copies of that word in memory, the computer will store the symbol only once.

# To loop hash map values

```ruby
ratings = Hash.new{0}
books.values.each{ |rate|
  ratings[rate]+=1
  }
puts ratings
```

# To loop a fixed times by assigning a primitive number
Different to Java or other language, you can call method on top of a int value directly, then apply functions in a block .

Moreover, you can surround *input* variable for the *block* with two **pipes** symbol.
```ruby
5.times {print "*===="}
5.times { |time|
  puts time
}
```

# parenthesis is optional and better to not
with or without parentheses is the same to Ruby, but the version without parentheses is a bit easier to read. And it saves you valuable typing time!
```ruby
puts "Hello"
puts("Hello")


def tame(number_of_shrews)
  number_of_shrews.times {
    puts "tamed a shrew"
    }
end

tame(5)
```


# To convert JSON to hashmap easily


```ruby
s = get_shakey
s["William Shakespeare"].each { |key,val|
  puts val["title"]
  }
```

# High end functions in hashmap
You can call `select` to filter hashmap then use `count` to gather number of occupance
```ruby
def count_plays(year)
  s = get_shakey

  s["William Shakespeare"]
    .select { |k, v|
      v["finished"] == year
    }.each { |key, val|
      puts val["title"]
    }.count
end

puts count_plays(0)
```
--End--



