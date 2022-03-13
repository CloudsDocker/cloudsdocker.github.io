---
header:
    image: /assets/images/hd_ruby_tips.jpg
title:  Ruby from zero to hero
date: 2022-03-13
tags:
 - Ruby
 - Java
 - Programing
 
permalink: /blogs/tech/en/ace_in_ruby_interview
layout: single
category: tech
---

> This is your life. Do what you love, and do it often.

# Run ruby in 1 second
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


--End--



