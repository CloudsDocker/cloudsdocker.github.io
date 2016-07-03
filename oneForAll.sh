# copy files to master page and conduct deploy
rsync -avh  ~/dev/hexo/cloudsdocker.github.io/* ~/dev/hexo/myblog/
cd ~/dev/hexo/myblog/
hexo clean
hexo g
hexo d
# submit source to blogSrc branch

git status
git fetch origin blogSrc
git add --all
git commit -m 'daily commit'
git push -u origin 'blogSrc'
