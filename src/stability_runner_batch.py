"""
Batch stability testing runner for benchmarking tasks.

Supports running multiple tasks with a single GitHub issue using patterns or lists.
"""

import sys
import json
import statistics
import glob
from pathlib import Path
from typing import Dict, Any, List, Set
from datetime import datetime

from .experiment import Experiment
from .config import Config


def extract_tasks(issue_body: str) -> List[str]:
    """
    Extract task list from GitHub issue body.

    Supports:
    - GitHub issue form format (from template):
        ### Task Pattern (if using Pattern Matching)
        htan_*_typos
    - Raw YAML format (legacy):
        tasks: htan_*_typos
        OR
        tasks:
          - task1
          - task2
    """
    lines = issue_body.split('\n')

    # Try GitHub form format first
    in_pattern_section = False
    in_list_section = False

    for i, line in enumerate(lines):
        line_stripped = line.strip()

        # Check for form headers
        if line_stripped == "### Task Pattern (if using Pattern Matching)":
            in_pattern_section = True
            in_list_section = False
            continue
        elif line_stripped == "### Task List (if using Explicit List)":
            in_list_section = True
            in_pattern_section = False
            continue
        elif line_stripped.startswith("###"):
            # End of current section
            in_pattern_section = False
            in_list_section = False
            continue

        # Extract pattern from form
        if in_pattern_section and line_stripped and not line_stripped.startswith("_") and not line_stripped == "No response":
            pattern = line_stripped
            return expand_task_pattern(pattern)

        # Extract list from form
        if in_list_section and line_stripped and not line_stripped.startswith("_") and not line_stripped == "No response":
            # Split by newlines and filter empty
            tasks = [t.strip() for t in line_stripped.split('\n') if t.strip()]
            if tasks:
                return tasks

    # Fallback to legacy YAML parsing
    tasks = []
    in_task_list = False

    for line in lines:
        line = line.strip()

        # Single task format
        if line.startswith('task:') and not line.startswith('tasks:'):
            task = line.split('task:')[1].strip()
            tasks.append(task)
            continue

        # Multiple tasks header
        if line.startswith('tasks:'):
            rest = line.split('tasks:')[1].strip()
            if rest:  # Inline pattern
                # Expand pattern
                expanded = expand_task_pattern(rest)
                tasks.extend(expanded)
            else:  # List format
                in_task_list = True
            continue

        # Task list items
        if in_task_list:
            if line.startswith('-'):
                task = line[1:].strip()
                if task:
                    tasks.append(task)
            elif line and not line.startswith('#'):
                # End of list
                in_task_list = False

    if not tasks:
        raise ValueError(
            "No tasks specified. Use:\n"
            "  task: <single_task>\n"
            "  OR\n"
            "  tasks: <pattern>\n"
            "  OR\n"
            "  tasks:\n"
            "    - task1\n"
            "    - task2"
        )

    return tasks


def expand_task_pattern(pattern: str) -> List[str]:
    """
    Expand task pattern using glob matching.

    Examples:
      htan_demographics_* → [htan_demographics_typos, htan_demographics_synonyms, ...]
      htan_*_typos → [htan_demographics_typos, htan_biospecimen_typos, ...]
      htan_* → all HTAN tasks
    """
    tasks_dir = Path("tasks")

    if not tasks_dir.exists():
        raise ValueError(f"Tasks directory not found: {tasks_dir}")

    # Find matching task directories
    pattern_path = tasks_dir / pattern
    matches = glob.glob(str(pattern_path))

    # Extract task names (relative to tasks/)
    task_names = []
    for match in matches:
        task_path = Path(match)
        if task_path.is_dir():
            task_names.append(task_path.name)

    task_names.sort()

    if not task_names:
        raise ValueError(f"No tasks found matching pattern: {pattern}")

    return task_names


def extract_model(issue_body: str) -> str:
    """Extract model name from GitHub issue body."""
    lines = issue_body.split('\n')

    # Try GitHub form format first
    in_model_section = False
    in_custom_model_section = False

    for line in lines:
        line_stripped = line.strip()

        # Check for form headers
        if line_stripped == "### Model":
            in_model_section = True
            in_custom_model_section = False
            continue
        elif line_stripped == "### Custom Model (if selected \"Other\")":
            in_custom_model_section = True
            in_model_section = False
            continue
        elif line_stripped.startswith("###"):
            # End of current section
            in_model_section = False
            in_custom_model_section = False
            continue

        # Extract model from form
        if in_model_section and line_stripped and not line_stripped.startswith("_") and not line_stripped == "No response":
            # Handle dropdown format (may have description in parentheses)
            model = line_stripped.split('(')[0].strip()
            return model

        # Extract custom model from form
        if in_custom_model_section and line_stripped and not line_stripped.startswith("_") and not line_stripped == "No response":
            return line_stripped

    # Fallback to legacy YAML format
    for line in lines:
        if line.startswith('model:'):
            return line.split('model:')[1].strip()

    raise ValueError("No model specified (expected 'model: <model_name>')")


def extract_num_runs(issue_body: str, default: int = 10) -> int:
    """Extract number of runs from GitHub issue body."""
    lines = issue_body.split('\n')

    # Try GitHub form format first
    in_num_runs_section = False

    for line in lines:
        line_stripped = line.strip()

        # Check for form header
        if line_stripped == "### Number of Runs per Task":
            in_num_runs_section = True
            continue
        elif line_stripped.startswith("###"):
            # End of current section
            in_num_runs_section = False
            continue

        # Extract num_runs from form
        if in_num_runs_section and line_stripped and not line_stripped.startswith("_") and not line_stripped == "No response":
            try:
                return int(line_stripped)
            except ValueError:
                return default

    # Fallback to legacy YAML format
    for line in lines:
        if line.startswith('num_runs:') or line.startswith('runs:'):
            try:
                return int(line.split(':')[1].strip())
            except (ValueError, IndexError):
                return default

    return default


def run_stability_test_single(
    task_name: str,
    model: str,
    num_runs: int = 10,
    temperature: float = 0.0
) -> Dict[str, Any]:
    """Run stability test for a single task."""
    print(f"\n{'='*70}")
    print(f"Task: {task_name}")
    print(f"{'='*70}")

    results_per_run = []

    for run_idx in range(num_runs):
        print(f"  Run {run_idx + 1}/{num_runs}...", end=' ', flush=True)

        try:
            experiment = Experiment(
                model=model,
                task_names=[task_name],
                temperature=temperature
            )

            run_results = experiment.run(update_other_experiments=False)

            if task_name in run_results:
                results_per_run.append(run_results[task_name])
                overall = run_results[task_name].get('overall_metrics', {})
                score = overall.get('average_score', 0)
                print(f"✓ Score: {score:.3f}")
            else:
                print(f"✗ Failed")

        except Exception as e:
            print(f"✗ Error: {e}")

    if not results_per_run:
        return {
            'task_name': task_name,
            'model': model,
            'num_runs_attempted': num_runs,
            'num_runs_completed': 0,
            'error': 'All runs failed'
        }

    return aggregate_stability_metrics(results_per_run, task_name, model, num_runs)


def aggregate_stability_metrics(
    results: List[Dict[str, Any]],
    task_name: str,
    model: str,
    num_runs: int
) -> Dict[str, Any]:
    """Compute mean, std, and 95% CI for all metrics."""
    metrics_to_aggregate = [
        'average_score',
        'average_f1',
        'average_precision',
        'average_recall',
        'average_confidence'
    ]

    aggregated = {
        'task_name': task_name,
        'model': model,
        'num_runs_attempted': num_runs,
        'num_runs_completed': len(results),
        'timestamp': datetime.now().isoformat()
    }

    for metric in metrics_to_aggregate:
        values = []
        for r in results:
            overall = r.get('overall_metrics', {})
            if metric in overall:
                val = overall[metric]
                if val is not None:
                    values.append(val)

        if values:
            mean_val = statistics.mean(values)
            std_val = statistics.stdev(values) if len(values) > 1 else 0.0
            ci_margin = 1.96 * (std_val / (len(values) ** 0.5))

            metric_short = metric.replace('average_', '')
            aggregated[metric_short] = {
                'mean': mean_val,
                'std': std_val,
                'ci_lower': mean_val - ci_margin,
                'ci_upper': mean_val + ci_margin,
                'min': min(values),
                'max': max(values),
                'median': statistics.median(values)
            }

    return aggregated


def run_batch_stability_test(
    tasks: List[str],
    model: str,
    num_runs: int = 10,
    temperature: float = 0.0
) -> Dict[str, Any]:
    """Run stability tests for multiple tasks."""
    print(f"\n{'█'*70}")
    print(f"BATCH STABILITY TEST")
    print(f"{'█'*70}")
    print(f"Tasks: {len(tasks)}")
    print(f"Model: {model}")
    print(f"Runs per task: {num_runs}")
    print(f"Temperature: {temperature}")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"{'█'*70}\n")

    task_results = {}
    successful_tasks = 0
    failed_tasks = 0

    for idx, task in enumerate(tasks, 1):
        print(f"\n[{idx}/{len(tasks)}] Processing: {task}")

        try:
            result = run_stability_test_single(task, model, num_runs, temperature)
            task_results[task] = result

            if result.get('num_runs_completed', 0) > 0:
                successful_tasks += 1
                print(f"  ✅ Completed: {result['num_runs_completed']}/{num_runs} runs")
            else:
                failed_tasks += 1
                print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            failed_tasks += 1
            print(f"  ❌ Error: {e}")
            task_results[task] = {
                'task_name': task,
                'model': model,
                'num_runs_attempted': num_runs,
                'num_runs_completed': 0,
                'error': str(e)
            }

    # Create batch summary
    batch_summary = {
        'batch_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
        'model': model,
        'num_runs_per_task': num_runs,
        'total_tasks': len(tasks),
        'successful_tasks': successful_tasks,
        'failed_tasks': failed_tasks,
        'tasks': list(tasks),
        'results': task_results,
        'timestamp': datetime.now().isoformat()
    }

    print(f"\n{'█'*70}")
    print(f"BATCH COMPLETE")
    print(f"{'█'*70}")
    print(f"Successful: {successful_tasks}/{len(tasks)}")
    print(f"Failed: {failed_tasks}/{len(tasks)}")
    print(f"Ended: {datetime.now().isoformat()}")
    print(f"{'█'*70}\n")

    return batch_summary


def save_batch_summary(summary: Dict[str, Any], output_dir: Path):
    """Save batch stability summary to JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save main batch summary
    summary_path = output_dir / "batch_stability_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\nBatch summary saved to: {summary_path}")

    # Save individual task summaries
    for task_name, result in summary['results'].items():
        if result.get('num_runs_completed', 0) > 0:
            task_safe = task_name.replace('/', '_')
            task_path = output_dir / f"stability_{task_safe}.json"
            with open(task_path, 'w') as f:
                json.dump(result, f, indent=2)


def print_batch_summary(summary: Dict[str, Any]):
    """Print formatted batch summary."""
    print(f"\n{'='*70}")
    print(f"BATCH STABILITY SUMMARY")
    print(f"{'='*70}")
    print(f"Model: {summary['model']}")
    print(f"Tasks: {summary['successful_tasks']}/{summary['total_tasks']} successful")
    print(f"Runs per task: {summary['num_runs_per_task']}")
    print(f"\n{'─'*70}\n")

    # Sort tasks by score (highest first)
    results_with_scores = [
        (task, result)
        for task, result in summary['results'].items()
        if result.get('score') is not None
    ]
    results_with_scores.sort(
        key=lambda x: x[1]['score']['mean'],
        reverse=True
    )

    # Print top performers
    print("Top Performing Tasks (by mean score):\n")
    for idx, (task, result) in enumerate(results_with_scores[:5], 1):
        score = result['score']
        print(f"{idx}. {task}")
        print(f"   Score: {score['mean']:.3f} ± {score['std']:.3f}")
        if 'f1' in result:
            print(f"   F1: {result['f1']['mean']:.3f}")
        print()

    # Print low performers
    if len(results_with_scores) > 5:
        print(f"{'─'*70}\n")
        print("Lowest Performing Tasks (by mean score):\n")
        for idx, (task, result) in enumerate(results_with_scores[-5:], 1):
            score = result['score']
            print(f"{idx}. {task}")
            print(f"   Score: {score['mean']:.3f} ± {score['std']:.3f}")
            if 'f1' in result:
                print(f"   F1: {result['f1']['mean']:.3f}")
            print()

    print(f"{'='*70}\n")


def main():
    """Main entry point for batch stability testing."""
    if len(sys.argv) < 3:
        print("Usage: python -m src.stability_runner_batch '<issue_body>' '<issue_number>'")
        print("\nExpected issue body format:")
        print("\n  # Single task:")
        print("  task: htan_demographics_typos")
        print("  model: claude-sonnet-4-5-20250929")
        print("  num_runs: 10")
        print("\n  # Pattern matching:")
        print("  tasks: htan_demographics_*")
        print("  model: claude-sonnet-4-5-20250929")
        print("  num_runs: 10")
        print("\n  # Multiple tasks:")
        print("  tasks:")
        print("    - htan_demographics_typos")
        print("    - htan_demographics_synonyms")
        print("    - htan_demographics_imputation")
        print("  model: claude-sonnet-4-5-20250929")
        print("  num_runs: 10")
        sys.exit(1)

    issue_body = sys.argv[1]
    issue_number = sys.argv[2]

    try:
        # Extract parameters
        tasks = extract_tasks(issue_body)
        model = extract_model(issue_body)
        num_runs = extract_num_runs(issue_body)

        print(f"\nParsed configuration:")
        print(f"  Tasks: {len(tasks)}")
        for task in tasks:
            print(f"    - {task}")
        print(f"  Model: {model}")
        print(f"  Runs: {num_runs}")

        # Run batch stability test
        summary = run_batch_stability_test(tasks, model, num_runs)

        # Save results
        results_dir = Path("docs/results")
        save_batch_summary(summary, results_dir)

        # Print summary
        print_batch_summary(summary)

        print(f"\n✅ Batch stability test completed!")
        print(f"   Issue #{issue_number} can be closed.")

    except Exception as e:
        print(f"\n❌ Batch stability test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
