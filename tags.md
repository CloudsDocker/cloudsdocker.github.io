---
layout: tags
title: "标签分类"
permalink: /tags/
author_profile: false
---

<style>
.tag-cloud {
  text-align: center;
  margin: 2rem 0;
  padding: 2rem;
  background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.1);
  backdrop-filter: blur(10px);
}

.tag-cloud a {
  display: inline-block;
  margin: 0.3rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  color: #1565c0;
  text-decoration: none;
  border-radius: 25px;
  border: 1px solid rgba(21, 101, 192, 0.2);
  transition: all 0.3s ease;
  font-weight: 500;
}

.tag-cloud a:hover {
  background: linear-gradient(135deg, #bbdefb 0%, #90caf9 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(21, 101, 192, 0.3);
}

.tag-section {
  margin: 2rem 0;
  padding: 1.5rem;
  background: rgba(255,255,255,0.05);
  border-radius: 12px;
  border-left: 4px solid #2196f3;
}

.tag-title {
  color: #1976d2;
  font-size: 1.5rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.post-list {
  list-style: none;
  padding: 0;
}

.post-list li {
  margin-bottom: 0.8rem;
  padding: 0.8rem;
  background: rgba(255,255,255,0.03);
  border-radius: 8px;
  border-left: 3px solid #2196f3;
  transition: all 0.3s ease;
}

.post-list li:hover {
  background: rgba(255,255,255,0.08);
  transform: translateX(5px);
}

.post-list a {
  color: #1976d2;
  text-decoration: none;
  font-weight: 500;
}

.post-list a:hover {
  color: #0d47a1;
  text-decoration: underline;
}

.post-meta {
  color: #666;
  font-size: 0.9rem;
  margin-top: 0.3rem;
}
</style>

## 🏷️ 标签云

<div class="tag-cloud">
  {% assign sorted_tags = site.tags | sort %}
  {% for tag in sorted_tags %}
    <a href="#{{ tag[0] | slugify }}" style="font-size: {{ tag[1].size | times: 0.8 | plus: 1 }}rem;">
      {{ tag[0] }} ({{ tag[1].size }})
    </a>
  {% endfor %}
</div>

---

## 📚 按标签分类的文章

{% for tag in sorted_tags %}
  <div class="tag-section" id="{{ tag[0] | slugify }}">
    <h3 class="tag-title">
      🔖 {{ tag[0] }}
      <span style="font-size: 0.8rem; color: #666;">({{ tag[1].size }} 篇文章)</span>
    </h3>
    
    <ul class="post-list">
      {% assign sorted_posts = tag[1] | sort: 'date' | reverse %}
      {% for post in sorted_posts %}
        <li>
          <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
          <div class="post-meta">
            📅 {{ post.date | date: "%Y-%m-%d" }}
            {% if post.excerpt %}
              <br>{{ post.excerpt | strip_html | truncate: 100 }}
            {% endif %}
          </div>
        </li>
      {% endfor %}
    </ul>
  </div>
{% endfor %}

---

<div style="text-align: center; margin-top: 2rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px;">
  <p style="color: #666; margin: 0;">
    📊 共有 {{ site.tags.size }} 个标签，{{ site.posts.size }} 篇文章
  </p>
</div>