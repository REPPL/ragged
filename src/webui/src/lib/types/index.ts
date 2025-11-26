/**
 * TypeScript type definitions for ragged WebUI
 * v0.7.3
 */

// ============================================
// API TYPES
// ============================================

export interface QueryRequest {
	query: string;
	collection?: string;
	top_k?: number;
	retrieval_method?: 'vector' | 'bm25' | 'hybrid';
	stream?: boolean;
}

export interface QueryResponse {
	answer: string;
	sources: Source[];
	retrieval_method: string;
	total_time: number;
}

export interface Source {
	id: string;
	filename: string;
	chunk_index: number;
	score: number;
	excerpt: string;
	page?: number;
}

export interface UploadResponse {
	filename: string;
	size: number;
	status: 'success' | 'error';
	message: string;
}

export interface HealthResponse {
	status: 'healthy' | 'degraded' | 'unhealthy';
	version: string;
	services: Record<string, string>;
}

export interface ErrorResponse {
	detail: string;
	code?: string;
}

// ============================================
// DOCUMENT TYPES
// ============================================

export interface Document {
	id: string;
	filename: string;
	path: string;
	size: number;
	type: DocumentType;
	chunks: number;
	chunk_count: number;
	status: 'ready' | 'processing' | 'error' | 'pending';
	collection?: string;
	tags: string[];
	metadata: DocumentMetadata;
	created_at: string;
	updated_at: string;
}

export type DocumentType = 'pdf' | 'markdown' | 'text' | 'html' | 'code' | 'unknown';

export interface DocumentMetadata {
	title?: string;
	author?: string;
	pages?: number;
	language?: string;
	domain?: DocumentDomain;
	[key: string]: unknown;
}

export type DocumentDomain = 'technical' | 'academic' | 'research' | 'general';

export interface DocumentFilters {
	collection: string | null;
	tags: string[];
	types: DocumentType[];
	dateRange: DateRange | null;
	search: string;
}

export interface DateRange {
	start: Date;
	end: Date;
}

// ============================================
// COLLECTION TYPES
// ============================================

export interface Collection {
	id: string;
	name: string;
	description?: string;
	document_count: number;
	chunk_count: number;
	is_default: boolean;
	icon?: string;
	colour?: string;
	created_at: string;
	updated_at: string;
}

// ============================================
// QUERY HISTORY TYPES
// ============================================

export interface QueryHistoryItem {
	id: string;
	query: string;
	answer?: string;
	source_count: number;
	status: 'completed' | 'failed' | 'cancelled';
	duration?: number;
	collection?: string;
	filters?: DocumentFilters;
	starred: boolean;
	created_at: string;
}

// ============================================
// QUERY MODE TYPES
// ============================================

export type QueryMode = 'text' | 'image' | 'hybrid';
export type RetrievalMethod = 'vector' | 'bm25' | 'hybrid';

// ============================================
// ANALYTICS TYPES
// ============================================

export interface PerformanceMetrics {
	period_start: string;
	period_end: string;
	query_count: number;
	avg_latency_ms: number;
	latency_p50: number;
	latency_p95: number;
	latency_p99: number;
	error_count: number;
	cache_hit_rate: number;
}

export interface StorageMetrics {
	total_size_bytes: number;
	total_size_mb: number;
	total_size_gb: number;
	categories: StorageCategory[];
	recommendations: string[];
	growth_projection?: GrowthProjection;
}

export interface StorageCategory {
	name: string;
	description: string;
	path: string;
	size_bytes: number;
	size_mb: number;
	file_count: number;
	percentage: number;
}

export interface GrowthProjection {
	daily_growth_bytes: number;
	weekly_growth_bytes: number;
	monthly_growth_bytes: number;
	days_until_full: number | null;
}

export interface SimilarityData {
	nodes: SimilarityNode[];
	edges: SimilarityEdge[];
	clusters: SimilarityCluster[];
}

export interface SimilarityNode {
	id: string;
	title: string;
	doc_type?: string;
	cluster_id: number;
}

export interface SimilarityEdge {
	source: string;
	target: string;
	similarity: number;
}

export interface SimilarityCluster {
	cluster_id: number;
	document_ids: string[];
	size: number;
	keywords?: string[];
}

// ============================================
// USER & AUTH TYPES
// ============================================

export interface User {
	id: string;
	email: string;
	name: string;
	role: UserRole;
	avatar?: string;
	created_at: string;
}

export type UserRole = 'admin' | 'editor' | 'viewer' | 'guest';

export interface AuthState {
	user: User | null;
	isAuthenticated: boolean;
	isLoading: boolean;
	error: string | null;
}

export interface LoginCredentials {
	email: string;
	password: string;
	remember?: boolean;
}

export interface RegisterData {
	name: string;
	email: string;
	password: string;
	confirm_password: string;
}

// ============================================
// SETTINGS TYPES
// ============================================

export interface UserSettings {
	general: GeneralSettings;
	query: QuerySettings;
	documents: DocumentSettings;
	privacy: PrivacySettings;
	advanced: AdvancedSettings;
}

export interface GeneralSettings {
	theme: 'light' | 'dark' | 'system';
	sidebarCollapsed: boolean;
	animations: boolean;
}

export interface QuerySettings {
	defaultTopK: number;
	defaultRetrievalMethod: 'vector' | 'bm25' | 'hybrid';
	autoSubmitOnEnter: boolean;
	showAdvancedOptions: boolean;
	streamResponses: boolean;
}

export interface DocumentSettings {
	defaultCollection: string | null;
	autoRefreshInterval: number;
	chunkPreviewLength: number;
}

export interface PrivacySettings {
	enableQueryHistory: boolean;
	enableTelemetry: boolean;
}

export interface AdvancedSettings {
	apiUrl: string;
	llmModel: string;
	embeddingModel: string;
	debugMode: boolean;
}

// ============================================
// UI STATE TYPES
// ============================================

export interface ToastMessage {
	id: string;
	type: 'success' | 'error' | 'warning' | 'info';
	title: string;
	message?: string;
	duration?: number;
}

export interface ModalState {
	isOpen: boolean;
	component: string | null;
	props?: Record<string, unknown>;
}

export interface CommandPaletteItem {
	id: string;
	label: string;
	description?: string;
	icon?: string;
	shortcut?: string;
	action: () => void;
	category?: string;
}

// ============================================
// COMPONENT PROP TYPES
// ============================================

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'success';
export type ButtonSize = 'sm' | 'md' | 'lg';

export type InputType = 'text' | 'email' | 'password' | 'search' | 'number' | 'url';

export type BadgeVariant = 'default' | 'primary' | 'success' | 'warning' | 'danger';

export type TabOrientation = 'horizontal' | 'vertical';

// ============================================
// UTILITY TYPES
// ============================================

export type SortDirection = 'asc' | 'desc';

export interface SortConfig<T> {
	key: keyof T;
	direction: SortDirection;
}

export interface PaginationConfig {
	page: number;
	pageSize: number;
	total: number;
}

export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

export interface AsyncState<T> {
	data: T | null;
	loading: boolean;
	error: string | null;
}
