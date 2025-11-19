"""
Test report generation utilities.

Provides functions to generate HTML, JSON, and summary reports.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================================
# HTML Report Generation
# ============================================================================

def generate_html_report(
    results: Dict[str, Any],
    output_path: str,
    title: str = "Test Results"
) -> None:
    """
    Generate HTML test report.

    Args:
        results: Test results dictionary
        output_path: Path to output HTML file
        title: Report title

    Example:
        generate_html_report(
            results=test_results,
            output_path="reports/test_run_2025-11-19.html",
            title="v0.2.9 Manual Test Results"
        )
    """
    passed = results.get("passed", [])
    failed = results.get("failed", [])
    skipped = results.get("skipped", [])

    total = len(passed) + len(failed) + len(skipped)
    pass_rate = (len(passed) / total * 100) if total > 0 else 0

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .header {{
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .summary {{
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .summary-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }}
            .summary-card {{
                padding: 15px;
                border-radius: 5px;
                text-align: center;
            }}
            .passed {{ background-color: #d4edda; color: #155724; }}
            .failed {{ background-color: #f8d7da; color: #721c24; }}
            .skipped {{ background-color: #fff3cd; color: #856404; }}
            .total {{ background-color: #d1ecf1; color: #0c5460; }}
            .metric-value {{
                font-size: 2em;
                font-weight: bold;
                margin: 10px 0;
            }}
            .metric-label {{
                font-size: 0.9em;
                text-transform: uppercase;
            }}
            .test-section {{
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .test-section h2 {{
                margin-top: 0;
                border-bottom: 2px solid #2c3e50;
                padding-bottom: 10px;
            }}
            .test-item {{
                padding: 10px;
                margin: 5px 0;
                border-left: 3px solid;
                background-color: #f8f9fa;
            }}
            .test-item.passed {{ border-color: #28a745; }}
            .test-item.failed {{ border-color: #dc3545; }}
            .test-item.skipped {{ border-color: #ffc107; }}
            .test-name {{
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .test-details {{
                font-size: 0.9em;
                color: #666;
            }}
            .timestamp {{
                color: #999;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{title}</h1>
            <p class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>

        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-grid">
                <div class="summary-card total">
                    <div class="metric-label">Total Tests</div>
                    <div class="metric-value">{total}</div>
                </div>
                <div class="summary-card passed">
                    <div class="metric-label">Passed</div>
                    <div class="metric-value">{len(passed)}</div>
                </div>
                <div class="summary-card failed">
                    <div class="metric-label">Failed</div>
                    <div class="metric-value">{len(failed)}</div>
                </div>
                <div class="summary-card skipped">
                    <div class="metric-label">Skipped</div>
                    <div class="metric-value">{len(skipped)}</div>
                </div>
            </div>
            <div style="margin-top: 20px; padding: 15px; background-color: #e7f3ff; border-radius: 5px;">
                <strong>Pass Rate:</strong> {pass_rate:.1f}%
            </div>
        </div>

        <div class="test-section">
            <h2>Passed Tests ({len(passed)})</h2>
            {"".join([f'<div class="test-item passed"><div class="test-name">{test}</div></div>' for test in passed]) if passed else '<p>No passed tests</p>'}
        </div>

        <div class="test-section">
            <h2>Failed Tests ({len(failed)})</h2>
            {"".join([f'<div class="test-item failed"><div class="test-name">{test}</div></div>' for test in failed]) if failed else '<p>No failed tests</p>'}
        </div>

        <div class="test-section">
            <h2>Skipped Tests ({len(skipped)})</h2>
            {"".join([f'<div class="test-item skipped"><div class="test-name">{test}</div></div>' for test in skipped]) if skipped else '<p>No skipped tests</p>'}
        </div>
    </body>
    </html>
    """

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html_content)


# ============================================================================
# JSON Report Generation
# ============================================================================

def generate_json_report(
    results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Generate JSON test report.

    Args:
        results: Test results dictionary
        output_path: Path to output JSON file

    Example:
        generate_json_report(
            results=test_results,
            output_path="reports/test_run_2025-11-19.json"
        )
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "summary": {
            "total": len(results.get("passed", [])) + len(results.get("failed", [])) + len(results.get("skipped", [])),
            "passed": len(results.get("passed", [])),
            "failed": len(results.get("failed", [])),
            "skipped": len(results.get("skipped", [])),
        }
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)


# ============================================================================
# Performance Report Generation
# ============================================================================

def generate_performance_report(
    benchmarks: Dict[str, Dict[str, float]],
    output_path: str,
    title: str = "Performance Comparison"
) -> None:
    """
    Generate performance comparison report.

    Args:
        benchmarks: Dictionary mapping version to performance metrics
        output_path: Path to output HTML file
        title: Report title

    Example:
        benchmarks = {
            "v0.2.8": {"ingestion_time": 50, "query_latency": 200},
            "v0.2.9": {"ingestion_time": 45, "query_latency": 180}
        }
        generate_performance_report(benchmarks, "reports/performance.html")
    """
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .header {{
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            table {{
                width: 100%;
                background-color: white;
                border-collapse: collapse;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border-radius: 5px;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #2c3e50;
                color: white;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            .improvement {{
                color: #28a745;
                font-weight: bold;
            }}
            .regression {{
                color: #dc3545;
                font-weight: bold;
            }}
            .timestamp {{
                color: #999;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{title}</h1>
            <p class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Version</th>
                    {"".join([f"<th>{metric}</th>" for metric in next(iter(benchmarks.values())).keys()])}
                </tr>
            </thead>
            <tbody>
                {"".join([f'''
                <tr>
                    <td><strong>{version}</strong></td>
                    {"".join([f"<td>{value}</td>" for value in metrics.values()])}
                </tr>
                ''' for version, metrics in benchmarks.items()])}
            </tbody>
        </table>
    </body>
    </html>
    """

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html_content)


# ============================================================================
# Summary Report Generation
# ============================================================================

def generate_summary_report(results: Dict[str, Any]) -> str:
    """
    Generate text summary of test results.

    Args:
        results: Test results dictionary

    Returns:
        Formatted summary string

    Example:
        summary = generate_summary_report(test_results)
        print(summary)
    """
    passed = results.get("passed", [])
    failed = results.get("failed", [])
    skipped = results.get("skipped", [])

    total = len(passed) + len(failed) + len(skipped)
    pass_rate = (len(passed) / total * 100) if total > 0 else 0

    summary = f"""
==========================================
Test Results Summary
==========================================
Total Tests:   {total}
Passed:        {len(passed)} ({len(passed)/total*100:.1f}%)
Failed:        {len(failed)} ({len(failed)/total*100:.1f}%)
Skipped:       {len(skipped)} ({len(skipped)/total*100:.1f}%)
Pass Rate:     {pass_rate:.1f}%
==========================================
"""

    if failed:
        summary += "\nFailed Tests:\n"
        for test in failed:
            summary += f"  ✗ {test}\n"

    return summary


# ============================================================================
# Comparison Table Generation
# ============================================================================

def create_comparison_table(
    data: Dict[str, Dict[str, Any]],
    columns: Optional[List[str]] = None
) -> str:
    """
    Create markdown comparison table.

    Args:
        data: Dictionary mapping row name to column values
        columns: List of column names (or None to infer)

    Returns:
        Markdown table string

    Example:
        table = create_comparison_table({
            "v0.2.8": {"latency": 200, "throughput": 10},
            "v0.2.9": {"latency": 180, "throughput": 12}
        })
        print(table)
    """
    if not data:
        return ""

    # Infer columns if not provided
    if columns is None:
        columns = list(next(iter(data.values())).keys())

    # Build table header
    header = "| Version | " + " | ".join(columns) + " |"
    separator = "|---------|" + "|".join(["-------"] * len(columns)) + "|"

    # Build table rows
    rows = []
    for row_name, row_data in data.items():
        values = [str(row_data.get(col, "N/A")) for col in columns]
        row = f"| {row_name} | " + " | ".join(values) + " |"
        rows.append(row)

    # Combine
    table = "\n".join([header, separator] + rows)
    return table


# ============================================================================
# Format Test Results
# ============================================================================

def format_test_results(
    results: List[Dict[str, Any]],
    format_type: str = "text"
) -> str:
    """
    Format test results for display.

    Args:
        results: List of test result dictionaries
        format_type: Format type ("text", "json", "markdown")

    Returns:
        Formatted results string

    Example:
        formatted = format_test_results(results, format_type="markdown")
        print(formatted)
    """
    if format_type == "json":
        return json.dumps(results, indent=2)

    elif format_type == "markdown":
        output = "## Test Results\n\n"
        for result in results:
            status = "✅" if result.get("passed") else "❌"
            output += f"{status} **{result.get('name', 'Unknown')}**\n"
            if "details" in result:
                output += f"   {result['details']}\n"
            output += "\n"
        return output

    else:  # text
        output = "Test Results:\n"
        output += "=" * 50 + "\n"
        for result in results:
            status = "PASS" if result.get("passed") else "FAIL"
            output += f"[{status}] {result.get('name', 'Unknown')}\n"
            if "details" in result:
                output += f"      {result['details']}\n"
        return output
