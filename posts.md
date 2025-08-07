---
layout: posts
title: "所有文章"
permalink: /posts/
author_profile: false
entries_layout: grid
---

<style>
.page__title {
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 1rem;
  text-align: center;
}

.archive__subtitle {
  font-size: 1.8rem;
  font-weight: 600;
  color: #2c5aa0;
  border-bottom: 3px solid #e3f2fd;
  padding-bottom: 0.5rem;
  margin: 2rem 0 1.5rem 0;
  position: relative;
}

.archive__subtitle:before {
  content: "📅";
  margin-right: 0.5rem;
}

.taxonomy__index {
  background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.1);
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
}

.taxonomy__index li {
  margin-bottom: 0.5rem;
}

.taxonomy__index a {
  color: #1976d2;
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  display: inline-block;
  transition: all 0.3s ease;
  background: rgba(33, 150, 243, 0.05);
  border: 1px solid rgba(33, 150, 243, 0.1);
}

.taxonomy__index a:hover {
  background: rgba(33, 150, 243, 0.1);
  transform: translateX(5px);
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.2);
}

.taxonomy__count {
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
  color: white;
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
  margin-left: 0.5rem;
}

.taxonomy__section {
  margin-bottom: 3rem;
  padding: 2rem;
  background: rgba(255,255,255,0.03);
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.1);
  backdrop-filter: blur(10px);
}

.entries-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.archive__item {
  background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid rgba(255,255,255,0.1);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.archive__item:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.15);
  border-color: rgba(33, 150, 243, 0.3);
}

.archive__item:before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.archive__item-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 0.8rem;
  line-height: 1.4;
}

.archive__item-title a {
  color: #1976d2;
  text-decoration: none;
  transition: color 0.3s ease;
}

.archive__item-title a:hover {
  color: #0d47a1;
}

.archive__item-excerpt {
  color: #666;
  font-size: 0.9rem;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.page__meta {
  font-size: 0.8rem;
  color: #888;
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255,255,255,0.1);
}

.page__meta i {
  margin-right: 0.3rem;
}

.back-to-top {
  display: inline-block;
  margin-top: 2rem;
  padding: 0.8rem 1.5rem;
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
  color: white;
  text-decoration: none;
  border-radius: 25px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
}

.back-to-top:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(33, 150, 243, 0.4);
  color: white;
}

/* 搜索和筛选功能 */
.posts-header {
  text-align: center;
  margin-bottom: 3rem;
  padding: 2rem;
  background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.1);
}

.posts-stats {
  color: #666;
  font-size: 1.1rem;
  margin-top: 1rem;
}

@media (max-width: 768px) {
  .entries-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .page__title {
    font-size: 2rem;
  }
  
  .taxonomy__section {
    padding: 1rem;
  }
}
</style>

<div class="posts-header">
  <h1 class="page__title">📚 技术文章集合</h1>
  <p style="color: #666; font-size: 1.1rem; margin: 0;">
    探索我的技术博客，涵盖云计算、容器化、编程语言等多个领域
  </p>
  <div class="posts-stats">
    📊 总计 {{ site.posts.size }} 篇文章 | 🏷️ {{ site.tags.size }} 个标签 | 📅 持续更新中
  </div>
</div>