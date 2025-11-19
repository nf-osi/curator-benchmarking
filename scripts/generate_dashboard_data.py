#!/usr/bin/env python3
"""Generate minified dashboard data file from experiment results."""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional


def load_experiments_log(log_file: Path) -> List[Dict[str, Any]]:
    """Load and deduplicate experiments from log file."""
    if not log_file.exists():
        return []
    
    experiments = []
    with open(log_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('<<<<<<<') or line.startswith('=======') or line.startswith('>>>>>>>'):
                continue
            try:
                exp = json.loads(line)
                experiments.append(exp)
            except:
                continue
    
    # Deduplicate by experiment_id, keeping most recent
    experiment_map = {}
    for exp in experiments:
        exp_id = exp.get('experiment_id')
        if exp_id:
            existing = experiment_map.get(exp_id)
            if not existing or exp.get('timestamp', '') > existing.get('timestamp', ''):
                experiment_map[exp_id] = exp
    
    return list(experiment_map.values())


def load_task_result(task_file: Path) -> Optional[Dict[str, Any]]:
    """Load a task result file and extract only needed data."""
    if not task_file.exists():
        return None
    
    try:
        with open(task_file, 'r') as f:
            data = json.load(f)
        
        task_result = data.get('task_result', {})
        if task_result.get('error'):
            return None
        
        # Extract only what's needed for display
        metrics = task_result.get('metrics', {})
        return {
            'average_score': metrics.get('average_score'),
            'duration_seconds': task_result.get('duration_seconds', 0),
            'token_usage': task_result.get('token_usage', {})
        }
    except Exception as e:
        print(f"Warning: Could not load {task_file}: {e}", file=sys.stderr)
        return None


def generate_dashboard_data(results_dir: Path, output_file: Path, tasks_dir: Optional[Path] = None):
    """Generate minified dashboard data file."""
    log_file = results_dir / "experiments_log.jsonl"
    
    # Load experiments from log
    experiments = load_experiments_log(log_file)
    print(f"Loaded {len(experiments)} experiments from log")
    
    # Get all valid task names from the tasks directory (source of truth)
    # This ensures we count all tasks, even if some experiments don't have results for all tasks yet
    known_task_names = set()
    
    if tasks_dir and Path(tasks_dir).exists():
        tasks_path = Path(tasks_dir)
        for task_dir in sorted(tasks_path.iterdir()):
            if task_dir.is_dir() and task_dir.name != 'example_task':
                known_task_names.add(task_dir.name)
        print(f"Found {len(known_task_names)} tasks in tasks directory")
    else:
        # Fallback: discover from result files
        for file in results_dir.glob('*.json'):
            if '_' in file.stem:
                # Extract task name from filename pattern: experiment_id_taskname.json
                parts = file.stem.split('_', 1)
                if len(parts) == 2:
                    known_task_names.add(parts[1])
        
        # Final fallback to hardcoded list if still empty
        if not known_task_names:
            known_task_names = {
                'broadening_of_narrow_synonyms',
                'correction_of_typos',
                'narrowing_of_broad_synonyms',
                'translation_of_exact_synonyms',
                'regex_generation',
                'column_enumeration',
                'column_type_identification',
                'validation_error_counting',
                'row_validation_explanation',
                'column_value_retrieval',
                'row_value_retrieval',
                'uppercase_conversion'
            }
    
    known_task_names = sorted(known_task_names)
    print(f"Using {len(known_task_names)} tasks: {', '.join(known_task_names)}")
    
    dashboard_data = []
    
    for exp in experiments:
        exp_id = exp.get('experiment_id')
        if not exp_id:
            continue
        
        # Initialize experiment data
        exp_data = {
            'experiment_id': exp_id,
            'model_id': exp.get('model_id', ''),
            'system_instructions': exp.get('system_instructions', ''),
            'temperature': exp.get('temperature'),
            'thinking': exp.get('thinking', False),
            'tools': [],
            'overall_metrics': {
                'total_samples': 0,
                'tasks_completed': 0,
                'tasks_failed': 0,
                'average_accuracy': None,
                'duration_seconds': 0,
                'token_usage': {
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'total_tokens': 0
                }
            },
            'task_results': {}
        }
        
        # Load task results
        total_samples = 0
        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0
        total_duration = 0
        all_scores = []
        tasks_completed = 0
        tasks_failed = 0
        
        for task_name in known_task_names:
            task_file = results_dir / f"{exp_id}_{task_name}.json"
            task_result = load_task_result(task_file)
            
            if task_result:
                # Extract metadata from first task file
                if tasks_completed == 0:
                    try:
                        with open(task_file, 'r') as f:
                            task_data = json.load(f)
                        exp_data['system_instructions'] = task_data.get('system_instructions', exp_data['system_instructions'])
                        exp_data['temperature'] = task_data.get('temperature', exp_data['temperature'])
                        exp_data['thinking'] = task_data.get('thinking', exp_data['thinking'])
                        exp_data['tools'] = task_data.get('tools', [])
                    except:
                        pass
                
                exp_data['task_results'][task_name] = task_result
                tasks_completed += 1
                
                # Aggregate metrics
                if task_result.get('average_score') is not None:
                    all_scores.append(task_result['average_score'])
                
                token_usage = task_result.get('token_usage', {})
                total_input_tokens += token_usage.get('input_tokens', 0)
                total_output_tokens += token_usage.get('output_tokens', 0)
                total_tokens += token_usage.get('total_tokens', 0)
                total_duration += task_result.get('duration_seconds', 0)
            else:
                # Task file doesn't exist - this is expected for older experiments
                # Count it as failed if we're checking all known tasks
                tasks_failed += 1
        
        # Calculate overall metrics
        if tasks_completed > 0:
            exp_data['overall_metrics'] = {
                'total_samples': total_samples,
                'tasks_completed': tasks_completed,
                'tasks_failed': tasks_failed,
                'average_accuracy': sum(all_scores) / len(all_scores) if all_scores else None,
                'duration_seconds': total_duration,
                'token_usage': {
                    'input_tokens': total_input_tokens,
                    'output_tokens': total_output_tokens,
                    'total_tokens': total_tokens
                }
            }
            
            dashboard_data.append(exp_data)
    
    # Write minified data file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(dashboard_data, f, separators=(',', ':'))  # Compact JSON
    
    file_size = output_file.stat().st_size
    print(f"Generated dashboard data file: {output_file}")
    print(f"  Experiments: {len(dashboard_data)}")
    print(f"  File size: {file_size / 1024:.1f} KB")
    
    # Compare with original size
    total_original_size = 0
    for exp_data in dashboard_data:
        exp_id = exp_data['experiment_id']
        for task_name in known_task_names:
            task_file = results_dir / f"{exp_id}_{task_name}.json"
            if task_file.exists():
                total_original_size += task_file.stat().st_size
    
    if total_original_size > 0:
        reduction = (1 - file_size / total_original_size) * 100
        print(f"  Original size: {total_original_size / 1024 / 1024:.1f} MB")
        print(f"  Size reduction: {reduction:.1f}%")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_dashboard_data.py <results_dir> [output_file] [tasks_dir]")
        sys.exit(1)
    
    results_dir = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    else:
        output_file = results_dir / "dashboard_data.json"
    
    # Get tasks directory (default to 'tasks' relative to script location)
    if len(sys.argv) > 3:
        tasks_dir = Path(sys.argv[3])
    else:
        # Default to 'tasks' directory relative to repo root
        script_dir = Path(__file__).parent
        repo_root = script_dir.parent
        tasks_dir = repo_root / "tasks"
    
    generate_dashboard_data(results_dir, output_file, tasks_dir)

