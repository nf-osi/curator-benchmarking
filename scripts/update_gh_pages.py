#!/usr/bin/env python3
"""Script to update GitHub Pages with latest results."""
import shutil
import subprocess
import sys
from pathlib import Path

def main():
    repo_root = Path(__file__).parent.parent
    docs_dir = repo_root / "docs"
    results_dir = repo_root / "results"
    docs_results_dir = docs_dir / "results"
    
    # Create docs/results directory if it doesn't exist
    docs_results_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy results files to docs/results
    print("Copying results to docs/results...")
    
    copied = 0
    for file in results_dir.glob("*.json"):
        shutil.copy2(file, docs_results_dir)
        copied += 1
    
    for file in results_dir.glob("*.jsonl"):
        shutil.copy2(file, docs_results_dir)
        copied += 1
    
    print(f"Copied {copied} files to: {docs_results_dir}")
    
    # Generate minified dashboard data file
    print("\nGenerating minified dashboard data...")
    generate_script = repo_root / "scripts" / "generate_dashboard_data.py"
    try:
        result = subprocess.run(
            [sys.executable, str(generate_script), str(docs_results_dir), str(docs_results_dir / "dashboard_data.json")],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to generate dashboard data: {e}")
        print(e.stderr)
    
    print(f"\nGitHub Pages results updated successfully!")

if __name__ == "__main__":
    main()

