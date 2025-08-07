# setup env

```bash
export PATH="/opt/homebrew/opt/ruby/bin:/opt/homebrew/bin:$PATH" && bundle install 
export PATH="/opt/homebrew/opt/ruby/bin:/opt/homebrew/bin:$PATH" && bundle update jekyll 
export PATH="/opt/homebrew/opt/ruby/bin:/opt/homebrew/bin:$PATH" && bundle exec jekyll serve --host 0.0.0.0 --livereload 
```

# To setup for a new blog

To run below command setup folder and files

```shell
mkdir -p ~/dev/ws/todd/cloudsdocker.github.io/_posts/2025/"$(date +%m)"/"$(date +%m%d)"
```

Then use your keyword to create a file 
```shell
touch ~/dev/ws/todd/cloudsdocker.github.io/_posts/2025/"$(date +%m)"/"$(date +%m%d)"/"$(date +%Y-%m-%d)-fix-annoying-fake-security-prompt-in-docker-desktop-in-macbook.md"
```

Then download the blog source to clipboard
```shell
cat ~/Downloads/docker-desktop-security-fix.md | pbcopy
```