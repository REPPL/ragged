import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	plugins: [sveltekit()],
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}'],
		environment: 'jsdom',
		globals: true,
		setupFiles: ['src/tests/setup.ts'],
		alias: {
			'$lib': '/src/lib',
			'$stores': '/src/lib/stores',
			'$api': '/src/lib/api',
			'$types': '/src/lib/types',
			'$components': '/src/lib/components',
			'$utils': '/src/lib/utils'
		},
		coverage: {
			provider: 'v8',
			reporter: ['text', 'json', 'html', 'lcov'],
			reportsDirectory: './coverage',
			exclude: [
				'node_modules/',
				'src/**/*.d.ts',
				'**/*.config.*',
				'src/tests/**',
				'tests/**',
				'.svelte-kit/**'
			],
			include: ['src/lib/**/*.{ts,svelte}'],
			// Quality gates - fail if coverage drops below thresholds
			thresholds: {
				statements: 70,
				branches: 65,
				functions: 70,
				lines: 70
			}
		}
	},
	server: {
		port: 5173,
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true
			}
		}
	},
	build: {
		target: 'esnext',
		minify: 'esbuild',
		sourcemap: true,
		rollupOptions: {
			output: {
				manualChunks: {
					vendor: ['chart.js', 'd3', 'dompurify']
				}
			}
		}
	}
});
