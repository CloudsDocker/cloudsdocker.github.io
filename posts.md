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
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 1rem;
  text-align: center;
}

.archive__subtitle {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--ink);
  border-bottom: 1px solid var(--line);
  padding-bottom: 0.5rem;
  margin: 2rem 0 1.5rem 0;
  position: relative;
}

.archive__subtitle:before {
  content: "📅";
  margin-right: 0.5rem;
}

.taxonomy__index {
  background: var(--paper-2);
  border-radius: var(--radius);
  padding: 1.5rem;
  margin-bottom: 2rem;
  border: 1px solid var(--line);
  box-shadow: none;
}

.taxonomy__index li {
  margin-bottom: 0.5rem;
}

.taxonomy__index a {
  color: var(--ink-2);
  text-decoration: none;
  font-weight: 500;
  padding: 0.45rem 0.9rem;
  border-radius: 6px;
  display: inline-block;
  transition: background 0.2s ease, color 0.2s ease;
  background: #fff;
  border: 1px solid var(--line);
}

.taxonomy__index a:hover {
  background: var(--clay-tint);
  color: var(--clay-deep);
  border-color: var(--line-2);
  transform: none;
  box-shadow: none;
}

.taxonomy__count {
  background: var(--clay);
  color: #fff;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 500;
  margin-left: 0.5rem;
}

.taxonomy__section {
  margin-bottom: 3rem;
  padding: 2rem;
  background: transparent;
  border-radius: 0;
  border: none;
}

.entries-grid {
  display: grid !important;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)) !important;
  gap: 1.5rem;
  margin-top: 1.5rem;
  width: 100%;
}

@media (min-width: 600px) {
  .entries-grid {
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)) !important;
  }
}

@media (min-width: 768px) {
  .entries-grid {
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)) !important;
  }
}

@media (min-width: 1024px) {
  .entries-grid {
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)) !important;
  }
}

@media (min-width: 1280px) {
  .entries-grid {
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)) !important;
  }
}

.archive__item {
  background: #fff;
  border-radius: var(--radius);
  padding: 1.5rem;
  border: 1px solid var(--line);
  box-shadow: var(--shadow-sm);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
  position: relative;
  overflow: hidden;
}

.archive__item:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
  border-color: var(--line-2);
}

.archive__item:before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--clay);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.archive__item:hover:before {
  opacity: 1;
}

.archive__item-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 0.8rem;
  line-height: 1.4;
}

.archive__item-title a {
  color: var(--ink);
  text-decoration: none;
  transition: color 0.2s ease;
}

.archive__item-title a:hover {
  color: var(--clay);
}

.archive__item-excerpt {
  color: var(--ink-2);
  font-size: 0.9rem;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.page__meta {
  font-size: 0.8rem;
  color: var(--ink-3);
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--line);
}

.page__meta i {
  margin-right: 0.3rem;
}

.back-to-top {
  display: inline-block;
  margin-top: 2rem;
  padding: 0.6rem 1.2rem;
  background: transparent;
  color: var(--ink-2);
  text-decoration: none;
  border: 1px solid var(--line-2);
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.9rem;
  transition: background 0.2s ease, color 0.2s ease;
  box-shadow: none;
}

.back-to-top:hover {
  background: var(--clay-tint);
  color: var(--clay-deep);
  transform: none;
  box-shadow: none;
}

/* Remove sidebar width reservation since author_profile is false */
#main .archive {
  width: 100% !important;
  padding-right: 0 !important;
  float: none !important;
  max-width: 100%;
}

.taxonomy__section {
  width: 100%;
  margin-left: 0;
  margin-right: 0;
}

.entries-grid .grid__item {
  float: none !important;
  width: auto !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
}

/* 页面头部 */
.posts-header {
  text-align: center;
  margin-bottom: 3rem;
  padding: 2.5rem 2rem;
  background: var(--paper-2);
  border-radius: var(--radius);
  border: 1px solid var(--line);
}

.posts-stats {
  color: var(--ink-3);
  font-size: 0.95rem;
  margin-top: 1rem;
}

@media (max-width: 599px) {
  .entries-grid {
    grid-template-columns: 1fr !important;
    gap: 1rem;
  }

  .page__title {
    font-size: 2rem;
  }

  .taxonomy__section {
    padding: 1rem 0;
  }
}
</style>

<div class="posts-header">
  <h1 class="page__title">📚 技术文章集合</h1>
  <p style="color: var(--ink-2); font-size: 1.05rem; margin: 0;">
    探索我的技术博客，涵盖云计算、容器化、编程语言等多个领域
  </p>
  <div class="posts-stats">
    📊 总计 {{ site.posts.size }} 篇文章 | 🏷️ {{ site.tags.size }} 个标签 | 📅 持续更新中
  </div>
</div>