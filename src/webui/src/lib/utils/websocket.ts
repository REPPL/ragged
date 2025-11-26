/**
 * Secure WebSocket Utilities
 * ragged WebUI v0.7.4 - SEC-006
 *
 * Provides secure WebSocket connection handling with:
 * - Automatic WSS upgrade for HTTPS origins
 * - Reconnection with exponential backoff
 * - Message validation
 * - Connection state management
 */
import { writable, type Readable } from 'svelte/store';
import { getCsrfToken } from './security';

// ============================================
// TYPES
// ============================================

export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'reconnecting' | 'error';

export interface WebSocketMessage {
	type: string;
	payload?: unknown;
	timestamp?: number;
}

export interface WebSocketOptions {
	/** Reconnect on disconnect */
	autoReconnect?: boolean;
	/** Maximum reconnection attempts */
	maxReconnectAttempts?: number;
	/** Base delay between reconnection attempts (ms) */
	reconnectBaseDelay?: number;
	/** Maximum delay between reconnection attempts (ms) */
	reconnectMaxDelay?: number;
	/** Heartbeat interval (ms), 0 to disable */
	heartbeatInterval?: number;
	/** Connection timeout (ms) */
	connectionTimeout?: number;
	/** Message handlers */
	onMessage?: (message: WebSocketMessage) => void;
	onConnect?: () => void;
	onDisconnect?: (code: number, reason: string) => void;
	onError?: (error: Event) => void;
}

// ============================================
// SECURE WEBSOCKET CLASS
// ============================================

/**
 * Secure WebSocket wrapper with automatic reconnection and state management.
 */
export class SecureWebSocket {
	private ws: WebSocket | null = null;
	private url: string;
	private options: Required<WebSocketOptions>;
	private reconnectAttempts = 0;
	private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
	private heartbeatTimeout: ReturnType<typeof setTimeout> | null = null;
	private connectionTimeout: ReturnType<typeof setTimeout> | null = null;
	private manualClose = false;

	// State store
	private _state = writable<ConnectionState>('disconnected');
	public state: Readable<ConnectionState> = this._state;

	constructor(path: string, options: WebSocketOptions = {}) {
		this.url = this.buildSecureUrl(path);
		this.options = {
			autoReconnect: true,
			maxReconnectAttempts: 5,
			reconnectBaseDelay: 1000,
			reconnectMaxDelay: 30000,
			heartbeatInterval: 30000,
			connectionTimeout: 10000,
			onMessage: () => {},
			onConnect: () => {},
			onDisconnect: () => {},
			onError: () => {},
			...options
		};
	}

	/**
	 * Build a secure WebSocket URL.
	 * Automatically upgrades to WSS for HTTPS origins.
	 */
	private buildSecureUrl(path: string): string {
		if (typeof window === 'undefined') {
			return path;
		}

		const { protocol, host } = window.location;
		const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';

		// Ensure path starts with /
		const cleanPath = path.startsWith('/') ? path : `/${path}`;

		return `${wsProtocol}//${host}${cleanPath}`;
	}

	/**
	 * Connect to the WebSocket server.
	 */
	connect(): void {
		if (this.ws?.readyState === WebSocket.OPEN) {
			return;
		}

		this.manualClose = false;
		this._state.set('connecting');

		try {
			// Add CSRF token to URL if available
			const csrfToken = getCsrfToken();
			const urlWithToken = csrfToken
				? `${this.url}${this.url.includes('?') ? '&' : '?'}csrf=${encodeURIComponent(csrfToken)}`
				: this.url;

			this.ws = new WebSocket(urlWithToken);

			// Set connection timeout
			this.connectionTimeout = setTimeout(() => {
				if (this.ws?.readyState !== WebSocket.OPEN) {
					this.ws?.close();
					this._state.set('error');
					this.scheduleReconnect();
				}
			}, this.options.connectionTimeout);

			this.ws.onopen = () => {
				this.clearConnectionTimeout();
				this.reconnectAttempts = 0;
				this._state.set('connected');
				this.startHeartbeat();
				this.options.onConnect();
			};

			this.ws.onclose = (event) => {
				this.clearHeartbeat();
				this.clearConnectionTimeout();

				if (!this.manualClose) {
					this._state.set('disconnected');
					this.options.onDisconnect(event.code, event.reason);
					this.scheduleReconnect();
				}
			};

			this.ws.onerror = (event) => {
				this._state.set('error');
				this.options.onError(event);
			};

			this.ws.onmessage = (event) => {
				try {
					const message = this.parseMessage(event.data);
					if (message) {
						// Handle heartbeat responses
						if (message.type === 'pong') {
							return;
						}
						this.options.onMessage(message);
					}
				} catch (error) {
					console.error('Failed to parse WebSocket message:', error);
				}
			};
		} catch (error) {
			this._state.set('error');
			console.error('WebSocket connection error:', error);
			this.scheduleReconnect();
		}
	}

	/**
	 * Disconnect from the WebSocket server.
	 */
	disconnect(): void {
		this.manualClose = true;
		this.clearReconnectTimeout();
		this.clearHeartbeat();
		this.clearConnectionTimeout();

		if (this.ws) {
			this.ws.close(1000, 'Client disconnect');
			this.ws = null;
		}

		this._state.set('disconnected');
	}

	/**
	 * Send a message to the server.
	 */
	send(message: WebSocketMessage): boolean {
		if (this.ws?.readyState !== WebSocket.OPEN) {
			console.warn('WebSocket not connected, cannot send message');
			return false;
		}

		try {
			const payload = JSON.stringify({
				...message,
				timestamp: Date.now()
			});
			this.ws.send(payload);
			return true;
		} catch (error) {
			console.error('Failed to send WebSocket message:', error);
			return false;
		}
	}

	/**
	 * Parse and validate incoming message.
	 */
	private parseMessage(data: string): WebSocketMessage | null {
		try {
			const parsed = JSON.parse(data);

			// Validate message structure
			if (typeof parsed !== 'object' || !parsed.type) {
				console.warn('Invalid WebSocket message format');
				return null;
			}

			return {
				type: String(parsed.type),
				payload: parsed.payload,
				timestamp: typeof parsed.timestamp === 'number' ? parsed.timestamp : Date.now()
			};
		} catch {
			console.warn('Failed to parse WebSocket message as JSON');
			return null;
		}
	}

	/**
	 * Schedule reconnection with exponential backoff.
	 */
	private scheduleReconnect(): void {
		if (!this.options.autoReconnect || this.manualClose) {
			return;
		}

		if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
			console.error('Max reconnection attempts reached');
			this._state.set('error');
			return;
		}

		this._state.set('reconnecting');
		this.reconnectAttempts++;

		// Exponential backoff with jitter
		const delay = Math.min(
			this.options.reconnectBaseDelay * Math.pow(2, this.reconnectAttempts - 1) +
				Math.random() * 1000,
			this.options.reconnectMaxDelay
		);

		console.log(`Reconnecting in ${Math.round(delay)}ms (attempt ${this.reconnectAttempts})`);

		this.reconnectTimeout = setTimeout(() => {
			this.connect();
		}, delay);
	}

	/**
	 * Clear reconnection timeout.
	 */
	private clearReconnectTimeout(): void {
		if (this.reconnectTimeout) {
			clearTimeout(this.reconnectTimeout);
			this.reconnectTimeout = null;
		}
	}

	/**
	 * Start heartbeat to keep connection alive.
	 */
	private startHeartbeat(): void {
		if (this.options.heartbeatInterval <= 0) {
			return;
		}

		this.heartbeatTimeout = setInterval(() => {
			this.send({ type: 'ping' });
		}, this.options.heartbeatInterval);
	}

	/**
	 * Clear heartbeat interval.
	 */
	private clearHeartbeat(): void {
		if (this.heartbeatTimeout) {
			clearInterval(this.heartbeatTimeout);
			this.heartbeatTimeout = null;
		}
	}

	/**
	 * Clear connection timeout.
	 */
	private clearConnectionTimeout(): void {
		if (this.connectionTimeout) {
			clearTimeout(this.connectionTimeout);
			this.connectionTimeout = null;
		}
	}

	/**
	 * Get current connection state.
	 */
	getState(): ConnectionState {
		let currentState: ConnectionState = 'disconnected';
		this._state.subscribe((s) => (currentState = s))();
		return currentState;
	}

	/**
	 * Check if connected.
	 */
	isConnected(): boolean {
		return this.ws?.readyState === WebSocket.OPEN;
	}
}

/**
 * Create a secure WebSocket connection.
 */
export function createSecureWebSocket(
	path: string,
	options: WebSocketOptions = {}
): SecureWebSocket {
	return new SecureWebSocket(path, options);
}
