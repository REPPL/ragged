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
			'$components': '/src/lib/components'
		},
		coverage: {
			provider: 'v8',
			reporter: ['text', 'json', 'html'],
			exclude: ['node_modules/', 'src/**/*.d.ts', '**/*.config.*']
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
		sourcemap: true
	}
});
