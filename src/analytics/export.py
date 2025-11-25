"""Data export and visualisation for analytics metrics.

Provides export to JSON/CSV and basic ASCII visualisation capabilities.

v0.6.4 OPTIMISE-004 Phase 3: Data Export & Visualisation
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MetricsExporter:
    """Export analytics metrics to various formats.

    Supports:
    - JSON export (structured, machine-readable)
    - CSV export (tabular, spreadsheet-compatible)
    - ASCII charts (basic CLI visualisation)
    """

    @staticmethod
    def export_to_json(
        data: dict[str, Any],
        file_path: Optional[Path] = None,
        pretty: bool = True,
    ) -> str:
        """Export metrics to JSON format.

        Args:
            data: Metrics data to export
            file_path: Optional file path to write JSON
            pretty: Use pretty formatting (indented)

        Returns:
            JSON string
        """
        # Convert datetime objects to ISO format
        json_data = MetricsExporter._prepare_for_json(data)

        # Serialise to JSON
        indent = 2 if pretty else None
        json_str = json.dumps(json_data, indent=indent, ensure_ascii=False)

        # Write to file if path provided
        if file_path:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(json_str, encoding="utf-8")
            logger.info(f"Exported metrics to JSON: {file_path}")

        return json_str

    @staticmethod
    def export_to_csv(
        data: list[dict[str, Any]],
        file_path: Path,
        fieldnames: Optional[list[str]] = None,
    ) -> None:
        """Export metrics to CSV format.

        Args:
            data: List of metric dictionaries
            file_path: File path to write CSV
            fieldnames: Optional field names (inferred from data if not provided)
        """
        if not data:
            logger.warning("No data to export to CSV")
            return

        # Infer fieldnames if not provided
        if fieldnames is None:
            fieldnames = list(data[0].keys())

        # Create parent directory
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write CSV
        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()

            for row in data:
                # Convert datetime objects to ISO format
                prepared_row = MetricsExporter._prepare_row_for_csv(row)
                writer.writerow(prepared_row)

        logger.info(f"Exported {len(data)} rows to CSV: {file_path}")

    @staticmethod
    def _prepare_for_json(data: Any) -> Any:
        """Recursively prepare data for JSON serialisation.

        Args:
            data: Data to prepare

        Returns:
            JSON-serialisable data
        """
        if isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, dict):
            return {k: MetricsExporter._prepare_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [MetricsExporter._prepare_for_json(item) for item in data]
        elif isinstance(data, tuple):
            return [MetricsExporter._prepare_for_json(item) for item in data]
        else:
            return data

    @staticmethod
    def _prepare_row_for_csv(row: dict[str, Any]) -> dict[str, Any]:
        """Prepare a row for CSV export.

        Args:
            row: Dictionary row

        Returns:
            CSV-compatible row
        """
        prepared = {}
        for k, v in row.items():
            if isinstance(v, datetime):
                prepared[k] = v.isoformat()
            elif isinstance(v, (dict, list)):
                # Serialise complex types as JSON strings
                prepared[k] = json.dumps(v)
            else:
                prepared[k] = v
        return prepared


class ASCIIVisualiser:
    """Basic ASCII visualisation for CLI display.

    Provides simple charts for terminal output.
    """

    @staticmethod
    def bar_chart(
        data: dict[str, float],
        title: str = "",
        max_width: int = 50,
        show_values: bool = True,
    ) -> str:
        """Create horizontal bar chart in ASCII.

        Args:
            data: Dictionary mapping labels to values
            title: Chart title
            max_width: Maximum width of bars (in characters)
            show_values: Show numeric values alongside bars

        Returns:
            ASCII bar chart string
        """
        if not data:
            return "No data to display"

        lines = []

        # Add title
        if title:
            lines.append(title)
            lines.append("=" * len(title))
            lines.append("")

        # Find max value for scaling
        max_value = max(data.values())
        if max_value == 0:
            max_value = 1  # Avoid division by zero

        # Find max label length for alignment
        max_label_len = max(len(str(label)) for label in data.keys())

        # Generate bars
        for label, value in data.items():
            # Calculate bar length
            bar_length = int((value / max_value) * max_width)

            # Create bar
            bar = "█" * bar_length

            # Format line
            label_str = str(label).ljust(max_label_len)
            if show_values:
                value_str = f" {value:.2f}" if isinstance(value, float) else f" {value}"
                line = f"{label_str} | {bar}{value_str}"
            else:
                line = f"{label_str} | {bar}"

            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def line_chart(
        data: list[tuple[str, float]],
        title: str = "",
        height: int = 10,
        width: int = 60,
    ) -> str:
        """Create simple line chart in ASCII.

        Args:
            data: List of (label, value) tuples
            title: Chart title
            height: Chart height in lines
            width: Chart width in characters

        Returns:
            ASCII line chart string
        """
        if not data:
            return "No data to display"

        lines = []

        # Add title
        if title:
            lines.append(title)
            lines.append("=" * len(title))
            lines.append("")

        # Extract values
        values = [v for _, v in data]
        if not values:
            return "No values to display"

        # Find min and max for scaling
        min_val = min(values)
        max_val = max(values)
        val_range = max_val - min_val
        if val_range == 0:
            val_range = 1

        # Create chart grid
        grid = [[" " for _ in range(width)] for _ in range(height)]

        # Plot points
        for i, (_, value) in enumerate(data):
            x = int((i / len(data)) * (width - 1))
            y = height - 1 - int(((value - min_val) / val_range) * (height - 1))

            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = "●"

                # Connect with previous point (simple)
                if i > 0:
                    prev_x = int(((i - 1) / len(data)) * (width - 1))
                    prev_y = height - 1 - int(
                        ((values[i - 1] - min_val) / val_range) * (height - 1)
                    )

                    # Draw connecting line
                    for step_x in range(min(prev_x, x), max(prev_x, x) + 1):
                        if prev_x == x:
                            step_y = prev_y
                        else:
                            step_y = prev_y + int(
                                ((step_x - prev_x) / (x - prev_x)) * (y - prev_y)
                            )

                        if 0 <= step_x < width and 0 <= step_y < height:
                            if grid[step_y][step_x] == " ":
                                grid[step_y][step_x] = "·"

        # Add Y-axis labels and grid lines
        for row_idx, row in enumerate(grid):
            y_val = max_val - (row_idx / (height - 1)) * val_range
            y_label = f"{y_val:>6.1f} │ "
            lines.append(y_label + "".join(row))

        # Add X-axis
        lines.append(" " * 8 + "└" + "─" * width)

        # Add X-axis labels (first, middle, last)
        if data:
            first_label = data[0][0]
            last_label = data[-1][0]
            mid_idx = len(data) // 2
            mid_label = data[mid_idx][0] if mid_idx < len(data) else ""

            x_axis_labels = " " * 9 + first_label
            if mid_label:
                padding = (width // 2) - len(first_label) - len(mid_label) // 2
                x_axis_labels += " " * padding + mid_label
            if last_label:
                padding = width - len(x_axis_labels) + 9 - len(last_label)
                x_axis_labels += " " * padding + last_label

            lines.append(x_axis_labels)

        return "\n".join(lines)

    @staticmethod
    def summary_table(
        data: dict[str, Any],
        title: str = "",
        key_width: int = 30,
        value_width: int = 40,
    ) -> str:
        """Create simple summary table in ASCII.

        Args:
            data: Dictionary of key-value pairs
            title: Table title
            key_width: Width of key column
            value_width: Width of value column

        Returns:
            ASCII table string
        """
        if not data:
            return "No data to display"

        lines = []

        # Add title
        if title:
            lines.append(title)
            lines.append("=" * len(title))
            lines.append("")

        # Table header
        total_width = key_width + value_width + 3
        lines.append("┌" + "─" * total_width + "┐")

        # Rows
        for key, value in data.items():
            # Format value
            if isinstance(value, float):
                value_str = f"{value:.2f}"
            elif isinstance(value, (dict, list)):
                value_str = json.dumps(value)
            else:
                value_str = str(value)

            # Truncate if too long
            key_str = str(key)[:key_width].ljust(key_width)
            value_str = value_str[:value_width].ljust(value_width)

            lines.append(f"│ {key_str} │ {value_str} │")

        # Table footer
        lines.append("└" + "─" * total_width + "┘")

        return "\n".join(lines)


def export_summary_to_json(
    query,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    file_path: Optional[Path] = None,
) -> str:
    """Export query summary to JSON.

    Args:
        query: MetricsQuery instance
        start_time: Start of time range
        end_time: End of time range
        file_path: Optional file path to write JSON

    Returns:
        JSON string
    """
    summary = query.query_summary(start_time=start_time, end_time=end_time)
    return MetricsExporter.export_to_json(summary, file_path=file_path)


def export_query_metrics_to_csv(
    storage,
    file_path: Path,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> None:
    """Export query metrics to CSV.

    Args:
        storage: MetricsStorage instance
        file_path: File path to write CSV
        start_time: Start of time range
        end_time: End of time range
    """
    from ragged.analytics.queries import MetricsQuery

    query = MetricsQuery(db_path=storage.db_path)

    # Get all query metrics in time range
    import sqlite3

    conn = sqlite3.connect(str(storage.db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if start_time and end_time:
        cursor.execute(
            """
            SELECT * FROM query_metrics
            WHERE timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp DESC
            """,
            (start_time.isoformat(), end_time.isoformat()),
        )
    else:
        cursor.execute(
            """
            SELECT * FROM query_metrics
            ORDER BY timestamp DESC
            """
        )

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Export to CSV
    if rows:
        MetricsExporter.export_to_csv(rows, file_path)
    else:
        logger.warning("No query metrics to export")


def visualise_latency_distribution(
    query,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> str:
    """Visualise latency distribution as ASCII chart.

    Args:
        query: MetricsQuery instance
        start_time: Start of time range
        end_time: End of time range

    Returns:
        ASCII chart string
    """
    percentiles = query.query_latency_percentiles(
        start_time=start_time,
        end_time=end_time,
        percentiles=[50, 75, 90, 95, 99],
    )

    return ASCIIVisualiser.bar_chart(
        data=percentiles,
        title="Latency Distribution (ms)",
        show_values=True,
    )


def visualise_model_usage(
    query,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> str:
    """Visualise model usage as ASCII chart.

    Args:
        query: MetricsQuery instance
        start_time: Start of time range
        end_time: End of time range

    Returns:
        ASCII chart string
    """
    comparison = query.compare_models(start_time=start_time, end_time=end_time)

    # Extract query counts
    model_usage = {
        model["model_id"]: model["query_count"] for model in comparison["models"]
    }

    return ASCIIVisualiser.bar_chart(
        data=model_usage,
        title="Model Usage (Query Count)",
        show_values=True,
    )


def visualise_cache_effectiveness(
    query,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> str:
    """Visualise cache effectiveness as ASCII chart.

    Args:
        query: MetricsQuery instance
        start_time: Start of time range
        end_time: End of time range

    Returns:
        ASCII chart string
    """
    cache_stats = query.query_cache_effectiveness(
        start_time=start_time, end_time=end_time
    )

    # Extract hit rates
    hit_rates = {stats["cache_layer"]: stats["hit_rate"] for stats in cache_stats}

    return ASCIIVisualiser.bar_chart(
        data=hit_rates,
        title="Cache Hit Rates",
        show_values=True,
    )
