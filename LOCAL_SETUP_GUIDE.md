# Jekyll博客本地运行指南

这是一个使用Minimal Mistakes主题的Jekyll博客。以下是在本地运行和测试的详细步骤。

## 前置要求

### 1. 安装Ruby环境

**Windows用户：**
1. 访问 [RubyInstaller官网](https://rubyinstaller.org/downloads/)
2. 下载最新的 **Ruby+Devkit** 版本（推荐Ruby 3.0+）
3. 运行安装程序，确保勾选：
   - "Add Ruby executables to your PATH"
   - "Associate .rb and .rbw files with this Ruby installation"
4. 安装完成后，会自动打开MSYS2安装窗口，按提示完成安装

**验证Ruby安装：**
```bash
ruby --version
gem --version
bundler --version
```

### 2. 安装Git（如果还没有）
确保Git已安装并配置好，用于版本控制。

## 本地运行步骤

### 步骤1：安装项目依赖
在项目根目录下运行：
```bash
gem uninstall bundler -v 2.2.26
gem install bundler
rm Gemfile.lock
bundle install
```

如果遇到权限问题，可以尝试：
```bash
bundle install --user-install
```

### 步骤2：启动本地服务器
```bash
bundle exec jekyll serve
```

或者使用带有实时重载的命令：
```bash
bundle exec jekyll serve --livereload
```

### 步骤3：访问网站
打开浏览器，访问：
```
http://localhost:4000
```

## 常用命令

### 构建网站（不启动服务器）
```bash
bundle exec jekyll build
```

### 清理生成的文件
```bash
bundle exec jekyll clean
```

### 启动服务器并监听文件变化
```bash
bundle exec jekyll serve --watch
```

### 启动服务器并启用草稿
```bash
bundle exec jekyll serve --drafts
```

## 项目结构说明

- `_config.yml` - Jekyll配置文件
- `_posts/` - 博客文章目录
- `_layouts/` - 页面布局模板
- `_includes/` - 可重用的页面组件
- `_sass/` - Sass样式文件
- `assets/` - 静态资源（图片、CSS、JS等）
- `Gemfile` - Ruby依赖配置

## 编写新文章

1. 在 `_posts/` 目录下创建新文件
2. 文件命名格式：`YYYY-MM-DD-title.md`
3. 文件开头添加Front Matter：

```yaml
---
layout: single
title: "文章标题"
date: 2024-01-01
categories: [category1, category2]
tags: [tag1, tag2]
---

文章内容...
```

## 常见问题解决

### 1. 依赖安装失败
```bash
# 更新gem
gem update --system

# 清理并重新安装
bundle clean --force
bundle install
```

### 2. 端口被占用
```bash
# 使用不同端口
bundle exec jekyll serve --port 4001
```

### 3. 权限问题
```bash
# 使用用户级安装
bundle install --user-install
```

### 4. 编码问题（Windows）
在命令行中设置编码：
```bash
chcp 65001
```

## 部署到GitHub Pages

这个博客配置为使用GitHub Pages，推送到main分支即可自动部署：
```bash
git add .
git commit -m "更新内容"
git push origin main
```

## 性能优化建议

1. 优化图片大小和格式
2. 使用适当的Jekyll插件
3. 启用缓存和压缩
4. 定期更新依赖包

## 更多资源

- [Jekyll官方文档](https://jekyllrb.com/docs/)
- [Minimal Mistakes主题文档](https://mmistakes.github.io/minimal-mistakes/)
- [Markdown语法指南](https://www.markdownguide.org/)