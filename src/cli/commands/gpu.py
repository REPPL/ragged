"""GPU management commands for ragged CLI.

v0.5.3: Device listing, info, stats, and benchmarking.
"""

import sys
import time
from typing import Optional

import click

from src.cli.common import ProgressType, console
from src.utils.logging import get_logger

logger = get_logger(__name__)


@click.group()
def gpu() -> None:
    """GPU device management and monitoring.

    \b
    Commands:
        list      - List all available devices
        info      - Show device information
        stats     - Display memory statistics
        benchmark - Benchmark vision embeddings

    \b
    Examples:
        ragged gpu list
        ragged gpu info cuda:0
        ragged gpu stats --watch
        ragged gpu benchmark --batch-size 8
    """
    pass


@gpu.command()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed device information",
)
def list(verbose: bool) -> None:
    """List all available GPU devices.

    \b
    Displays:
    - Device type (CUDA, MPS, CPU)
    - Device ID
    - Device name (if available)
    - Total memory (if available)
    - Compute capability (CUDA only)

    \b
    Examples:
        ragged gpu list
        ragged gpu list --verbose
    """
    from src.gpu.device_manager import DeviceManager, DeviceType

    try:
        manager = DeviceManager()
        devices = manager.available_devices

        if not devices:
            console.print("[yellow]No devices detected.[/yellow]")
            return

        console.print(f"[bold blue]Available Devices ({len(devices)}):[/bold blue]")
        console.print()

        for i, device in enumerate(devices):
            # Device type and ID
            if device.device_type == DeviceType.CPU:
                device_str = f"[cyan]{device.device_type.value}[/cyan]"
            elif device.device_type == DeviceType.CUDA:
                device_str = f"[green]cuda:{device.device_id}[/green]"
            elif device.device_type == DeviceType.MPS:
                device_str = f"[green]mps[/green]"
            else:
                device_str = device.device_type.value

            console.print(f"[{i}] {device_str}")

            # Device name
            if device.name:
                console.print(f"    Name: {device.name}")

            # Memory
            if device.total_memory:
                memory_gb = device.total_memory / (1024**3)
                console.print(f"    Memory: {memory_gb:.2f} GB")

            # Compute capability (CUDA only)
            if device.compute_capability:
                major, minor = device.compute_capability
                console.print(f"    Compute Capability: {major}.{minor}")

            if verbose:
                # Show optimal device marker
                optimal = manager.get_optimal_device()
                if device.device_type == optimal.device_type and device.device_id == optimal.device_id:
                    console.print("    [dim]✓ Optimal device[/dim]")

            console.print()

        # Show recommendation
        optimal = manager.get_optimal_device()
        console.print(f"[dim]Recommended device: {optimal.device_type.value}[/dim]")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to list devices: {e}")
        logger.error(f"Device listing failed: {e}", exc_info=True)
        sys.exit(1)


@gpu.command()
@click.argument("device", required=False)
def info(device: Optional[str]) -> None:
    """Show detailed device information.

    \b
    If no device is specified, shows info for the optimal device.

    \b
    Examples:
        ragged gpu info
        ragged gpu info cuda:0
        ragged gpu info mps
        ragged gpu info cpu
    """
    from src.gpu.device_manager import DeviceManager

    try:
        manager = DeviceManager()

        # Get device
        if device:
            device_info = manager.get_optimal_device(device_hint=device)
        else:
            device_info = manager.get_optimal_device()

        console.print(f"[bold blue]Device Information:[/bold blue]")
        console.print()

        # Basic info
        console.print(f"Type: {device_info.device_type.value}")
        console.print(f"ID: {device_info.device_id}")

        if device_info.name:
            console.print(f"Name: {device_info.name}")

        # Memory info
        if device_info.total_memory:
            memory_gb = device_info.total_memory / (1024**3)
            console.print(f"Total Memory: {memory_gb:.2f} GB")

            # Get current memory usage if GPU
            from src.gpu.device_manager import DeviceType

            if device_info.device_type != DeviceType.CPU:
                try:
                    mem_info = manager.get_memory_info(device_info)
                    if mem_info:
                        allocated = mem_info.get("allocated", 0) / (1024**3)
                        reserved = mem_info.get("reserved", 0) / (1024**3)
                        free = mem_info.get("free", 0) / (1024**3)

                        console.print(f"Allocated: {allocated:.2f} GB")
                        console.print(f"Reserved: {reserved:.2f} GB")
                        console.print(f"Free: {free:.2f} GB")

                        if device_info.total_memory:
                            utilization = (allocated / (device_info.total_memory / (1024**3))) * 100
                            console.print(f"Utilization: {utilization:.1f}%")
                except Exception:
                    pass

        # Compute capability (CUDA only)
        if device_info.compute_capability:
            major, minor = device_info.compute_capability
            console.print(f"Compute Capability: {major}.{minor}")

        # Optimal status
        optimal = manager.get_optimal_device()
        if device_info.device_type == optimal.device_type and device_info.device_id == optimal.device_id:
            console.print()
            console.print("[green]✓ This is the optimal device[/green]")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to get device info: {e}")
        logger.error(f"Device info failed: {e}", exc_info=True)
        sys.exit(1)


@gpu.command()
@click.argument("device", required=False)
@click.option(
    "--watch",
    "-w",
    is_flag=True,
    help="Auto-refresh every 1 second (Ctrl+C to stop)",
)
@click.option(
    "--interval",
    "-i",
    type=int,
    default=1,
    help="Refresh interval in seconds (default: 1)",
)
def stats(device: Optional[str], watch: bool, interval: int) -> None:
    """Display real-time memory statistics.

    \b
    Monitoring Mode:
    Use --watch for continuous monitoring with automatic refresh.
    Press Ctrl+C to stop.

    \b
    Examples:
        ragged gpu stats
        ragged gpu stats cuda:0
        ragged gpu stats --watch
        ragged gpu stats mps --watch --interval 2
    """
    from src.gpu.device_manager import DeviceManager, DeviceType

    try:
        manager = DeviceManager()

        # Get device
        if device:
            device_info = manager.get_optimal_device(device_hint=device)
        else:
            device_info = manager.get_optimal_device()

        # Check if device supports stats
        if device_info.device_type == DeviceType.CPU:
            console.print("[yellow]CPU device does not have GPU memory statistics.[/yellow]")
            return

        console.print(f"[bold blue]Memory Statistics: {device_info.device_type.value}[/bold blue]")
        console.print()

        try:
            if watch:
                # Continuous monitoring
                console.print("[dim]Press Ctrl+C to stop...[/dim]")
                console.print()

                while True:
                    mem_info = manager.get_memory_info(device_info)

                    if mem_info:
                        allocated = mem_info.get("allocated", 0) / (1024**3)
                        reserved = mem_info.get("reserved", 0) / (1024**3)
                        free = mem_info.get("free", 0) / (1024**3)

                        # Clear previous output (for watch mode)
                        if watch:
                            console.clear()

                        console.print(
                            f"[bold blue]Memory Statistics: {device_info.device_type.value}[/bold blue]"
                        )
                        console.print()
                        console.print(f"Allocated: {allocated:.2f} GB")
                        console.print(f"Reserved:  {reserved:.2f} GB")
                        console.print(f"Free:      {free:.2f} GB")

                        if device_info.total_memory:
                            total = device_info.total_memory / (1024**3)
                            utilization = (allocated / total) * 100
                            console.print(f"Total:     {total:.2f} GB")
                            console.print(f"Utilization: {utilization:.1f}%")

                            # Visual progress bar
                            bar_width = 40
                            filled = int((utilization / 100) * bar_width)
                            bar = "█" * filled + "░" * (bar_width - filled)

                            # Color based on utilization
                            if utilization > 95:
                                color = "red"
                            elif utilization > 85:
                                color = "yellow"
                            else:
                                color = "green"

                            console.print(f"[{color}]{bar}[/{color}]")

                        console.print()
                        console.print(f"[dim]Refreshing every {interval}s... (Ctrl+C to stop)[/dim]")

                    time.sleep(interval)

            else:
                # Single snapshot
                mem_info = manager.get_memory_info(device_info)

                if mem_info:
                    allocated = mem_info.get("allocated", 0) / (1024**3)
                    reserved = mem_info.get("reserved", 0) / (1024**3)
                    free = mem_info.get("free", 0) / (1024**3)

                    console.print(f"Allocated: {allocated:.2f} GB")
                    console.print(f"Reserved:  {reserved:.2f} GB")
                    console.print(f"Free:      {free:.2f} GB")

                    if device_info.total_memory:
                        total = device_info.total_memory / (1024**3)
                        utilization = (allocated / total) * 100
                        console.print(f"Total:     {total:.2f} GB")
                        console.print(f"Utilization: {utilization:.1f}%")
                else:
                    console.print("[yellow]Memory info not available for this device.[/yellow]")

        except KeyboardInterrupt:
            console.print()
            console.print("[dim]Monitoring stopped.[/dim]")

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to get statistics: {e}")
        logger.error(f"Stats failed: {e}", exc_info=True)
        sys.exit(1)


@gpu.command()
@click.option(
    "--batch-size",
    "-b",
    type=int,
    help="Batch size for benchmark (default: adaptive)",
)
@click.option(
    "--num-pages",
    "-n",
    type=int,
    default=10,
    help="Number of pages to process (default: 10)",
)
@click.option(
    "--device",
    "-d",
    help="Device to benchmark (default: all available)",
)
def benchmark(batch_size: Optional[int], num_pages: int, device: Optional[str]) -> None:
    """Benchmark vision embedding generation.

    \b
    Benchmarking:
    Generates synthetic images and measures embedding generation performance
    across different devices. Useful for comparing CUDA, MPS, and CPU.

    \b
    Examples:
        ragged gpu benchmark
        ragged gpu benchmark --batch-size 8 --num-pages 20
        ragged gpu benchmark --device cuda:0
        ragged gpu benchmark --device mps
    """
    from src.embeddings.colpali_embedder import ColPaliEmbedder
    from src.gpu.device_manager import DeviceManager

    try:
        manager = DeviceManager()

        # Determine which devices to benchmark
        if device:
            devices = [manager.get_optimal_device(device_hint=device)]
        else:
            devices = manager.available_devices

        console.print(f"[bold blue]Vision Embedding Benchmark[/bold blue]")
        console.print(f"Pages: {num_pages}")
        if batch_size:
            console.print(f"Batch size: {batch_size}")
        else:
            console.print("Batch size: adaptive")
        console.print()

        results = []

        for dev_info in devices:
            console.print(f"[cyan]Benchmarking {dev_info.device_type.value}...[/cyan]")

            try:
                # Create synthetic images
                from PIL import Image
                import numpy as np

                synthetic_images = []
                for _ in range(num_pages):
                    # Create random image (simulating PDF page)
                    img_array = np.random.randint(0, 255, (1024, 768, 3), dtype=np.uint8)
                    synthetic_images.append(Image.fromarray(img_array))

                # Initialize embedder
                embedder = ColPaliEmbedder(
                    device=None if dev_info.device_type.value == "auto" else dev_info.device_type.value,
                    batch_size=batch_size,
                    enable_adaptive_batching=batch_size is None,
                    enable_memory_monitoring=True,
                    enable_oom_recovery=True,
                )

                # Warmup
                _ = embedder.embed_batch_images([synthetic_images[0]])

                # Benchmark
                start_time = time.time()
                embeddings = embedder.embed_batch_images(synthetic_images)
                elapsed_time = time.time() - start_time

                # Calculate metrics
                pages_per_sec = num_pages / elapsed_time
                ms_per_page = (elapsed_time * 1000) / num_pages

                results.append({
                    "device": dev_info.device_type.value,
                    "batch_size": embedder.batch_size,
                    "total_time": elapsed_time,
                    "pages_per_sec": pages_per_sec,
                    "ms_per_page": ms_per_page,
                    "embedding_shape": embeddings.shape,
                })

                console.print(f"  Total time: {elapsed_time:.2f}s")
                console.print(f"  Throughput: {pages_per_sec:.2f} pages/sec")
                console.print(f"  Latency: {ms_per_page:.1f}ms/page")
                console.print(f"  Batch size: {embedder.batch_size}")
                console.print()

            except Exception as e:
                console.print(f"  [red]Failed: {e}[/red]")
                console.print()
                continue

        # Summary
        if len(results) > 1:
            console.print("[bold]Summary:[/bold]")
            console.print()

            # Sort by throughput
            results.sort(key=lambda x: x["pages_per_sec"], reverse=True)

            for i, result in enumerate(results):
                rank = f"[{i+1}]"
                console.print(
                    f"{rank} {result['device']}: {result['pages_per_sec']:.2f} pages/sec "
                    f"({result['ms_per_page']:.1f}ms/page)"
                )

            # Show speedup
            if len(results) >= 2:
                fastest = results[0]
                slowest = results[-1]
                speedup = fastest["pages_per_sec"] / slowest["pages_per_sec"]
                console.print()
                console.print(
                    f"[dim]{fastest['device']} is {speedup:.1f}x faster than {slowest['device']}[/dim]"
                )

    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Benchmark failed: {e}")
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        sys.exit(1)
