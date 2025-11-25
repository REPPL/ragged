/// <reference types="@sveltejs/kit" />

declare global {
	namespace App {
		interface Error {
			message: string;
			code?: string;
		}
		interface Locals {
			user?: {
				id: string;
				email: string;
				name: string;
				role: string;
			};
		}
		interface PageData {
			user?: App.Locals['user'];
		}
		interface Platform {}
	}
}

export {};
