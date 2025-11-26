/**
 * Load Testing Scenarios
 * ragged WebUI v0.7.5 - QA-007
 *
 * k6 load testing scenarios for stress testing the WebUI and API.
 *
 * Run with: k6 run tests/load/scenarios.js
 */
import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const queryDuration = new Trend('query_duration');
const uploadDuration = new Trend('upload_duration');
const documentsLoaded = new Counter('documents_loaded');

// Test configuration
export const options = {
	// Stages for ramping up and down
	stages: [
		{ duration: '30s', target: 10 },   // Ramp up to 10 users
		{ duration: '1m', target: 50 },    // Ramp up to 50 users
		{ duration: '2m', target: 100 },   // Stay at 100 users
		{ duration: '30s', target: 50 },   // Ramp down to 50 users
		{ duration: '30s', target: 0 },    // Ramp down to 0 users
	],

	// Thresholds for pass/fail
	thresholds: {
		http_req_duration: ['p(95)<2000'], // 95% of requests under 2s
		http_req_failed: ['rate<0.01'],     // Error rate under 1%
		errors: ['rate<0.05'],              // Custom error rate under 5%
		query_duration: ['p(95)<3000'],     // 95% of queries under 3s
	},
};

// Base URL - configure for your environment
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Helper function for authenticated requests
function authHeaders() {
	return {
		'Content-Type': 'application/json',
		'Authorization': `Bearer ${__ENV.AUTH_TOKEN || 'test-token'}`,
	};
}

// Main test function
export default function () {
	group('Health Check', () => {
		const healthRes = http.get(`${BASE_URL}/api/health`);
		check(healthRes, {
			'health check status 200': (r) => r.status === 200,
			'health check has status': (r) => JSON.parse(r.body).status !== undefined,
		});
		errorRate.add(healthRes.status !== 200);
	});

	sleep(1);

	group('Document List', () => {
		const docsRes = http.get(`${BASE_URL}/api/documents`, {
			headers: authHeaders(),
		});
		check(docsRes, {
			'documents status 200': (r) => r.status === 200,
			'documents is array': (r) => Array.isArray(JSON.parse(r.body)),
		});
		documentsLoaded.add(1);
		errorRate.add(docsRes.status !== 200);
	});

	sleep(0.5);

	group('Query Execution', () => {
		const startTime = new Date();

		const queryRes = http.post(
			`${BASE_URL}/api/query`,
			JSON.stringify({
				query: 'What is retrieval augmented generation?',
				top_k: 5,
				retrieval_method: 'hybrid',
			}),
			{
				headers: authHeaders(),
				timeout: '30s',
			}
		);

		const duration = new Date() - startTime;
		queryDuration.add(duration);

		check(queryRes, {
			'query status 200': (r) => r.status === 200,
			'query has answer': (r) => {
				try {
					return JSON.parse(r.body).answer !== undefined;
				} catch {
					return false;
				}
			},
			'query under 5s': (r) => r.timings.duration < 5000,
		});
		errorRate.add(queryRes.status !== 200);
	});

	sleep(1);

	group('Collections', () => {
		const colRes = http.get(`${BASE_URL}/api/collections`, {
			headers: authHeaders(),
		});
		check(colRes, {
			'collections status 200': (r) => r.status === 200,
		});
		errorRate.add(colRes.status !== 200);
	});

	sleep(0.5);

	group('History', () => {
		const historyRes = http.get(`${BASE_URL}/api/history`, {
			headers: authHeaders(),
		});
		check(historyRes, {
			'history status 200': (r) => r.status === 200,
		});
		errorRate.add(historyRes.status !== 200);
	});

	sleep(0.5);

	group('Analytics', () => {
		const perfRes = http.get(`${BASE_URL}/api/analytics/performance`, {
			headers: authHeaders(),
		});
		check(perfRes, {
			'performance status 200': (r) => r.status === 200,
		});

		const storageRes = http.get(`${BASE_URL}/api/analytics/storage`, {
			headers: authHeaders(),
		});
		check(storageRes, {
			'storage status 200': (r) => r.status === 200,
		});
		errorRate.add(perfRes.status !== 200 || storageRes.status !== 200);
	});

	// Random sleep between requests to simulate real user behaviour
	sleep(Math.random() * 2 + 1);
}

// Stress test scenario
export function stressTest() {
	// More aggressive load
	const stages = [
		{ duration: '1m', target: 100 },
		{ duration: '2m', target: 200 },
		{ duration: '1m', target: 300 },
		{ duration: '2m', target: 300 },
		{ duration: '1m', target: 0 },
	];
}

// Spike test scenario
export function spikeTest() {
	group('Spike Test', () => {
		// Simulate sudden spike in traffic
		for (let i = 0; i < 10; i++) {
			http.get(`${BASE_URL}/api/health`);
		}
	});
}

// Soak test scenario (run separately with: k6 run --duration 1h tests/load/scenarios.js)
export function soakTest() {
	const options = {
		stages: [
			{ duration: '5m', target: 50 },
			{ duration: '50m', target: 50 },
			{ duration: '5m', target: 0 },
		],
	};
}

// Handle test lifecycle events
export function setup() {
	console.log('Starting load test...');
	console.log(`Target URL: ${BASE_URL}`);

	// Verify API is accessible
	const res = http.get(`${BASE_URL}/api/health`);
	if (res.status !== 200) {
		throw new Error(`API not accessible: ${res.status}`);
	}

	return { startTime: new Date().toISOString() };
}

export function teardown(data) {
	console.log('Load test completed.');
	console.log(`Started: ${data.startTime}`);
	console.log(`Ended: ${new Date().toISOString()}`);
}
