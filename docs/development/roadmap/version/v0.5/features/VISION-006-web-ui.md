# VISION-006: Web UI for Multi-Modal RAG

**Feature:** Interactive Web Interface
**Category:** User Interface
**Estimated Effort:** 24-32 hours
**Dependencies:** All VISION-001 through VISION-005
**Status:** Planned

---

## Overview

Create a modern web interface for ragged that makes multi-modal RAG accessible without command-line expertise. Built with Gradio for rapid development, this UI provides document upload, visual querying, result exploration, and GPU monitoring.

**Design Goals:**
1. **Accessibility:** No technical knowledge required
2. **Speed:** Fast iterations on queries and document management
3. **Visual:** Leverage vision capabilities with image previews
4. **Feedback:** Real-time progress and GPU statistics
5. **Privacy:** Runs locally, no external services

**Technology Choice:** Gradio
- Rapid prototyping with Python-only code
- Built-in components for file upload, image display, sliders
- Automatic API generation (REST + WebSocket)
- Easy deployment (local or cloud)
- MIT license (compatible with ragged's GPL-3.0)

---

## Architecture

### UI Structure

```
Web Interface (Gradio)
├── Document Management Tab
│   ├── Upload PDF
│   ├── Enable vision toggle
│   ├── Ingestion progress
│   └── Document list
│
├── Query Tab
│   ├── Text query input
│   ├── Image query upload
│   ├── Hybrid mode toggle
│   ├── Weight sliders
│   └── Results pane
│
├── Results Explorer
│   ├── Result cards (ranked)
│   ├── Page thumbnails (vision)
│   ├── Text snippets
│   └── Metadata display
│
└── System Dashboard
    ├── GPU information
    ├── Memory usage chart
    ├── Storage statistics
    └── Performance metrics
```

### Component Flow

```
User uploads PDF
    ↓
[Upload Handler]
    ├─ Save to temporary directory
    ├─ Trigger ingestion (with/without vision)
    └─ Update progress bar
    ↓
[Document Processor]
    ├─ Generate text embeddings
    ├─ Generate vision embeddings (if enabled)
    └─ Store in DualEmbeddingStore
    ↓
[Document List Update]
    └─ Show newly ingested document

User enters query
    ↓
[Query Handler]
    ├─ Detect query type (text/image/hybrid)
    ├─ Process query via VisionRetriever
    └─ Return ranked results
    ↓
[Results Renderer]
    ├─ Display result cards
    ├─ Show page thumbnails (if vision)
    └─ Render text snippets
```

---

## Implementation Plan

### Phase 1: Core UI Framework (6-8 hours)

#### Session 1.1: Gradio Application Structure (3-4h)

**Task:** Create main Gradio application with tab structure

**Implementation:**

```python
# src/ui/app.py

import gradio as gr
from pathlib import Path
from typing import Optional, List, Tuple
from loguru import logger

from ragged.storage.dual_store import DualEmbeddingStore
from ragged.embeddings.text_embedder import TextEmbedder
from ragged.embeddings.colpali_embedder import ColPaliEmbedder
from ragged.retrieval.vision_retriever import VisionRetriever
from ragged.ingestion.processor import DocumentProcessor
from ragged.gpu.device_manager import DeviceManager


class RaggedWebUI:
    """
    Ragged web interface for multi-modal RAG.

    Provides:
    - Document upload and ingestion
    - Multi-modal querying
    - Results exploration
    - System monitoring
    """

    def __init__(
        self,
        collection_name: str = "documents",
        enable_vision: bool = True,
        device: Optional[str] = None
    ):
        """
        Initialise web UI.

        Args:
            collection_name: ChromaDB collection name
            enable_vision: Whether to enable vision embeddings
            device: GPU device hint (None = auto-detect)
        """
        self.collection_name = collection_name
        self.enable_vision = enable_vision

        # Initialise storage
        self.store = DualEmbeddingStore(collection_name=collection_name)

        # Initialise embedders
        self.text_embedder = TextEmbedder()

        self.vision_embedder = None
        if enable_vision:
            try:
                self.vision_embedder = ColPaliEmbedder(device=device)
                logger.info(f"Vision embedder initialised: {self.vision_embedder.device_info}")
            except RuntimeError as e:
                logger.warning(f"Vision embedder failed to initialise: {e}")
                self.enable_vision = False

        # Initialise retriever
        self.retriever = VisionRetriever(
            store=self.store,
            query_processor=None  # Will use defaults
        )

        # Initialise processor
        self.processor = DocumentProcessor(
            text_embedder=self.text_embedder,
            vision_embedder=self.vision_embedder,
            store=self.store
        )

        # Device manager for GPU stats
        self.device_manager = DeviceManager()

        logger.info("RaggedWebUI initialised")

    def build_interface(self) -> gr.Blocks:
        """
        Build Gradio interface.

        Returns:
            Gradio Blocks application
        """
        with gr.Blocks(
            title="Ragged - Multi-Modal RAG",
            theme=gr.themes.Soft()
        ) as app:
            gr.Markdown("# Ragged: Multi-Modal RAG System")
            gr.Markdown(
                "Privacy-first document retrieval with vision understanding. "
                "Upload PDFs, query with text or images, and explore results visually."
            )

            with gr.Tabs():
                # Tab 1: Document Management
                with gr.Tab("📄 Documents"):
                    self._build_document_tab()

                # Tab 2: Query
                with gr.Tab("🔍 Query"):
                    self._build_query_tab()

                # Tab 3: System Dashboard
                with gr.Tab("⚙️ System"):
                    self._build_system_tab()

        return app

    def _build_document_tab(self):
        """Build document management tab."""
        gr.Markdown("## Upload Documents")

        with gr.Row():
            with gr.Column(scale=2):
                pdf_input = gr.File(
                    label="Upload PDF",
                    file_types=[".pdf"],
                    type="filepath"
                )

                vision_toggle = gr.Checkbox(
                    label="Enable vision embeddings (requires GPU)",
                    value=self.enable_vision,
                    interactive=self.enable_vision
                )

                upload_button = gr.Button("Ingest Document", variant="primary")

            with gr.Column(scale=1):
                progress_output = gr.Textbox(
                    label="Status",
                    lines=5,
                    interactive=False
                )

        gr.Markdown("## Document Collection")

        document_list = gr.Dataframe(
            headers=["Document ID", "Text Embeddings", "Vision Embeddings"],
            datatype=["str", "number", "number"],
            label="Ingested Documents"
        )

        refresh_button = gr.Button("Refresh List")

        # Event handlers
        upload_button.click(
            fn=self.handle_document_upload,
            inputs=[pdf_input, vision_toggle],
            outputs=[progress_output, document_list]
        )

        refresh_button.click(
            fn=self.get_document_list,
            outputs=document_list
        )

        # Load initial document list
        app.load(fn=self.get_document_list, outputs=document_list)

    def _build_query_tab(self):
        """Build query tab."""
        gr.Markdown("## Multi-Modal Query")

        with gr.Row():
            with gr.Column(scale=1):
                # Query inputs
                query_text = gr.Textbox(
                    label="Text Query",
                    placeholder="Enter your question or search terms...",
                    lines=2
                )

                query_image = gr.Image(
                    label="Image Query (optional)",
                    type="filepath",
                    sources=["upload"]
                )

                with gr.Accordion("Advanced Options", open=False):
                    num_results = gr.Slider(
                        minimum=1,
                        maximum=50,
                        value=10,
                        step=1,
                        label="Number of results"
                    )

                    text_weight = gr.Slider(
                        minimum=0.0,
                        maximum=1.0,
                        value=0.5,
                        step=0.1,
                        label="Text weight (for hybrid queries)"
                    )

                    vision_weight = gr.Slider(
                        minimum=0.0,
                        maximum=1.0,
                        value=0.5,
                        step=0.1,
                        label="Vision weight (for hybrid queries)"
                    )

                    boost_diagrams = gr.Checkbox(
                        label="Boost results with diagrams",
                        value=False
                    )

                    boost_tables = gr.Checkbox(
                        label="Boost results with tables",
                        value=False
                    )

                query_button = gr.Button("Search", variant="primary")

            with gr.Column(scale=2):
                # Results display
                results_output = gr.HTML(label="Results")

        # Event handler
        query_button.click(
            fn=self.handle_query,
            inputs=[
                query_text,
                query_image,
                num_results,
                text_weight,
                vision_weight,
                boost_diagrams,
                boost_tables
            ],
            outputs=results_output
        )

    def _build_system_tab(self):
        """Build system dashboard tab."""
        gr.Markdown("## System Information")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### GPU Devices")
                gpu_info = gr.Textbox(
                    label="Available Devices",
                    lines=10,
                    interactive=False
                )

            with gr.Column():
                gr.Markdown("### Storage Statistics")
                storage_stats = gr.Textbox(
                    label="Collection Statistics",
                    lines=10,
                    interactive=False
                )

        refresh_system_button = gr.Button("Refresh System Info")

        # Event handler
        refresh_system_button.click(
            fn=self.get_system_info,
            outputs=[gpu_info, storage_stats]
        )

        # Load initial system info
        app.load(fn=self.get_system_info, outputs=[gpu_info, storage_stats])

    # Event Handlers

    def handle_document_upload(
        self,
        pdf_path: Optional[str],
        enable_vision: bool
    ) -> Tuple[str, List]:
        """
        Handle document upload and ingestion.

        Args:
            pdf_path: Path to uploaded PDF
            enable_vision: Whether to generate vision embeddings

        Returns:
            Tuple of (status_message, updated_document_list)
        """
        if pdf_path is None:
            return "⚠️ Please upload a PDF file.", self.get_document_list()

        try:
            logger.info(f"Ingesting document: {pdf_path}")

            # Process document
            doc_id = self.processor.process_document(
                Path(pdf_path),
                enable_vision=enable_vision and self.enable_vision
            )

            # Get statistics
            stats = self.store.get_by_document(doc_id)
            text_count = sum(
                1 for m in stats["metadatas"] if m["embedding_type"] == "text"
            )
            vision_count = sum(
                1 for m in stats["metadatas"] if m["embedding_type"] == "vision"
            )

            status = (
                f"✅ Document ingested successfully!\n\n"
                f"Document ID: {doc_id}\n"
                f"Text embeddings: {text_count}\n"
                f"Vision embeddings: {vision_count}"
            )

            return status, self.get_document_list()

        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            return f"❌ Ingestion failed: {str(e)}", self.get_document_list()

    def handle_query(
        self,
        text: str,
        image_path: Optional[str],
        num_results: int,
        text_weight: float,
        vision_weight: float,
        boost_diagrams: bool,
        boost_tables: bool
    ) -> str:
        """
        Handle query execution.

        Args:
            text: Text query string
            image_path: Path to query image (optional)
            num_results: Number of results to return
            text_weight: Weight for text scores
            vision_weight: Weight for vision scores
            boost_diagrams: Boost diagram results
            boost_tables: Boost table results

        Returns:
            HTML-formatted results
        """
        if not text and not image_path:
            return "<p>⚠️ Please enter a text query or upload an image.</p>"

        try:
            # Execute query
            response = self.retriever.query(
                text=text if text else None,
                image=Path(image_path) if image_path else None,
                n_results=num_results,
                text_weight=text_weight,
                vision_weight=vision_weight,
                boost_diagrams=boost_diagrams,
                boost_tables=boost_tables
            )

            # Format results as HTML
            html = self._format_results_html(response)

            return html

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return f"<p>❌ Query failed: {str(e)}</p>"

    def get_document_list(self) -> List[List]:
        """
        Get list of ingested documents.

        Returns:
            List of document rows for Dataframe
        """
        all_results = self.store.collection.get()

        if not all_results["ids"]:
            return []

        # Group by document ID
        doc_stats = {}
        for metadata in all_results["metadatas"]:
            doc_id = metadata["document_id"]

            if doc_id not in doc_stats:
                doc_stats[doc_id] = {"text": 0, "vision": 0}

            if metadata["embedding_type"] == "text":
                doc_stats[doc_id]["text"] += 1
            else:
                doc_stats[doc_id]["vision"] += 1

        # Format as rows
        rows = [
            [doc_id, stats["text"], stats["vision"]]
            for doc_id, stats in doc_stats.items()
        ]

        return rows

    def get_system_info(self) -> Tuple[str, str]:
        """
        Get system information.

        Returns:
            Tuple of (gpu_info, storage_stats)
        """
        # GPU information
        gpu_lines = []
        for i, device in enumerate(self.device_manager._available_devices):
            gpu_lines.append(f"{i + 1}. {device}")

            if device.total_memory:
                mem_gb = device.total_memory / (1024**3)
                gpu_lines.append(f"   Memory: {mem_gb:.2f} GB")

        gpu_info = "\n".join(gpu_lines) if gpu_lines else "No GPU devices found."

        # Storage statistics
        all_results = self.store.collection.get()

        if not all_results["ids"]:
            storage_stats = "Collection is empty."
        else:
            text_count = sum(
                1 for m in all_results["metadatas"] if m.get("embedding_type") == "text"
            )
            vision_count = sum(
                1 for m in all_results["metadatas"] if m.get("embedding_type") == "vision"
            )
            unique_docs = len(set(m["document_id"] for m in all_results["metadatas"]))

            storage_stats = (
                f"Collection: {self.collection_name}\n"
                f"Documents: {unique_docs}\n"
                f"Text embeddings: {text_count}\n"
                f"Vision embeddings: {vision_count}\n"
                f"Total embeddings: {len(all_results['ids'])}"
            )

        return gpu_info, storage_stats

    def _format_results_html(self, response) -> str:
        """
        Format query results as HTML.

        Args:
            response: RetrievalResponse object

        Returns:
            HTML string
        """
        html_parts = []

        html_parts.append(
            f"<div style='margin-bottom: 20px;'>"
            f"<strong>Found {response.total_results} results "
            f"in {response.execution_time_ms:.2f}ms</strong>"
            f"</div>"
        )

        for result in response.results:
            # Result card
            card_html = f"""
            <div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px;">
                <div style="font-weight: bold; font-size: 16px; margin-bottom: 5px;">
                    {result.rank}. {result.document_id}
                </div>
                <div style="color: #666; margin-bottom: 10px;">
                    Score: {result.score:.4f} | Type: {result.embedding_type}
                </div>
            """

            # Add type-specific metadata
            if result.embedding_type == "text":
                text_content = result.metadata.get("text_content", "")
                if text_content:
                    preview = text_content[:200] + "..." if len(text_content) > 200 else text_content
                    card_html += f"<div style='font-style: italic;'>\"{preview}\"</div>"

            elif result.embedding_type == "vision":
                page_num = result.metadata.get("page_number", "N/A")
                has_diagrams = result.metadata.get("has_diagrams", False)
                has_tables = result.metadata.get("has_tables", False)

                visual_tags = []
                if has_diagrams:
                    visual_tags.append("📊 Diagrams")
                if has_tables:
                    visual_tags.append("📋 Tables")

                card_html += f"<div>Page: {page_num}"
                if visual_tags:
                    card_html += f" | {' | '.join(visual_tags)}"
                card_html += "</div>"

            card_html += "</div>"
            html_parts.append(card_html)

        return "".join(html_parts)

    def launch(
        self,
        server_name: str = "127.0.0.1",
        server_port: int = 7860,
        share: bool = False
    ):
        """
        Launch web interface.

        Args:
            server_name: Server hostname
            server_port: Server port
            share: Whether to create public link (Gradio sharing)
        """
        app = self.build_interface()

        logger.info(f"Launching web UI on {server_name}:{server_port}")

        app.launch(
            server_name=server_name,
            server_port=server_port,
            share=share
        )


def main():
    """Main entry point for web UI."""
    import argparse

    parser = argparse.ArgumentParser(description="Ragged Web UI")
    parser.add_argument(
        "--collection",
        default="documents",
        help="ChromaDB collection name"
    )
    parser.add_argument(
        "--no-vision",
        action="store_true",
        help="Disable vision embeddings"
    )
    parser.add_argument(
        "--device",
        default=None,
        help="GPU device (cuda, mps, cpu, or cuda:N)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Server port"
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create public Gradio link"
    )

    args = parser.parse_args()

    # Create and launch UI
    ui = RaggedWebUI(
        collection_name=args.collection,
        enable_vision=not args.no_vision,
        device=args.device
    )

    ui.launch(
        server_port=args.port,
        share=args.share
    )


if __name__ == "__main__":
    main()
```

**Deliverables:**
- `src/ui/app.py` (~500 lines)
- Tab-based interface (Documents, Query, System)
- Event handlers for all interactions
- HTML result formatting

**Time:** 3-4 hours

---

#### Session 1.2: Enhanced Results Display (3-4h)

**Task:** Improve results rendering with thumbnails and rich metadata

**Implementation:**

```python
# src/ui/results_renderer.py

from typing import List, Optional
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image

from ragged.retrieval.vision_retriever import RetrievalResult


class ResultsRenderer:
    """
    Render query results with rich formatting.

    Features:
    - Page thumbnails for vision results
    - Text snippet highlighting
    - Metadata badges
    - Responsive cards
    """

    def __init__(self, thumbnail_size: tuple = (200, 300)):
        """
        Initialise results renderer.

        Args:
            thumbnail_size: (width, height) for page thumbnails
        """
        self.thumbnail_size = thumbnail_size

    def render_results_html(
        self,
        results: List[RetrievalResult],
        total_results: int,
        execution_time_ms: float,
        show_thumbnails: bool = True
    ) -> str:
        """
        Render results as HTML with thumbnails.

        Args:
            results: List of retrieval results
            total_results: Total number of results
            execution_time_ms: Query execution time
            show_thumbnails: Whether to render page thumbnails

        Returns:
            HTML string
        """
        html_parts = []

        # Header
        html_parts.append(
            f"""
            <div style="margin-bottom: 20px; padding: 10px; background: #f0f0f0; border-radius: 5px;">
                <strong>Found {total_results} results in {execution_time_ms:.2f}ms</strong>
            </div>
            """
        )

        # Result cards
        for result in results:
            card_html = self._render_result_card(result, show_thumbnails)
            html_parts.append(card_html)

        return "".join(html_parts)

    def _render_result_card(
        self,
        result: RetrievalResult,
        show_thumbnails: bool
    ) -> str:
        """Render individual result card."""
        card_style = """
        border: 1px solid #ddd;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 8px;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        """

        html = f'<div style="{card_style}">'

        # Header row
        html += f"""
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <div style="font-weight: bold; font-size: 18px;">
                #{result.rank} - {result.document_id[:8]}...
            </div>
            <div style="background: #4CAF50; color: white; padding: 5px 10px; border-radius: 3px;">
                {result.score:.3f}
            </div>
        </div>
        """

        # Type badge
        type_color = "#2196F3" if result.embedding_type == "text" else "#FF9800"
        html += f"""
        <div style="margin-bottom: 10px;">
            <span style="background: {type_color}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px;">
                {result.embedding_type.upper()}
            </span>
        </div>
        """

        # Content based on type
        if result.embedding_type == "text":
            html += self._render_text_result(result)
        else:
            html += self._render_vision_result(result, show_thumbnails)

        html += "</div>"
        return html

    def _render_text_result(self, result: RetrievalResult) -> str:
        """Render text result content."""
        text_content = result.metadata.get("text_content", "")

        if not text_content:
            return "<p><em>No text preview available</em></p>"

        # Truncate long text
        preview = text_content[:300] + "..." if len(text_content) > 300 else text_content

        html = f"""
        <div style="padding: 10px; background: #f9f9f9; border-left: 3px solid #2196F3; margin-top: 10px;">
            <p style="margin: 0; font-style: italic;">"{preview}"</p>
        </div>
        """

        # Metadata
        chunk_index = result.metadata.get("chunk_index", "N/A")
        char_count = result.metadata.get("char_count", "N/A")

        html += f"""
        <div style="margin-top: 10px; font-size: 12px; color: #666;">
            Chunk: {chunk_index} | Characters: {char_count}
        </div>
        """

        return html

    def _render_vision_result(
        self,
        result: RetrievalResult,
        show_thumbnails: bool
    ) -> str:
        """Render vision result content with optional thumbnail."""
        html_parts = []

        # Page information
        page_num = result.metadata.get("page_number", "N/A")
        html_parts.append(f"<div style='margin-bottom: 10px;'><strong>Page {page_num}</strong></div>")

        # Visual content badges
        has_diagrams = result.metadata.get("has_diagrams", False)
        has_tables = result.metadata.get("has_tables", False)
        layout_complexity = result.metadata.get("layout_complexity", "unknown")

        badges = []
        if has_diagrams:
            badges.append('<span style="background: #9C27B0; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; margin-right: 5px;">📊 Diagrams</span>')
        if has_tables:
            badges.append('<span style="background: #009688; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; margin-right: 5px;">📋 Tables</span>')

        badges.append(f'<span style="background: #607D8B; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Layout: {layout_complexity}</span>')

        if badges:
            html_parts.append(f"<div style='margin-bottom: 10px;'>{''.join(badges)}</div>")

        # Thumbnail (placeholder - requires PDF rendering)
        if show_thumbnails:
            html_parts.append(
                "<div style='background: #f0f0f0; width: 200px; height: 280px; "
                "display: flex; align-items: center; justify-content: center; "
                "border: 1px solid #ddd; border-radius: 4px;'>"
                f"<span style='color: #999;'>Page {page_num} Preview</span>"
                "</div>"
            )

        return "".join(html_parts)


# Update RaggedWebUI to use ResultsRenderer

class RaggedWebUI:
    def __init__(self, ...):
        # ... existing init code ...
        self.results_renderer = ResultsRenderer()

    def handle_query(self, ...):
        # ... existing query code ...

        # Use results renderer
        html = self.results_renderer.render_results_html(
            results=response.results,
            total_results=response.total_results,
            execution_time_ms=response.execution_time_ms,
            show_thumbnails=True
        )

        return html
```

**Deliverables:**
- `src/ui/results_renderer.py` (~200 lines)
- Rich HTML formatting for results
- Visual content badges
- Thumbnail placeholders

**Time:** 3-4 hours

---

### Phase 2: Advanced Features (8-10 hours)

#### Session 2.1: Real-Time GPU Monitoring (4-5h)

**Task:** Add live GPU memory charts and statistics

**Implementation:**

```python
# src/ui/monitoring.py

import gradio as gr
from typing import Dict, List
import time
from ragged.gpu.device_manager import DeviceManager, DeviceInfo, DeviceType


class GPUMonitor:
    """Real-time GPU monitoring for web UI."""

    def __init__(self, device_manager: DeviceManager):
        """
        Initialise GPU monitor.

        Args:
            device_manager: Device manager instance
        """
        self.device_manager = device_manager
        self.gpu_devices = [
            d for d in device_manager._available_devices
            if d.device_type != DeviceType.CPU
        ]

    def get_memory_stats(self) -> Dict[str, List]:
        """
        Get current memory statistics for plotting.

        Returns:
            Dictionary with timestamps and memory values
        """
        stats = {"timestamps": [], "allocated": [], "free": []}

        if not self.gpu_devices:
            return stats

        # Get stats for first GPU device
        device = self.gpu_devices[0]

        try:
            memory_info = self.device_manager.get_device_memory_info(device)

            allocated_gb = memory_info["allocated"] / (1024**3)
            free_gb = memory_info["free"] / (1024**3)

            stats["timestamps"].append(time.strftime("%H:%M:%S"))
            stats["allocated"].append(allocated_gb)
            stats["free"].append(free_gb)

        except Exception:
            pass

        return stats

    def create_monitoring_tab(self) -> gr.Tab:
        """
        Create GPU monitoring tab with live charts.

        Returns:
            Gradio Tab component
        """
        with gr.Tab("📊 GPU Monitor") as tab:
            if not self.gpu_devices:
                gr.Markdown("**No GPU devices available for monitoring.**")
                return tab

            gr.Markdown(f"## Real-Time GPU Monitoring")
            gr.Markdown(f"**Device:** {self.gpu_devices[0]}")

            # Memory chart
            memory_plot = gr.LinePlot(
                value={"timestamps": [], "allocated": [], "free": []},
                x="timestamps",
                y=["allocated", "free"],
                title="GPU Memory Usage (GB)",
                width=800,
                height=400
            )

            # Statistics
            with gr.Row():
                allocated_text = gr.Textbox(
                    label="Allocated",
                    value="0.00 GB",
                    interactive=False
                )

                free_text = gr.Textbox(
                    label="Free",
                    value="0.00 GB",
                    interactive=False
                )

                utilisation_text = gr.Textbox(
                    label="Utilisation",
                    value="0.0%",
                    interactive=False
                )

            # Auto-refresh every 2 seconds
            refresh_timer = gr.Timer(value=2.0)

            refresh_timer.tick(
                fn=self._update_monitoring,
                outputs=[memory_plot, allocated_text, free_text, utilisation_text]
            )

        return tab

    def _update_monitoring(self):
        """Update monitoring displays."""
        device = self.gpu_devices[0]

        try:
            memory_info = self.device_manager.get_device_memory_info(device)

            allocated_gb = memory_info["allocated"] / (1024**3)
            free_gb = memory_info["free"] / (1024**3)
            total_gb = memory_info["total"] / (1024**3)
            util_pct = (allocated_gb / total_gb) * 100 if total_gb > 0 else 0.0

            # Update plot data
            plot_data = self.get_memory_stats()

            return (
                plot_data,
                f"{allocated_gb:.2f} GB",
                f"{free_gb:.2f} GB",
                f"{util_pct:.1f}%"
            )

        except Exception:
            return (
                {"timestamps": [], "allocated": [], "free": []},
                "N/A",
                "N/A",
                "N/A"
            )
```

**Deliverables:**
- `src/ui/monitoring.py` (~150 lines)
- Live GPU memory charts
- Auto-refresh every 2 seconds

**Time:** 4-5 hours

---

#### Session 2.2: Batch Upload and Progress Tracking (4-5h)

**Task:** Support multiple PDF uploads with progress tracking

**Implementation:**

```python
# Extend src/ui/app.py

def _build_document_tab(self):
    """Build document management tab with batch upload."""
    gr.Markdown("## Upload Documents")

    with gr.Row():
        with gr.Column(scale=2):
            # Support multiple files
            pdf_input = gr.File(
                label="Upload PDF(s)",
                file_types=[".pdf"],
                type="filepath",
                file_count="multiple"  # Enable batch upload
            )

            vision_toggle = gr.Checkbox(
                label="Enable vision embeddings",
                value=self.enable_vision,
                interactive=self.enable_vision
            )

            upload_button = gr.Button("Ingest Documents", variant="primary")

        with gr.Column(scale=1):
            # Progress bar
            progress_bar = gr.Progress()

            # Status output
            progress_output = gr.Textbox(
                label="Status",
                lines=10,
                interactive=False
            )

    # ... rest of tab ...

    upload_button.click(
        fn=self.handle_batch_upload,
        inputs=[pdf_input, vision_toggle],
        outputs=[progress_output, document_list]
    )


def handle_batch_upload(
    self,
    pdf_paths: Optional[List[str]],
    enable_vision: bool,
    progress=gr.Progress()
) -> Tuple[str, List]:
    """
    Handle batch document upload.

    Args:
        pdf_paths: List of PDF file paths
        enable_vision: Whether to generate vision embeddings
        progress: Gradio Progress tracker

    Returns:
        Tuple of (status_message, updated_document_list)
    """
    if not pdf_paths:
        return "⚠️ Please upload at least one PDF file.", self.get_document_list()

    status_lines = []
    succeeded = 0
    failed = 0

    for i, pdf_path in enumerate(pdf_paths):
        # Update progress
        progress((i + 1) / len(pdf_paths), desc=f"Processing {i + 1}/{len(pdf_paths)}")

        try:
            doc_id = self.processor.process_document(
                Path(pdf_path),
                enable_vision=enable_vision and self.enable_vision
            )

            succeeded += 1
            status_lines.append(f"✅ {Path(pdf_path).name} → {doc_id[:8]}...")

        except Exception as e:
            failed += 1
            status_lines.append(f"❌ {Path(pdf_path).name}: {str(e)}")
            logger.error(f"Failed to process {pdf_path}: {e}")

    # Summary
    summary = (
        f"📊 Batch Upload Complete\n\n"
        f"Succeeded: {succeeded}\n"
        f"Failed: {failed}\n\n"
        + "\n".join(status_lines)
    )

    return summary, self.get_document_list()
```

**Deliverables:**
- Batch PDF upload support
- Progress tracking with Gradio Progress API
- Per-file status reporting

**Time:** 4-5 hours

---

### Phase 3: Polish and Testing (8-12 hours)

#### Session 3.1: UI/UX Improvements (4-6h)

**Enhancements:**
1. Custom CSS for better styling
2. Loading spinners for long operations
3. Error message styling
4. Keyboard shortcuts
5. Responsive layout adjustments

**Time:** 4-6 hours

---

#### Session 3.2: Testing and Documentation (4-6h)

**Test Coverage:**
1. UI component rendering
2. Event handler logic
3. Error handling in UI
4. Results formatting accuracy

**Documentation:**
- User guide for web UI
- Screenshots and examples
- Troubleshooting section

**Time:** 4-6 hours

---

### Phase 4: Deployment (2-4 hours)

#### Session 4.1: Production Configuration (1-2h)

**Task:** Add production-ready configurations

**Implementation:**

```python
# src/ui/config.py

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class UIConfig:
    """Web UI configuration."""

    # Server settings
    server_name: str = "127.0.0.1"
    server_port: int = 7860
    enable_share: bool = False

    # Security
    auth_username: Optional[str] = None
    auth_password: Optional[str] = None

    # Features
    enable_vision: bool = True
    enable_batch_upload: bool = True
    max_upload_size_mb: int = 100

    # GPU settings
    device: Optional[str] = None
    enable_gpu_monitoring: bool = True

    # Storage
    collection_name: str = "documents"
    persist_directory: Optional[Path] = None

    # UI theme
    theme: str = "soft"  # "soft", "default", "monochrome"
    show_footer: bool = True


def load_config(config_path: Optional[Path] = None) -> UIConfig:
    """Load UI configuration from file or defaults."""
    if config_path and config_path.exists():
        # Load from YAML/JSON (future enhancement)
        pass

    return UIConfig()
```

**Deliverables:**
- Configuration dataclass
- Authentication support (optional)
- Resource limits

**Time:** 1-2 hours

---

#### Session 4.2: Docker and Deployment Guide (1-2h)

**Deliverables:**
- Dockerfile for web UI
- docker-compose.yml for full stack
- Deployment documentation

**Time:** 1-2 hours

---

## Success Criteria

**Functional Requirements:**
- [ ] Document upload (single and batch)
- [ ] Vision embedding toggle
- [ ] Text, image, and hybrid queries
- [ ] Results display with metadata
- [ ] GPU monitoring dashboard
- [ ] Storage statistics
- [ ] Progress indicators for long operations

**Quality Requirements:**
- [ ] 75%+ test coverage for UI module
- [ ] Responsive design (desktop and tablet)
- [ ] Error handling with user-friendly messages
- [ ] <2s load time for initial UI

**User Experience:**
- [ ] Intuitive layout and navigation
- [ ] Helpful tooltips and labels
- [ ] Visual feedback for all actions
- [ ] Accessible (WCAG 2.1 Level AA compliance)

---

## Dependencies

**Required:**
- gradio >= 4.0.0 (web framework)
- All VISION-001 through VISION-005 features

**Optional:**
- plotly >= 5.0.0 (enhanced charts)
- pandas >= 2.0.0 (data manipulation)

---

## Known Limitations

1. **Thumbnail Generation:** Placeholder thumbnails (requires PDF rendering integration)
2. **Authentication:** Basic auth only (no OAuth, SSO)
3. **Multi-User:** No concurrent user session management
4. **Real-Time Updates:** Polling-based (no WebSocket push)

---

## Future Enhancements (Post-v0.5)

1. **Advanced Charts:** Interactive plots with Plotly
2. **Document Viewer:** Embedded PDF viewer with highlighting
3. **Query History:** Save and revisit previous queries
4. **Export Results:** Download results as JSON/CSV/PDF
5. **Custom Themes:** User-selectable colour schemes
6. **Mobile App:** React Native companion app

---

**Status:** Planned
**Estimated Total Effort:** 24-32 hours
