rsync -r ~/dev/hexo/myblog/*   ~/dev/hexo/cloudsdocker.github.io/
rm -fr ~/dev/hexo/cloudsdocker.github.io/public
rm -fr ~/dev/hexo/cloudsdocker.github.io/archives
git fetch origin blogSrc
git add --all
git commit -m 'daily commit'
git push -u origin 'blogSrc'
