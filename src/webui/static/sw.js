/**
 * Service Worker
 * ragged WebUI v0.9.5
 *
 * Provides offline support and caching for PWA functionality
 */

const CACHE_NAME = 'ragged-cache-v1';
const STATIC_CACHE_NAME = 'ragged-static-v1';
const DYNAMIC_CACHE_NAME = 'ragged-dynamic-v1';

// Static assets to cache on install
const STATIC_ASSETS = [
	'/',
	'/manifest.json',
	'/favicon.png'
];

// Cache strategies
const CACHE_STRATEGIES = {
	// Network first, fall back to cache (for API calls)
	networkFirst: async (request) => {
		try {
			const networkResponse = await fetch(request);
			if (networkResponse.ok) {
				const cache = await caches.open(DYNAMIC_CACHE_NAME);
				cache.put(request, networkResponse.clone());
			}
			return networkResponse;
		} catch (error) {
			const cachedResponse = await caches.match(request);
			if (cachedResponse) {
				return cachedResponse;
			}
			throw error;
		}
	},

	// Cache first, fall back to network (for static assets)
	cacheFirst: async (request) => {
		const cachedResponse = await caches.match(request);
		if (cachedResponse) {
			return cachedResponse;
		}
		try {
			const networkResponse = await fetch(request);
			if (networkResponse.ok) {
				const cache = await caches.open(STATIC_CACHE_NAME);
				cache.put(request, networkResponse.clone());
			}
			return networkResponse;
		} catch (error) {
			return new Response('Offline', { status: 503 });
		}
	},

	// Stale while revalidate (for pages)
	staleWhileRevalidate: async (request) => {
		const cachedResponse = await caches.match(request);
		const fetchPromise = fetch(request)
			.then((networkResponse) => {
				if (networkResponse.ok) {
					const cache = caches.open(DYNAMIC_CACHE_NAME);
					cache.then((c) => c.put(request, networkResponse.clone()));
				}
				return networkResponse;
			})
			.catch(() => cachedResponse);

		return cachedResponse || fetchPromise;
	}
};

// Install event - cache static assets
self.addEventListener('install', (event) => {
	event.waitUntil(
		caches.open(STATIC_CACHE_NAME).then((cache) => {
			console.log('[SW] Caching static assets');
			return cache.addAll(STATIC_ASSETS);
		})
	);
	// Activate immediately
	self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches.keys().then((cacheNames) => {
			return Promise.all(
				cacheNames
					.filter(
						(name) =>
							name !== STATIC_CACHE_NAME &&
							name !== DYNAMIC_CACHE_NAME &&
							name.startsWith('ragged-')
					)
					.map((name) => {
						console.log('[SW] Deleting old cache:', name);
						return caches.delete(name);
					})
			);
		})
	);
	// Take control of all clients
	self.clients.claim();
});

// Fetch event - apply caching strategies
self.addEventListener('fetch', (event) => {
	const { request } = event;
	const url = new URL(request.url);

	// Skip non-GET requests
	if (request.method !== 'GET') {
		return;
	}

	// Skip cross-origin requests
	if (url.origin !== self.location.origin) {
		return;
	}

	// API requests - network first
	if (url.pathname.startsWith('/api/')) {
		event.respondWith(CACHE_STRATEGIES.networkFirst(request));
		return;
	}

	// Static assets - cache first
	if (
		url.pathname.match(/\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$/) ||
		url.pathname.startsWith('/icons/') ||
		url.pathname.startsWith('/_app/')
	) {
		event.respondWith(CACHE_STRATEGIES.cacheFirst(request));
		return;
	}

	// Pages - stale while revalidate
	event.respondWith(CACHE_STRATEGIES.staleWhileRevalidate(request));
});

// Handle messages from the app
self.addEventListener('message', (event) => {
	if (event.data === 'skipWaiting') {
		self.skipWaiting();
	}

	if (event.data === 'clearCache') {
		event.waitUntil(
			caches.keys().then((names) => {
				return Promise.all(names.map((name) => caches.delete(name)));
			})
		);
	}
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
	if (event.tag === 'sync-documents') {
		event.waitUntil(syncDocuments());
	}
});

async function syncDocuments() {
	// TODO: Implement document sync when back online
	console.log('[SW] Syncing documents...');
}

// Push notifications (for future use)
self.addEventListener('push', (event) => {
	if (!event.data) return;

	const data = event.data.json();
	const options = {
		body: data.body,
		icon: '/icons/icon-192x192.png',
		badge: '/icons/badge-72x72.png',
		vibrate: [100, 50, 100],
		data: data.url,
		actions: [
			{ action: 'open', title: 'Open' },
			{ action: 'dismiss', title: 'Dismiss' }
		]
	};

	event.waitUntil(self.registration.showNotification(data.title, options));
});

self.addEventListener('notificationclick', (event) => {
	event.notification.close();

	if (event.action === 'open' && event.notification.data) {
		event.waitUntil(clients.openWindow(event.notification.data));
	}
});
