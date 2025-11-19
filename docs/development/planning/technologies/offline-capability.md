# Offline Capability & Privacy-First Web Design

**Status:** Planning

---

## Overview

This document details how ragged maintains 100% offline capability and privacy-first principles in its web interface, ensuring no external dependencies or data leakage.

## Core Principle: Complete Local Operation

**Goal**: ragged's web interface must work perfectly without internet connectivity.

**Why**: Privacy, security, and reliability.

---

## Privacy-First Architecture

### No External Dependencies

#### What We Avoid

❌ **CDN-Hosted Libraries**
```html
<!-- NEVER DO THIS -->
<script src="https://cdn.jsdelivr.net/npm/library@1.0.0"></script>
<link href="https://fonts.googleapis.com/css?family=Roboto">
```

❌ **External APIs**
```javascript
// NEVER DO THIS
fetch('https://api.analytics.com/track', {
  method: 'POST',
  body: JSON.stringify({query: userQuery})  // ⚠️ PRIVACY VIOLATION
});
```

❌ **Third-Party Tracking**
```html
<!-- NEVER DO THIS -->
<script async src="https://www.googletagmanager.com/gtag/js"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
</script>
```

#### What We Do Instead

✅ **Bundle Everything Locally**
```
ragged/web/static/
├── js/
│   ├── bundle.js          # All JavaScript bundled
│   └── bundle.js.map      # Source maps (dev only)
├── css/
│   ├── bundle.css         # All styles bundled
│   └── fonts/             # Fonts bundled locally
│       └── inter-var.woff2
└── img/
    └── logo.svg           # Local assets only
```

✅ **Self-Hosted Everything**
```javascript
// vite.config.js (v0.5+)
export default {
  build: {
    rollupOptions: {
      external: [],  // Bundle EVERYTHING
      output: {
        manualChunks: undefined  // Single bundle for offline
      }
    }
  }
}
```

✅ **No Analytics, Ever**
```javascript
// Privacy-first: NO telemetry
// NO user tracking
// NO error reporting to external services
// ALL data stays local
```

---

## Progressive Web App (PWA) Implementation

### Service Worker Strategy (v1.0)

#### Basic Service Worker

```javascript
// static/service-worker.js
const CACHE_NAME = 'ragged-v1.0.0';
const OFFLINE_ASSETS = [
  '/',
  '/index.html',
  '/assets/bundle.js',
  '/assets/bundle.css',
  '/assets/fonts/inter-var.woff2',
  '/favicon.ico'
];

// Install: Cache all assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching offline assets');
        return cache.addAll(OFFLINE_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate: Clean old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch: Cache-first strategy
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // API requests: Network-first (fresher data)
  if (request.url.includes('/api/')) {
    event.respondWith(
      fetch(request)
        .catch(() => {
          return new Response(
            JSON.stringify({ error: 'Offline - API unavailable' }),
            { headers: { 'Content-Type': 'application/json' } }
          );
        })
    );
    return;
  }

  // Static assets: Cache-first (faster)
  event.respondWith(
    caches.match(request)
      .then((cached) => {
        if (cached) {
          console.log('[SW] Serving from cache:', request.url);
          return cached;
        }

        console.log('[SW] Fetching:', request.url);
        return fetch(request).then((response) => {
          // Cache successful responses
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, clone);
            });
          }
          return response;
        });
      })
  );
});
```

#### Register Service Worker

```javascript
// main.js
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then((registration) => {
        console.log('SW registered:', registration.scope);

        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;

          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New version available
              showUpdateNotification();
            }
          });
        });
      })
      .catch((error) => {
        console.error('SW registration failed:', error);
      });
  });
}

function showUpdateNotification() {
  // Notify user of update
  const banner = document.createElement('div');
  banner.className = 'update-banner';
  banner.innerHTML = `
    <span>New version available!</span>
    <button onclick="location.reload()">Update</button>
  `;
  document.body.appendChild(banner);
}
```

### Web App Manifest (v1.0)

```json
// static/manifest.json
{
  "name": "ragged - Local RAG System",
  "short_name": "ragged",
  "description": "Privacy-first local RAG for document Q&A",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#2563eb",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ],
  "categories": ["productivity", "utilities"],
  "screenshots": [
    {
      "src": "/screenshots/desktop.png",
      "sizes": "1280x720",
      "type": "image/png",
      "form_factor": "wide"
    },
    {
      "src": "/screenshots/mobile.png",
      "sizes": "750x1334",
      "type": "image/png",
      "form_factor": "narrow"
    }
  ],
  "prefer_related_applications": false
}
```

```html
<!-- index.html -->
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#2563eb">
<link rel="apple-touch-icon" href="/icons/icon-192x192.png">
```

---

## Local Storage Strategy

### What to Store Locally

✅ **User Preferences**
```javascript
// Store in localStorage (non-sensitive only)
const preferences = {
  theme: 'light',  // or 'dark'
  model: 'llama2',
  temperature: 0.7,
  topK: 5,
  collection: 'default'
};

localStorage.setItem('ragged_prefs', JSON.stringify(preferences));
```

✅ **Conversation History**
```javascript
// Store conversations locally
const conversations = [
  {
    id: 'conv-123',
    timestamp: Date.now(),
    messages: [
      { role: 'user', content: 'What is RAG?' },
      { role: 'assistant', content: 'RAG is...' }
    ]
  }
];

// Use IndexedDB for larger data
const db = await openDB('ragged-conversations', 1, {
  upgrade(db) {
    db.createObjectStore('conversations', {
      keyPath: 'id',
      autoIncrement: true
    });
  }
});

await db.add('conversations', conversation);
```

❌ **Never Store Externally**
- User queries
- Document contents
- API responses
- Personal data

### IndexedDB for Larger Data

```javascript
// db.js - IndexedDB wrapper
import { openDB } from 'idb';

export async function initDB() {
  return openDB('ragged', 1, {
    upgrade(db) {
      // Conversations
      if (!db.objectStoreNames.contains('conversations')) {
        const store = db.createObjectStore('conversations', {
          keyPath: 'id',
          autoIncrement: true
        });
        store.createIndex('timestamp', 'timestamp');
      }

      // Cached responses
      if (!db.objectStoreNames.contains('cache')) {
        const cache = db.createObjectStore('cache', {
          keyPath: 'queryHash'
        });
        cache.createIndex('timestamp', 'timestamp');
      }
    }
  });
}

export async function saveConversation(conversation) {
  const db = await initDB();
  return db.add('conversations', {
    ...conversation,
    timestamp: Date.now()
  });
}

export async function getRecentConversations(limit = 10) {
  const db = await initDB();
  const tx = db.transaction('conversations', 'readonly');
  const index = tx.store.index('timestamp');

  const conversations = [];
  let cursor = await index.openCursor(null, 'prev');

  while (cursor && conversations.length < limit) {
    conversations.push(cursor.value);
    cursor = await cursor.continue();
  }

  return conversations;
}
```

---

## Asset Bundling Strategy

### Svelte/Vite Configuration (v0.5+)

```javascript
// vite.config.js
import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],

  build: {
    // Inline all assets for offline capability
    assetsInlineLimit: 0,  // Don't inline (bundle separately)

    rollupOptions: {
      output: {
        // Predictable file names for caching
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name].[ext]'
      }
    },

    // Optimise for size (privacy: less data)
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,  // Remove console.logs
        drop_debugger: true
      }
    }
  },

  // No external dependencies
  resolve: {
    dedupe: ['svelte']
  }
});
```

### Font Bundling

```css
/* Bundle fonts locally - NO Google Fonts */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-var.woff2') format('woff2');
  font-weight: 100 900;
  font-display: swap;
}

body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}
```

---

## Network Detection

### Offline Detection

```javascript
// utils/network.js
export function isOnline() {
  return navigator.onLine;
}

export function watchNetworkStatus(callback) {
  window.addEventListener('online', () => {
    callback(true);
    console.log('Network: online');
  });

  window.addEventListener('offline', () => {
    callback(false);
    console.log('Network: offline');
  });

  // Initial state
  callback(navigator.onLine);
}
```

```svelte
<!-- NetworkStatus.svelte -->
<script>
  import { onMount } from 'svelte';
  import { watchNetworkStatus } from '$lib/utils/network';

  let online = true;

  onMount(() => {
    const unwatch = watchNetworkStatus((status) => {
      online = status;
    });

    return unwatch;
  });
</script>

{#if !online}
  <div class="offline-banner">
    ⚠️ No internet connection. ragged works offline, but some features may be limited.
  </div>
{/if}
```

---

## Privacy Checklist

### Before Release (v1.0)

- [ ] **No External Requests**
  - [ ] Check all fetch() calls (should be localhost only)
  - [ ] Verify no CDN dependencies
  - [ ] Confirm no external font loading

- [ ] **No Tracking**
  - [ ] No analytics scripts
  - [ ] No error reporting to external services
  - [ ] No telemetry

- [ ] **Data Privacy**
  - [ ] User data never sent externally
  - [ ] Conversations stored locally only
  - [ ] Clear data deletion functionality

- [ ] **Security**
  - [ ] HTTPS for production (localhost SSL)
  - [ ] Content Security Policy configured
  - [ ] No inline scripts (CSP compliance)

### Content Security Policy

```html
<!-- index.html -->
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self';
               script-src 'self';
               style-src 'self';
               img-src 'self' data:;
               font-src 'self';
               connect-src 'self';
               frame-ancestors 'none';
               base-uri 'self';
               form-action 'self';">
```

---

## Testing Offline Capability

### Manual Testing

```bash
# 1. Start ragged
python -m ragged.web

# 2. Load in browser
# http://localhost:8000

# 3. Disconnect internet (WiFi off)

# 4. Verify functionality:
# - UI loads from cache
# - Can query documents (server still local)
# - Can upload new documents
# - Everything works normally
```

### Automated Testing

```javascript
// tests/offline.test.js
import { test, expect } from '@playwright/test';

test('works offline', async ({ page, context }) => {
  // Visit while online
  await page.goto('http://localhost:8000');
  await page.waitForLoadState('networkidle');

  // Go offline
  await context.setOffline(true);

  // Reload page
  await page.reload();

  // Should still work (from cache)
  await expect(page.locator('h1')).toContainText('ragged');

  // Can interact with UI
  await page.fill('[data-testid="query-input"]', 'test');
  await page.click('[data-testid="send-button"]');

  // Note: API calls will fail (server requires connection)
  // But UI should handle gracefully
});
```

---

## Performance Optimisation

### Lazy Loading (Still Offline)

```javascript
// Lazy load heavy components
const GraphVisualization = () => import('./GraphVisualization.svelte');

// User navigates to graph view
if (showGraph) {
  const GraphView = await GraphVisualization();
  // Render graph
}
```

### Code Splitting

```javascript
// vite.config.js
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Split vendor code
          'vendor': ['svelte', 'svelte/internal'],

          // Split graph viz (heavy)
          'graph': ['d3', 'graphology']
        }
      }
    }
  }
}
```

### Compression

```python
# FastAPI compression
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

---

## Lighthouse Performance Targets (v1.0)

### PWA Checklist

| Metric | Target | Status |
|--------|--------|--------|
| **Performance** | > 90 | v1.0 |
| **Accessibility** | > 95 | v1.0 |
| **Best Practices** | > 95 | v1.0 |
| **SEO** | > 80 | v1.0 |
| **PWA** | ✅ All checks | v1.0 |

### PWA Requirements

- ✅ Registers a service worker
- ✅ Responds with 200 when offline
- ✅ Has a web app manifest
- ✅ Configured for a custom splash screen
- ✅ Sets an address bar theme color
- ✅ Content sized correctly for viewport
- ✅ Has a `<meta name="viewport">` tag
- ✅ Provides a valid apple-touch-icon

---

## Implementation Timeline

### v0.2: Basic Offline (Localhost Only)
- [ ] Bundle all assets locally
- [ ] No CDN dependencies
- [ ] Works on localhost without internet

### v0.3: Enhanced Offline
- [ ] Local storage for preferences
- [ ] IndexedDB for conversations
- [ ] Offline mode indicator

### v0.5: Svelte + Better Bundling
- [ ] Optimised asset bundling
- [ ] Font subsetting
- [ ] Code splitting for performance

### v1.0: Full PWA
- [ ] Service worker implementation
- [ ] Web app manifest
- [ ] Install prompt
- [ ] Offline-first architecture
- [ ] Lighthouse score > 90

---

## Privacy Guarantees

### What ragged Never Does

❌ Send queries to external services
❌ Track user behaviour
❌ Report errors externally
❌ Load resources from CDNs
❌ Make any external network requests
❌ Store data on external servers

### What ragged Always Does

✅ Process everything locally
✅ Store data on user's machine only
✅ Bundle all dependencies
✅ Work offline
✅ Respect user privacy
✅ Give users full control

---

## Conclusion

**ragged's offline capability is a core feature, not an afterthought.**

**Privacy guarantees**:
- 100% local processing
- No external dependencies
- Offline-first architecture
- User data never leaves their machine

**Implementation priorities**:
1. v0.2: No CDN dependencies
2. v0.3: Local storage
3. v1.0: Full PWA with service worker

**Next Steps**: See version-specific web UI implementation guides.
