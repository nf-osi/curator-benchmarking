#!/usr/bin/env python3
"""Synthesize a task-subset experiment from an existing completed experiment.

Copies the per-task result files for the requested tasks under the subset
experiment's ID (the same ID a real run with that Task Subset would produce),
then lets Experiment.run() aggregate from cache — no model API calls are made.

Usage:
    python scripts/synthesize_task_subset.py --source <experiment_id> \
        --tasks task_a,task_b,... [--dry-run]
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.experiment import Experiment, NaNSafeJSONEncoder  # noqa: E402

RESULTS_DIR = Path(__file__).parent.parent / "docs" / "results"
TASKS_DIR = Path(__file__).parent.parent / "tasks"

CORE_12_TASKS = [
    "broadening_of_narrow_synonyms",
    "column_enumeration",
    "column_type_identification",
    "column_value_retrieval",
    "correction_of_typos",
    "narrowing_of_broad_synonyms",
    "regex_generation",
    "row_validation_explanation",
    "row_value_retrieval",
    "translation_of_exact_synonyms",
    "uppercase_conversion",
    "validation_error_counting",
]


def synthesize(source_id: str, task_names: list, dry_run: bool = False) -> dict:
    rollup_path = RESULTS_DIR / f"{source_id}_results.json"
    if not rollup_path.exists():
        raise FileNotFoundError(f"Source rollup not found: {rollup_path}")
    with open(rollup_path) as f:
        source = json.load(f)

    if source.get("tools"):
        raise ValueError("Synthesis for experiments with tools is not supported")

    missing = [t for t in task_names if not (RESULTS_DIR / f"{source_id}_{t}.json").exists()]
    if missing:
        raise FileNotFoundError(f"Source is missing task results for: {', '.join(missing)}")

    experiment = Experiment(
        tasks_dir=TASKS_DIR,
        model_id=source["model_id"],
        system_instructions=source.get("system_instructions"),
        temperature=source.get("temperature"),
        thinking=source.get("thinking"),
        task_names=task_names,
    )
    subset_id = experiment.experiment_id
    print(f"Source experiment:  {source_id} ({source['model_id']})")
    print(f"Subset experiment:  {subset_id} ({len(task_names)} tasks)")

    if dry_run:
        return {"subset_id": subset_id}

    # Copy per-task result files under the subset ID
    for task_name in task_names:
        with open(RESULTS_DIR / f"{source_id}_{task_name}.json") as f:
            task_data = json.load(f)
        task_data["experiment_id"] = subset_id
        task_data["synthesized_from"] = source_id
        with open(RESULTS_DIR / f"{subset_id}_{task_name}.json", "w") as f:
            json.dump(task_data, f, indent=2, cls=NaNSafeJSONEncoder)

    # Aggregate from cache: all tasks resolve as unchanged, no API calls
    result = experiment.run(update_other_experiments=False)

    # Save the rollup with provenance
    result["synthesized_from"] = source_id
    result["timestamp"] = datetime.now().isoformat()
    with open(RESULTS_DIR / f"{subset_id}_results.json", "w") as f:
        json.dump(result, f, indent=2, cls=NaNSafeJSONEncoder)

    acc = result.get("overall_metrics", {}).get("average_accuracy")
    print(f"Synthesized {subset_id}: average accuracy "
          f"{acc * 100:.2f}%" if acc is not None else "(no accuracy)")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Source experiment ID")
    parser.add_argument("--tasks", default=",".join(CORE_12_TASKS),
                        help="Comma-separated task names (default: the 12 core tasks)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    task_names = [t.strip() for t in args.tasks.split(",") if t.strip()]
    synthesize(args.source, task_names, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
