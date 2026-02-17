/**
 * Faceted Search for MkDocs
 * Configurable for any project - automatically discovers facets from data
 */

document.addEventListener("DOMContentLoaded", async () => {
  const container = document.getElementById("faceted-search-app");
  if (!container) return;

  // Configuration - easily customizable per project
  const CONFIG = {
    // Define which fields to use as facets and their display names
    facets: {
      content_type: "Content Type",
      product: "Product",
      component: "Component",
      tags: "Tags",
      audience: "Audience",
      difficulty: "Difficulty"
    },
    // Badge colors for different facet types (optional)
    badgeColors: {
      content_type: "type",
      product: "product",
      component: "component"
    }
  };

  // Try multiple paths for the facets index (handles different page depths)
  async function loadFacetsIndex() {
    const paths = [
      "../assets/facets-index.json",
      "./assets/facets-index.json",
      "../../assets/facets-index.json",
      "/assets/facets-index.json"
    ];

    for (const path of paths) {
      try {
        const resp = await fetch(path);
        if (resp.ok) {
          return await resp.json();
        }
      } catch (e) {
        // Try next path
      }
    }

    throw new Error("Could not load facets index");
  }

  // Load data
  let pages = [];
  try {
    pages = await loadFacetsIndex();
  } catch (e) {
    container.innerHTML = `
      <div class="fs-no-results">
        <p>Search index is being generated. Please refresh in a moment.</p>
        <p style="font-size: 0.9rem; margin-top: 1rem;">
          If this persists, ensure <code>generate_facets_index.py</code> runs during build.
        </p>
      </div>
    `;
    return;
  }

  // Discover available facets from the data
  const availableFacets = {};
  const facetCounts = {};

  // Initialize facet structures
  Object.keys(CONFIG.facets).forEach(facetKey => {
    availableFacets[facetKey] = new Set();
    facetCounts[facetKey] = {};
  });

  // Collect facet values from all pages
  pages.forEach(page => {
    Object.keys(CONFIG.facets).forEach(facetKey => {
      const value = page[facetKey];
      if (value) {
        if (Array.isArray(value)) {
          // Handle array fields like tags
          value.forEach(v => {
            availableFacets[facetKey].add(v);
            facetCounts[facetKey][v] = (facetCounts[facetKey][v] || 0) + 1;
          });
        } else {
          // Handle single-value fields
          availableFacets[facetKey].add(value);
          facetCounts[facetKey][value] = (facetCounts[facetKey][value] || 0) + 1;
        }
      }
    });
  });

  // Convert sets to sorted arrays and filter empty facets
  const facets = {};
  Object.keys(CONFIG.facets).forEach(facetKey => {
    const values = Array.from(availableFacets[facetKey]).sort();
    if (values.length > 0) {
      facets[facetKey] = values;
    }
  });

  // Application state
  const state = {
    query: "",
    filters: {}
  };

  // Initialize filters
  Object.keys(facets).forEach(facetKey => {
    state.filters[facetKey] = [];
  });

  // Search function
  function searchPages(query, filters) {
    return pages.filter(page => {
      // Text search
      if (query) {
        const q = query.toLowerCase();
        const searchable = [
          page.title,
          page.description,
          page.snippet,
          ...(page.tags || [])
        ].filter(Boolean).join(" ").toLowerCase();

        if (!searchable.includes(q)) {
          return false;
        }
      }

      // Apply facet filters
      for (const [facetKey, selectedValues] of Object.entries(filters)) {
        if (selectedValues.length === 0) continue;

        const pageValue = page[facetKey];
        if (!pageValue) return false;

        if (Array.isArray(pageValue)) {
          // For array fields, check if any selected value is in the array
          if (!selectedValues.some(v => pageValue.includes(v))) {
            return false;
          }
        } else {
          // For single-value fields
          if (!selectedValues.includes(pageValue)) {
            return false;
          }
        }
      }

      return true;
    });
  }

  // Render functions
  function renderFacetGroup(label, facetKey, values) {
    if (!values || values.length === 0) return "";

    const selectedCount = state.filters[facetKey].length;
    const labelWithCount = selectedCount > 0 ? `${label} (${selectedCount})` : label;

    return `
      <div class="fs-facet-group">
        <strong class="fs-facet-title">${labelWithCount}</strong>
        ${values.map(value => {
          const count = facetCounts[facetKey][value] || 0;
          const isChecked = state.filters[facetKey].includes(value);
          return `
            <label class="fs-facet-option">
              <input type="checkbox"
                class="fs-facet-checkbox"
                data-facet="${facetKey}"
                data-value="${value}"
                ${isChecked ? "checked" : ""}>
              <span>${value}</span>
              <span class="fs-facet-count">${count}</span>
            </label>
          `;
        }).join("")}
      </div>
    `;
  }

  function renderResult(page) {
    // Collect badges
    const badges = [];

    Object.keys(CONFIG.facets).forEach(facetKey => {
      const value = page[facetKey];
      if (value && facetKey !== "tags" && facetKey !== "description") {
        if (Array.isArray(value)) {
          badges.push(...value.map(v => ({ key: facetKey, value: v })));
        } else if (value !== "both") {  // Skip generic values
          badges.push({ key: facetKey, value });
        }
      }
    });

    // Build URL (handle relative paths)
    let url = page.url;
    if (!url.startsWith("/") && !url.startsWith("http")) {
      url = "../" + url;
    }

    return `
      <div class="fs-result-item">
        <a href="${url}" class="fs-result-title">${page.title || "Untitled"}</a>
        ${badges.length > 0 ? `
          <div class="fs-result-badges">
            ${badges.map(b => `
              <span class="fs-badge ${CONFIG.badgeColors[b.key] || ""}">${b.value}</span>
            `).join("")}
          </div>
        ` : ""}
        <p class="fs-result-description">
          ${page.description || page.snippet || "No description available"}
        </p>
      </div>
    `;
  }

  function render() {
    const filtered = searchPages(state.query, state.filters);

    // Count active filters
    const activeFilterCount = Object.values(state.filters)
      .reduce((sum, arr) => sum + arr.length, 0);

    container.innerHTML = `
      <div class="fs-container">
        <div class="fs-sidebar">
          <input type="text"
            id="fs-query"
            class="fs-search-box"
            placeholder="Search documentation..."
            value="${state.query}">

          ${Object.entries(facets)
            .map(([key, values]) => renderFacetGroup(CONFIG.facets[key], key, values))
            .join("")}

          ${activeFilterCount > 0 ? `
            <button id="fs-clear" class="fs-clear-btn">
              Clear all filters (${activeFilterCount})
            </button>
          ` : ""}
        </div>

        <div class="fs-results">
          <p class="fs-result-count">
            ${filtered.length} ${filtered.length === 1 ? "result" : "results"}
            ${state.query ? ` for "${state.query}"` : ""}
            ${activeFilterCount > 0 ? ` with ${activeFilterCount} filter${activeFilterCount !== 1 ? "s" : ""}` : ""}
          </p>

          ${filtered.length > 0 ?
            filtered.map(renderResult).join("") :
            `<div class="fs-no-results">
              <h3>No results found</h3>
              <p>Try adjusting your search terms or filters</p>
            </div>`
          }
        </div>
      </div>
    `;

    // Bind events
    bindEvents();
  }

  function bindEvents() {
    // Search input
    const searchInput = document.getElementById("fs-query");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        state.query = e.target.value;
        render();
      });

      // Auto-focus search input
      if (!state.query) {
        searchInput.focus();
      }
    }

    // Facet checkboxes
    document.querySelectorAll(".fs-facet-checkbox").forEach(checkbox => {
      checkbox.addEventListener("change", (e) => {
        const facet = e.target.dataset.facet;
        const value = e.target.dataset.value;

        if (e.target.checked) {
          if (!state.filters[facet].includes(value)) {
            state.filters[facet].push(value);
          }
        } else {
          state.filters[facet] = state.filters[facet].filter(v => v !== value);
        }

        render();
      });
    });

    // Clear button
    const clearBtn = document.getElementById("fs-clear");
    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        state.query = "";
        Object.keys(state.filters).forEach(key => {
          state.filters[key] = [];
        });
        render();
      });
    }
  }

  // Initial render
  render();
});