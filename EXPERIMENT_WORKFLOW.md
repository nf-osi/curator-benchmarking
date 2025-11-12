# Experiment Submission Workflow

This document describes the GitHub issue-based workflow for submitting experiments.

## Overview

Experiments are submitted by creating a GitHub issue using the "Experiment Submission" template. When an issue is created or edited with the `experiment` label, a GitHub Action automatically:

1. Parses the issue to extract experiment parameters
2. Runs the experiment
3. Posts results as a comment on the issue
4. Closes the issue when complete

## Step-by-Step Guide

### 1. Create a New Issue

1. Go to the Issues tab in your repository
2. Click "New Issue"
3. Select "Experiment Submission" template
4. Fill out the form

### 2. Fill Out the Form

#### Required Fields

- **Task**: Select from dropdown or enter custom task name
  - The dropdown is populated with available tasks
  - If your task isn't listed, enter it in "Custom Task Name"
  - Update the template: `python scripts/update_issue_template.py`

#### Optional Fields

- **Model Endpoint**: Leave empty to use default (`global.anthropic.claude-sonnet-4-5-20250929-v1:0`)
- **System Instructions**: 
  - Reference a file: `file:path/to/instructions.txt`
  - Or paste directly
  - Leave empty to use default
- **Prompt**:
  - Reference a file: `file:path/to/prompt.txt`
  - Or paste directly
  - Leave empty to use task default
- **Experiment Description**: Optional description of what you're testing

### 3. Submit the Issue

1. Check the confirmation boxes
2. Click "Submit new issue"
3. The `experiment` label is automatically applied

### 4. Monitor Progress

- The GitHub Action will start automatically
- You can watch progress in the Actions tab
- Results will be posted as a comment when complete
- The issue will be automatically closed on success

## File References

You can reference files in the repository for system instructions or prompts:

```
file:prompts/my_custom_prompt.txt
file:instructions/metadata_curation_v2.txt
```

Paths are relative to the repository root.

## Example Issue

```
### Task
example_task

### Model Endpoint
global.anthropic.claude-3-5-sonnet-20241022-v2:0

### System Instructions
file:instructions/custom_instructions.txt

### Prompt
Please correct the following metadata entry. Return as JSON.

### Experiment Description
Testing Claude 3.5 Sonnet on metadata correction with custom instructions.
```

## Troubleshooting

### Issue Not Triggering Workflow

- Ensure the issue has the `experiment` label
- Check that the issue body follows the template format
- Verify GitHub Actions are enabled for the repository

### Experiment Fails

- Check the Actions tab for error logs
- Verify AWS credentials are set in repository secrets
- Ensure the task directory exists and has required files
- Check that the model endpoint is valid

### Results Not Posted

- Check Actions logs for errors
- Verify the workflow has permission to write comments
- Check repository settings → Actions → General → Workflow permissions

## Manual Processing

If you need to process an issue manually (e.g., for testing):

1. Save the issue body to a file
2. Run: `python -m src.issue_processor <issue_body_file.txt>`

## Updating Available Tasks

When you add new tasks, update the issue template:

```bash
python scripts/update_issue_template.py
```

This updates the task dropdown with all available tasks in the `tasks/` directory.

