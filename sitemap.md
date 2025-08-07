---
layout: archive
title: "网站地图"
permalink: /sitemap/
author_profile: false
---

<style>
.sitemap-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.1);
  backdrop-filter: blur(10px);
}

.sitemap-section h2 {
  color: #2c5aa0;
  border-bottom: 2px solid #e3f2fd;
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}

.sitemap-list {
  list-style: none;
  padding: 0;
}

.sitemap-list li {
  margin-bottom: 0.5rem;
  padding-left: 1rem;
  position: relative;
}

.sitemap-list li:before {
  content: "📄";
  position: absolute;
  left: 0;
}

.sitemap-list a {
  color: #1976d2;
  text-decoration: none;
  transition: color 0.3s ease;
}

.sitemap-list a:hover {
  color: #0d47a1;
  text-decoration: underline;
}

.year-section {
  margin-bottom: 1.5rem;
}

.year-title {
  font-size: 1.2rem;
  font-weight: bold;
  color: #1565c0;
  margin-bottom: 0.5rem;
}

.post-count {
  color: #666;
  font-size: 0.9rem;
  margin-left: 0.5rem;
}
</style>

## 📋 网站导航

<div class="sitemap-section">
  <h2>🏠 主要页面</h2>
  <ul class="sitemap-list">
    <li><a href="{{ '/' | relative_url }}">首页</a></li>
    <li><a href="{{ '/about/' | relative_url }}">关于</a></li>
    <li><a href="{{ '/sitemap/' | relative_url }}">网站地图</a></li>
  </ul>
</div>

<div class="sitemap-section">
  <h2>📚 技术文章</h2>
  
  {% assign posts_by_year = site.posts | group_by_exp: "post", "post.date | date: '%Y'" %}
  {% for year in posts_by_year %}
    <div class="year-section">
      <div class="year-title">
        {{ year.name }} 年
        <span class="post-count">({{ year.items | size }} 篇文章)</span>
      </div>
      <ul class="sitemap-list">
        {% for post in year.items %}
          <li>
            <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
            <small style="color: #666; margin-left: 0.5rem;">
              {{ post.date | date: "%m-%d" }}
              {% if post.tags.size > 0 %}
                | {{ post.tags | join: ", " }}
              {% endif %}
            </small>
          </li>
        {% endfor %}
      </ul>
    </div>
  {% endfor %}
</div>

<div class="sitemap-section">
  <h2>🏷️ 标签分类</h2>
  <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
    {% assign sorted_tags = site.tags | sort %}
    {% for tag in sorted_tags %}
      <a href="{{ '/tags/#' | append: tag[0] | slugify | relative_url }}" 
         style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
                color: #1565c0; 
                padding: 0.3rem 0.8rem; 
                border-radius: 20px; 
                text-decoration: none; 
                font-size: 0.9rem;
                border: 1px solid rgba(21, 101, 192, 0.2);
                transition: all 0.3s ease;">
        {{ tag[0] }} ({{ tag[1].size }})
      </a>
    {% endfor %}
  </div>
</div>

<div class="sitemap-section">
  <h2>🔗 技术资源</h2>
  <ul class="sitemap-list">
    <li><a href="https://github.com/CloudsDocker" target="_blank">GitHub 项目</a></li>
    <li><a href="{{ '/feed.xml' | relative_url }}">RSS 订阅</a></li>
    <li><a href="{{ '/sitemap.xml' | relative_url }}">XML 网站地图</a></li>
  </ul>
</div>

---

<div style="text-align: center; margin-top: 2rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px;">
  <p style="color: #666; margin: 0;">
    📊 总计: {{ site.posts.size }} 篇技术文章 | 
    🏷️ {{ site.tags.size }} 个标签 | 
    📅 最后更新: {{ site.time | date: "%Y-%m-%d" }}
  </p>
</div>