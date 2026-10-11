/**
 * Edward W. Pritchard Stories Archive - Client JavaScript
 * Interactive Search, Filters, Themes, Quick Reader & Keyboard Shortcuts
 */

(function () {
  'use strict';

  // --- Theme Management ---
  const THEMES = ['dark', 'sepia', 'light'];
  const STORAGE_THEME = 'ewp_theme';
  const STORAGE_FONT_SIZE = 'ewp_font_size';

  function initTheme() {
    const saved = localStorage.getItem(STORAGE_THEME);
    if (saved && THEMES.includes(saved)) {
      document.body.setAttribute('data-theme', saved);
    } else {
      document.body.setAttribute('data-theme', 'dark');
    }

    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    if (themeToggleBtn) {
      themeToggleBtn.addEventListener('click', cycleTheme);
    }
  }

  function cycleTheme() {
    const current = document.body.getAttribute('data-theme') || 'dark';
    const nextIdx = (THEMES.indexOf(current) + 1) % THEMES.length;
    const next = THEMES[nextIdx];
    document.body.setAttribute('data-theme', next);
    localStorage.setItem(STORAGE_THEME, next);
  }

  // --- Reader Font Sizing ---
  function initFontSize() {
    const savedSize = localStorage.getItem(STORAGE_FONT_SIZE);
    if (savedSize) {
      document.documentElement.style.setProperty('--reader-font-size', savedSize + 'px');
    }

    const decBtn = document.getElementById('font-decrease-btn');
    const incBtn = document.getElementById('font-increase-btn');

    if (decBtn && incBtn) {
      decBtn.addEventListener('click', () => changeFontSize(-2));
      incBtn.addEventListener('click', () => changeFontSize(2));
    }
  }

  function changeFontSize(delta) {
    const rootStyle = getComputedStyle(document.documentElement);
    let cur = parseInt(rootStyle.getPropertyValue('--reader-font-size'), 10) || 18;
    cur = Math.max(14, Math.min(26, cur + delta));
    document.documentElement.style.setProperty('--reader-font-size', cur + 'px');
    localStorage.setItem(STORAGE_FONT_SIZE, cur);
  }

  // --- Reading Progress Bar ---
  function initReadingProgress() {
    const progressBar = document.querySelector('.reading-progress-bar');
    if (!progressBar) return;

    window.addEventListener('scroll', () => {
      const scrollTotal = document.documentElement.scrollHeight - window.innerHeight;
      if (scrollTotal > 0) {
        const pct = Math.min(100, Math.max(0, (window.scrollY / scrollTotal) * 100));
        progressBar.style.width = pct + '%';
      }
    }, { passive: true });
  }

  // --- Quick View Modal ---
  let modalOverlay = null;
  let modalTitle = null;
  let modalMeta = null;
  let modalBody = null;
  let modalFullLink = null;

  function initModal() {
    modalOverlay = document.getElementById('quick-modal');
    if (!modalOverlay) return;

    modalTitle = document.getElementById('modal-title');
    modalMeta = document.getElementById('modal-meta');
    modalBody = document.getElementById('modal-body');
    modalFullLink = document.getElementById('modal-full-link');

    const closeBtn = document.getElementById('modal-close-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', closeModal);
    }

    modalOverlay.addEventListener('click', (e) => {
      if (e.target === modalOverlay) closeModal();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeModal();
    });
  }

  function openModal(story) {
    if (!modalOverlay) return;
    modalTitle.textContent = story.t;
    modalMeta.innerHTML = `
      <span>📅 ${story.d}</span>
      <span>📖 ${story.w.toLocaleString()} words (~${story.m} min read)</span>
      ${story.c && story.c.length ? `<span>🏷️ ${story.c.join(', ')}</span>` : ''}
    `;
    modalBody.innerHTML = `<p>${escapeHTML(story.e)}</p><p style="color:var(--text-secondary);font-style:italic;">(Click 'Read Full Story' below to view full unabridged text and chapter divisions...)</p>`;
    
    // Resolve URL relative to current root
    const rootPrefix = getRootPrefix();
    modalFullLink.href = rootPrefix + story.u;

    modalOverlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    if (!modalOverlay) return;
    modalOverlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  function getRootPrefix() {
    if (document.body && document.body.dataset && document.body.dataset.root !== undefined) {
      return document.body.dataset.root;
    }
    const path = window.location.pathname;
    if (path.includes('/stories/')) {
      return '../../';
    }
    if (path.includes('/years/')) {
      return '../';
    }
    return '';
  }

  function escapeHTML(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // --- Random Story Dice Roll ---
  let isRolling = false;

  function initRandomStory() {
    const randomBtn = document.getElementById('random-story-btn');
    if (!randomBtn) return;

    randomBtn.addEventListener('click', rollRandomStory);
  }

  function ensureArchiveLoaded() {
    if (window.STORY_ARCHIVE && window.STORY_ARCHIVE.length) {
      return Promise.resolve(window.STORY_ARCHIVE);
    }

    return new Promise((resolve, reject) => {
      const rootPrefix = getRootPrefix();

      // Check if existing script tag is already in DOM
      const existingScript = document.querySelector('script[src*="stories-data.js"]');
      if (existingScript) {
        let attempts = 0;
        const interval = setInterval(() => {
          attempts++;
          if (window.STORY_ARCHIVE && window.STORY_ARCHIVE.length) {
            clearInterval(interval);
            resolve(window.STORY_ARCHIVE);
          } else if (attempts > 60) {
            clearInterval(interval);
            fetchFallback().then(resolve).catch(reject);
          }
        }, 50);

        existingScript.addEventListener('load', () => {
          clearInterval(interval);
          if (window.STORY_ARCHIVE && window.STORY_ARCHIVE.length) {
            resolve(window.STORY_ARCHIVE);
          } else {
            fetchFallback().then(resolve).catch(reject);
          }
        }, { once: true });
        return;
      }

      // If script tag is not present at all, dynamically insert it
      const script = document.createElement('script');
      script.src = rootPrefix + 'js/stories-data.js';
      script.onload = () => {
        if (window.STORY_ARCHIVE && window.STORY_ARCHIVE.length) {
          resolve(window.STORY_ARCHIVE);
        } else {
          fetchFallback().then(resolve).catch(reject);
        }
      };
      script.onerror = () => {
        fetchFallback().then(resolve).catch(reject);
      };
      document.head.appendChild(script);
    });
  }

  function fetchFallback() {
    const rootPrefix = getRootPrefix();
    return fetch(rootPrefix + 'stories.json')
      .then(r => r.json())
      .then(data => {
        window.STORY_ARCHIVE = data;
        return data;
      });
  }

  function rollRandomStory() {
    if (isRolling) return;

    const archive = window.STORY_ARCHIVE;
    if (archive && archive.length) {
      performRandomJump(archive);
      return;
    }

    // Archive is still loading; give visual feedback
    isRolling = true;
    const randomBtn = document.getElementById('random-story-btn');
    const prevHtml = randomBtn ? randomBtn.innerHTML : '';
    if (randomBtn) {
      randomBtn.innerHTML = '🎲 Rolling...';
      randomBtn.setAttribute('aria-busy', 'true');
    }

    ensureArchiveLoaded()
      .then(loadedArchive => {
        isRolling = false;
        if (randomBtn) {
          randomBtn.innerHTML = prevHtml;
          randomBtn.removeAttribute('aria-busy');
        }
        performRandomJump(loadedArchive);
      })
      .catch(err => {
        isRolling = false;
        if (randomBtn) {
          randomBtn.innerHTML = prevHtml;
          randomBtn.removeAttribute('aria-busy');
        }
        console.error('Could not load stories for random jump:', err);
      });
  }

  function performRandomJump(archive) {
    if (!archive || !archive.length) return;

    // Filter out current page if multiple stories exist
    const currentPath = window.location.pathname;
    let pool = archive;
    if (archive.length > 1) {
      const filtered = archive.filter(s => !currentPath.endsWith(s.u));
      if (filtered.length) {
        pool = filtered;
      }
    }

    const randomStory = pool[Math.floor(Math.random() * pool.length)];
    const rootPrefix = getRootPrefix();
    window.location.href = rootPrefix + randomStory.u;
  }

  // --- Archive Catalog Explorer (Home Page) ---
  const BATCH_SIZE = 48;
  let allStories = [];
  let filteredStories = [];
  let currentlyRenderedCount = 0;
  let activeYear = 'ALL';
  let activeQuery = '';
  let activeSort = 'longest'; // Default to longest first as requested!

  function initCatalog() {
    const grid = document.getElementById('story-grid');
    if (!grid) return;

    // Load data from global STORY_ARCHIVE
    if (window.STORY_ARCHIVE && window.STORY_ARCHIVE.length) {
      allStories = window.STORY_ARCHIVE;
      setupCatalogUI();
    } else {
      ensureArchiveLoaded()
        .then(data => {
          allStories = data;
          setupCatalogUI();
        })
        .catch(err => {
          console.warn('Could not load stories data, using pre-rendered HTML', err);
        });
    }
  }

  function setupCatalogUI() {
    const searchInput = document.getElementById('search-input');
    const searchClear = document.getElementById('search-clear');
    const sortSelect = document.getElementById('sort-select');
    const yearBtns = document.querySelectorAll('.year-btn');
    const loadMoreBtn = document.getElementById('load-more-btn');

    // Year buttons
    yearBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        yearBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeYear = btn.getAttribute('data-year');
        applyFilters();
      });
    });

    // Search input with debounce
    let searchDebounce = null;
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        clearTimeout(searchDebounce);
        searchDebounce = setTimeout(() => {
          activeQuery = e.target.value.trim().toLowerCase();
          if (searchClear) {
            searchClear.classList.toggle('visible', activeQuery.length > 0);
          }
          applyFilters();
        }, 150);
      });
    }

    if (searchClear && searchInput) {
      searchClear.addEventListener('click', () => {
        searchInput.value = '';
        activeQuery = '';
        searchClear.classList.remove('visible');
        applyFilters();
        searchInput.focus();
      });
    }

    // Sort select
    if (sortSelect) {
      sortSelect.value = activeSort;
      sortSelect.addEventListener('change', (e) => {
        activeSort = e.target.value;
        applyFilters();
      });
    }

    // Load More button
    if (loadMoreBtn) {
      loadMoreBtn.addEventListener('click', renderNextBatch);
    }

    // Initial filter apply
    applyFilters();
  }

  function applyFilters() {
    filteredStories = allStories.filter(story => {
      // Year filter
      if (activeYear !== 'ALL' && story.y !== activeYear) {
        return false;
      }

      // Query filter
      if (activeQuery) {
        const inTitle = story.t.toLowerCase().includes(activeQuery);
        const inDate = story.d.includes(activeQuery);
        const inExcerpt = story.e.toLowerCase().includes(activeQuery);
        const inCats = story.c && story.c.some(c => c.toLowerCase().includes(activeQuery));
        if (!inTitle && !inDate && !inExcerpt && !inCats) {
          return false;
        }
      }

      return true;
    });

    // Sort
    if (activeSort === 'longest') {
      filteredStories.sort((a, b) => b.w - a.w || a.d.localeCompare(b.d));
    } else if (activeSort === 'shortest') {
      filteredStories.sort((a, b) => a.w - b.w || a.d.localeCompare(b.d));
    } else if (activeSort === 'newest') {
      filteredStories.sort((a, b) => b.d.localeCompare(a.d) || a.t.localeCompare(b.t));
    } else if (activeSort === 'oldest') {
      filteredStories.sort((a, b) => a.d.localeCompare(b.d) || a.t.localeCompare(b.t));
    }

    // Update result status
    updateStatusDisplay();

    // Reset and render first batch
    const grid = document.getElementById('story-grid');
    if (grid) {
      grid.innerHTML = '';
      currentlyRenderedCount = 0;
      renderNextBatch();
    }
  }

  function updateStatusDisplay() {
    const statusCount = document.getElementById('results-count');
    const statusDesc = document.getElementById('results-desc');
    if (statusCount) {
      statusCount.textContent = filteredStories.length.toLocaleString();
    }
    if (statusDesc) {
      let desc = 'stories';
      if (activeYear !== 'ALL') desc += ` from ${activeYear}`;
      if (activeQuery) desc += ` matching "${activeQuery}"`;
      statusDesc.textContent = desc;
    }
  }

  function renderNextBatch() {
    const grid = document.getElementById('story-grid');
    const loadMoreWrap = document.getElementById('load-more-wrap');
    if (!grid) return;

    const rootPrefix = getRootPrefix();
    const nextBatch = filteredStories.slice(currentlyRenderedCount, currentlyRenderedCount + BATCH_SIZE);

    const frag = document.createDocumentFragment();

    nextBatch.forEach(story => {
      const card = document.createElement('article');
      card.className = 'story-card';

      const tagsHtml = story.c && story.c.length
        ? `<div class="tag-list">${story.c.slice(0, 3).map(c => `<span class="tag-badge">#${escapeHTML(c)}</span>`).join('')}</div>`
        : '';

      const storyUrl = rootPrefix + story.u;

      card.innerHTML = `
        <div>
          <div class="card-header-row">
            <span class="card-date">📅 ${story.d}</span>
            <span class="card-words-tag">📖 ${story.w.toLocaleString()} w · ~${story.m}m</span>
          </div>
          <h3 class="card-title">
            <a href="${storyUrl}">${escapeHTML(story.t)}</a>
          </h3>
          <p class="card-excerpt">${escapeHTML(story.e)}</p>
          ${tagsHtml}
        </div>
        <div class="card-footer">
          <div class="card-actions">
            <a href="${storyUrl}" class="btn-card-read">Read Story →</a>
            <button class="btn-card-preview" data-id="${story.id}" title="Quick Preview">⚡ Preview</button>
          </div>
        </div>
      `;

      // Preview click handler
      const previewBtn = card.querySelector('.btn-card-preview');
      if (previewBtn) {
        previewBtn.addEventListener('click', () => openModal(story));
      }

      frag.appendChild(card);
    });

    grid.appendChild(frag);
    currentlyRenderedCount += nextBatch.length;

    // Toggle Load More button
    if (loadMoreWrap) {
      loadMoreWrap.style.display = currentlyRenderedCount < filteredStories.length ? 'block' : 'none';
    }
  }

  // --- Global Keyboard Shortcuts ---
  function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Don't trigger shortcuts if typing in an input, textarea, or contentEditable
      const tag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
      if (tag === 'input' || tag === 'textarea' || (document.activeElement && document.activeElement.isContentEditable)) {
        return;
      }

      if (e.key === 'r' || e.key === 'R') {
        e.preventDefault();
        rollRandomStory();
      } else if (e.key === 't' || e.key === 'T') {
        e.preventDefault();
        cycleTheme();
      } else if (e.key === '/') {
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
          e.preventDefault();
          searchInput.focus();
        }
      }
    });
  }

  // --- Expose Global Helpers ---
  window.EWP = {
    openModal,
    closeModal,
    rollRandomStory,
    cycleTheme
  };

  // --- DOM Ready ---
  document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initFontSize();
    initReadingProgress();
    initModal();
    initRandomStory();
    initKeyboardShortcuts();
    initCatalog();
  });
})();
