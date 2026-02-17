---
title: Advanced Search
description: Search and filter documentation using faceted navigation for quick discovery
content_type: reference
product: both
tags:
- Reference
- Search
last_reviewed: null
original_author: null
---


# Advanced Search

<div id="faceted-search-app">
  <p style="text-align: center; padding: 2rem; color: var(--md-default-fg-color--light);">
    Loading search interface.
  </p>
</div>

<style>
  /*Custom styles for faceted search*/
  .fs-container {
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
  }

  .fs-sidebar {
    min-width: 250px;
    flex: 0 0 250px;
  }

  .fs-results {
    flex: 1;
    min-width: 300px;
  }

  .fs-search-box {
    width: 100%;
    padding: 10px 16px;
    margin-bottom: 1.5rem;
    border: 2px solid var(--md-default-fg-color--lighter);
    border-radius: 8px;
    font-size: 1rem;
    background: var(--md-default-bg-color);
    color: var(--md-default-fg-color);
    transition: border-color 0.2s;
  }

  .fs-search-box:focus {
    outline: none;
    border-color: var(--md-primary-fg-color);
  }

  .fs-facet-group {
    margin-bottom: 1.5rem;
  }

  .fs-facet-title {
    display: block;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--md-default-fg-color--light);
  }

  .fs-facet-option {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
    font-size: 0.95rem;
    cursor: pointer;
  }

  .fs-facet-option:hover {
    color: var(--md-primary-fg-color);
  }

  .fs-facet-checkbox {
    cursor: pointer;
  }

  .fs-facet-count {
    margin-left: auto;
    padding: 0 6px;
    font-size: 0.85rem;
    color: var(--md-default-fg-color--lighter);
    background: var(--md-default-bg-color--secondary);
    border-radius: 10px;
  }

  .fs-clear-btn {
    margin-top: 1rem;
    padding: 8px 16px;
    cursor: pointer;
    border: 1px solid var(--md-default-fg-color--lighter);
    border-radius: 6px;
    background: var(--md-default-bg-color);
    color: var(--md-default-fg-color);
    font-size: 0.9rem;
    transition: all 0.2s;
  }

  .fs-clear-btn:hover {
    background: var(--md-default-fg-color--lightest);
  }

  .fs-result-count {
    color: var(--md-default-fg-color--light);
    margin-bottom: 1.5rem;
    font-size: 0.95rem;
  }

  .fs-result-item {
    margin-bottom: 1.5rem;
    padding: 1.2rem;
    border: 1px solid var(--md-default-fg-color--lightest);
    border-radius: 8px;
    transition: all 0.2s;
  }

  .fs-result-item:hover {
    border-color: var(--md-primary-fg-color);
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }

  .fs-result-title {
    font-size: 1.15rem;
    font-weight: 600;
    text-decoration: none;
    color: var(--md-primary-fg-color);
  }

  .fs-result-title:hover {
    text-decoration: underline;
  }

  .fs-result-badges {
    margin: 0.5rem 0;
  }

  .fs-badge {
    display: inline-block;
    padding: 3px 10px;
    margin-right: 6px;
    font-size: 0.8rem;
    border-radius: 4px;
    background: var(--md-primary-fg-color);
    color: var(--md-primary-bg-color);
  }

  .fs-badge.type {
    background: var(--md-accent-fg-color);
  }

  .fs-badge.product {
    background: var(--md-code-bg-color);
    color: var(--md-code-fg-color);
  }

  .fs-result-description {
    margin: 0.5rem 0 0;
    font-size: 0.95rem;
    color: var(--md-default-fg-color--light);
    line-height: 1.5;
  }

  .fs-no-results {
    padding: 3rem;
    text-align: center;
    color: var(--md-default-fg-color--light);
  }

  @media (max-width: 768px) {
    .fs-sidebar {
      flex: 1 1 100%;
    }
  }
</style>
