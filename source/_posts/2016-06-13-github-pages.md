---
Layout: page
title: Github page commands notes
tag:
- Git
- GitPages
---
## following lages are searchable in google 

- [alice](http://byalice.github.io/2016/06/04/Build-Blog/)
- gihub

# Travis errors:

Got following errors in Travis page:

branch not included or excluded

`solution`: that's because your source branch, such as 'blogSrc' should be added in whitelist of .travis.yml, for instance

```sh
branches:
  only:
  - blogSrc
```
