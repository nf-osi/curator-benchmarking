#!/usr/bin/env python3
"""Update the GitHub issue template with available tasks."""
import yaml
from pathlib import Path


def get_available_tasks(tasks_dir: Path) -> list:
    """Get list of available task directories."""
    tasks_dir = Path(tasks_dir)
    if not tasks_dir.exists():
        return []
    
    return sorted([d.name for d in tasks_dir.iterdir() if d.is_dir() and not d.name.startswith('.') and d.name != 'example_task'])


def update_issue_template(template_path: Path, tasks: list):
    """Update the issue template with available tasks."""
    # Read the file as text first to preserve formatting
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Parse YAML
    template = yaml.safe_load(content)
    
    # Find the task dropdown field and update it
    for field in template['body']:
        if field.get('id') == 'task':
            field['attributes']['options'] = tasks
            break
    
    # Write back with better formatting
    with open(template_path, 'w') as f:
        # Use a custom dumper to preserve list formatting
        class CustomDumper(yaml.SafeDumper):
            def represent_list(self, data):
                return self.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=False)
        
        CustomDumper.add_representer(list, CustomDumper.represent_list)
        yaml.dump(template, f, Dumper=CustomDumper, default_flow_style=False, sort_keys=False, allow_unicode=True, width=1000)
    
    print(f"Updated issue template with {len(tasks)} tasks: {', '.join(tasks)}")


if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    tasks_dir = project_root / 'tasks'
    template_path = project_root / '.github' / 'ISSUE_TEMPLATE' / 'experiment.yml'
    
    tasks = get_available_tasks(tasks_dir)
    
    if not tasks:
        print("No tasks found. Make sure tasks are organized in the tasks/ directory.")
        exit(1)
    
    update_issue_template(template_path, tasks)

