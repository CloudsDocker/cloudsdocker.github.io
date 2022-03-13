---
header:
    image: /assets/images/hd_ruby_on_rails_error.jpg
title:  Failed to install gem in Mac, incompatible architecture and missing psych
date: 2022-03-11
tags:
 - Ruby
 - Rails
 - Programming
 - MacBook errors
 
permalink: /blogs/tech/en/ruby_gem_installation_error_on_macbook_M1_chips_CPU
layout: single
category: tech
---

> Burn your ego before it burns you.

# Summary
If you trying to install `gem` (ruby gem) on MacBook shipped with M1 CPU. For example following sample command, 

```ruby
gem update --system
```
You may encounter following errors:

 - Installation issues with Arm Mac (M1 Chip)
 - It seems your ruby installation is missing psych (for YAML output).
 - incompatible architecture (have 'x86_64', need 'arm64e')
 - use of undeclared identifier 'username_completion_function'; did you mean 'rl_username_completion_function'?

Here is one error stacktrace for such weird error
```bash
linking shared-object rbconfig/sizeof.bundle
readline.c:1904:37: error: use of undeclared identifier 'username_completion_function'; did you mean 'rl_username_completion_function'?
                                    rl_username_completion_function);
                                    ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    rl_username_completion_function
readline.c:79:42: note: expanded from macro 'rl_username_completion_function'
# define rl_username_completion_function username_completion_function
                                         ^
/usr/local/opt/readline/include/readline/readline.h:485:14: note: 'rl_username_completion_function' declared here
extern char *rl_username_completion_function PARAMS((const char *, int));
             ^
1 error generated.
make[2]: *** [readline.o] Error 1
make[1]: *** [ext/readline/all] Error 2
```

Here are some error screenshots
![](/assets/images/ruby_gem_errors_m1_2.png)


And another error related to this :

![](/assets/images/ruby_gem_errors_m1.png)

# Troubleshooting

> TL;DR; This is because the CPU architecture changed to ARM in Apple's latest M1 chip CPU. So you should run both Ruby binary and rbenv in HomeBrew in `both ARM architecture`.

If you read above error logs in details, you'll find following line:

**incompatible architecture (have 'x86_64', need 'arm64e')**

> This is most likely you upgraded/restored your **old** Mac OS  (in X86 architecture) into **new** MacBook hardware with M1 chipsets (in ARM architecture). Which caused the incompatible issue.

# Solutions
Once we get to figure out the root case, the fix is simple and straightforward.

## Delete *brew* which built in old architecture (X86)
By Running following command from HomeBrew website

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/uninstall.sh)"
```
https://github.com/homebrew/install#uninstall-homebrew

## Then reinstall HomeBrew in latest architecture
Run command 
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then 
```bash
export HOMEBREW_BREW_GIT_REMOTE="..."  # put your Git mirror of Homebrew/brew here
export HOMEBREW_CORE_GIT_REMOTE="..."  # put your Git mirror of Homebrew/homebrew-core here
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
All details can be found at https://github.com/homebrew/install

### Then uninstall and reinstall `rbenv` from Brew


# Conclusion
If aforesaid steps running smoothly, you'll get both `brew`,`rbenv`, and `ruby`, `rails` installed correctly.
Then you can try following command to verify it. 

```bash
ruby -v
```


*Enjoy Coding and happy everyday :-)*


--End--



