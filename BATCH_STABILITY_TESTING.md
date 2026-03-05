# Batch Stability Testing Guide

Run stability tests for multiple tasks with a single GitHub issue instead of creating 30+ issues manually.

## Quick Start

### Option 1: Use Issue Template (Recommended)

1. Go to [New Issue](https://github.com/sage-bdf/curator-benchmarking/issues/new/choose)
2. Select **"Batch Stability Test"** template
3. Fill in the form:
   - Choose "Pattern Matching" or "Explicit Task List"
   - Enter task pattern (e.g., `htan_*_typos`) OR list tasks
   - Select model
   - Enter number of runs (default: 10)
4. Submit issue

The template automatically:
- ✅ Adds `batch-stability-test` label
- ✅ Sets title prefix `[Batch Stability Test]`
- ✅ Provides structured form with examples
- ✅ Triggers workflow immediately

### Option 2: Manual Issue (Legacy)

Create a GitHub issue manually with:
- **Title**: `[Batch Stability Test] <Description>`
- **Label**: `batch-stability-test`
- **Body**: Task specification (see formats below)

---

## Issue Body Formats

### 1. Pattern Matching (Recommended for bulk testing)

Test all demographics tasks:
```yaml
tasks: htan_demographics_*
model: claude-sonnet-4-5-20250929
num_runs: 10
```

Test all typos tasks:
```yaml
tasks: htan_*_typos
model: claude-sonnet-4-5-20250929
num_runs: 10
```

Test ALL HTAN tasks (39 tasks):
```yaml
tasks: htan_*
model: claude-sonnet-4-5-20250929
num_runs: 10
```

### 2. Explicit List

Test specific tasks:
```yaml
tasks:
  - htan_demographics_typos
  - htan_demographics_synonyms
  - htan_demographics_imputation
  - htan_biospecimen_typos
  - htan_diagnosis_imputation
model: claude-sonnet-4-5-20250929
num_runs: 10
```

### 3. Single Task (fallback to original workflow)

```yaml
task: htan_demographics_typos
model: claude-sonnet-4-5-20250929
num_runs: 10
```

---

## Pattern Examples

| Pattern | Matches | Count |
|---------|---------|-------|
| `htan_demographics_*` | All demographics tasks (typos, synonyms, imputation) | 3 |
| `htan_biospecimen_*` | All biospecimen tasks | 3 |
| `htan_*_typos` | All typos tasks across schemas | 13 |
| `htan_*_synonyms` | All synonyms tasks | 13 |
| `htan_*_imputation` | All imputation tasks | 13 |
| `htan_bulk_wes_*` | All bulk WES tasks (level1, 2, 3 × 3 types) | 9 |
| `htan_*` | ALL HTAN tasks | 39 |

---

## Recommended Batches

### Batch 1: Simple Tasks (3 tasks, ~30 min)
```yaml
tasks: htan_demographics_*
model: claude-sonnet-4-5-20250929
num_runs: 10
```

### Batch 2: All Typos Tasks (13 tasks, ~2-3 hours)
```yaml
tasks: htan_*_typos
model: claude-sonnet-4-5-20250929
num_runs: 10
```

### Batch 3: All Synonyms Tasks (13 tasks, ~2-3 hours)
```yaml
tasks: htan_*_synonyms
model: claude-sonnet-4-5-20250929
num_runs: 10
```

### Batch 4: All Imputation Tasks (13 tasks, ~2-3 hours)
```yaml
tasks: htan_*_imputation
model: claude-sonnet-4-5-20250929
num_runs: 10
```

### Batch 5: Full Test Suite (39 tasks, ~6-8 hours)
```yaml
tasks: htan_*
model: claude-sonnet-4-5-20250929
num_runs: 10
```

---

## Results Format

The workflow will post a comment with:

### Summary Table

| Task | Score | F1 | Precision | Recall | Stability |
|------|-------|----|-----------|---------|-----------  |
| `htan_demographics_typos` | 0.850 | 0.820 | 0.880 | 0.780 | ✅ |
| `htan_demographics_synonyms` | 0.820 | 0.800 | 0.850 | 0.760 | ⚠️ |
| `htan_demographics_imputation` | 0.750 | 0.720 | 0.800 | 0.680 | ❗ |

**Stability Legend:**
- ✅ Highly stable (std dev < 0.05)
- ⚠️ Moderately stable (std dev 0.05-0.10)
- ❗ Low stability (std dev > 0.10)

### Expandable Detailed Metrics

Click "📊 Detailed Metrics" to see full statistics for each task:
- Mean ± Std Dev
- 95% Confidence Intervals
- Min/Max ranges
- Completed/attempted runs

---

## Output Files

All results saved to `docs/results/`:

- **`batch_stability_summary.json`** - Complete batch results
- **`stability_<task>_<timestamp>.json`** - Individual task results

---

## Model Options

### Anthropic Models
```yaml
model: claude-sonnet-4-5-20250929
model: claude-opus-4-5-20251101
model: claude-3-7-sonnet-20250219
```

### AWS Bedrock ARNs
```yaml
model: global.anthropic.claude-sonnet-4-5-20250929-v1:0
model: global.anthropic.claude-opus-4-5-20251101-v1:0
```

---

## Example Issues

### Issue 1: Test All Demographics
```
Title: [Batch Stability Test] Demographics Tasks

Body:
tasks: htan_demographics_*
model: claude-sonnet-4-5-20250929
num_runs: 10

Label: batch-stability-test
```

### Issue 2: Test All Typos
```
Title: [Batch Stability Test] All Typos Tasks

Body:
tasks: htan_*_typos
model: claude-sonnet-4-5-20250929
num_runs: 10

Label: batch-stability-test
```

### Issue 3: Full Suite
```
Title: [Batch Stability Test] Complete HTAN v1.2.0 Suite

Body:
tasks: htan_*
model: claude-sonnet-4-5-20250929
num_runs: 10

Label: batch-stability-test
```

### Issue 4: Custom Selection
```
Title: [Batch Stability Test] High Priority Tasks

Body:
tasks:
  - htan_biospecimen_imputation
  - htan_diagnosis_synonyms
  - htan_molecular_test_typos
  - htan_demographics_imputation
model: claude-sonnet-4-5-20250929
num_runs: 10

Label: batch-stability-test
```

---

## Tips

### Run Time Estimation
- **Per task**: ~10-15 minutes (10 runs × ~1 min per run)
- **3 tasks**: ~30-45 minutes
- **13 tasks**: ~2-3 hours
- **39 tasks**: ~6-8 hours

### Cost Estimation (Sonnet 4.5)
- **Per run**: ~$0.10-0.30 (varies by task complexity)
- **Per task (10 runs)**: ~$1-3
- **Full suite (39 tasks × 10 runs)**: ~$40-120

### Best Practices
1. **Start small**: Test with `htan_demographics_*` (3 tasks) first
2. **Error type batches**: Run all typos, then synonyms, then imputation
3. **Schema batches**: Test by complexity (simple schemas first)
4. **Parallel testing**: Create multiple issues for different error types simultaneously

### Troubleshooting
- **Pattern not matching**: Check task names with `ls tasks/htan_*`
- **Workflow not triggering**: Ensure label is `batch-stability-test` or `stability-test`
- **Some tasks failing**: Check individual task logs in workflow output
- **Rate limits**: Space out large batches or reduce num_runs

---

## Comparison with Single-Task Workflow

| Feature | Single Task | Batch Testing |
|---------|------------|---------------|
| Issues to create | 1 per task (39 for full suite) | 1 for multiple tasks |
| Manual effort | High (create 39 issues) | Low (create 1 issue) |
| Results format | Individual comments | Aggregated table + details |
| Comparison | Manual across issues | Automatic in single view |
| Best for | Testing 1-5 tasks | Testing 6+ tasks |

---

## Advanced: Progressive Testing Strategy

### Phase 1: Sanity Check (1 issue, ~30 min)
```yaml
tasks: htan_demographics_*
model: claude-sonnet-4-5-20250929
num_runs: 10
```
Verify workflow works and model performs reasonably.

### Phase 2: Error Type Coverage (3 issues, ~6-9 hours total)
Create 3 separate issues to run in parallel:

**Issue A: All Typos**
```yaml
tasks: htan_*_typos
model: claude-sonnet-4-5-20250929
num_runs: 10
```

**Issue B: All Synonyms**
```yaml
tasks: htan_*_synonyms
model: claude-sonnet-4-5-20250929
num_runs: 10
```

**Issue C: All Imputation**
```yaml
tasks: htan_*_imputation
model: claude-sonnet-4-5-20250929
num_runs: 10
```

### Phase 3: Analysis
Compare results across error types:
- Which error type is easiest for the model?
- Which schemas are most challenging?
- Where is stability lowest?

### Phase 4: Focused Re-testing
Create targeted batches for problem areas:
```yaml
tasks:
  - htan_biospecimen_imputation
  - htan_diagnosis_synonyms
  - htan_molecular_test_typos
model: claude-sonnet-4-5-20250929
num_runs: 20  # Increased for better stability measurement
```

---

## Local Testing

Test locally before creating GitHub issue:

```bash
cd curator-benchmarking

# Pattern matching
python -m src.stability_runner_batch \
  "tasks: htan_demographics_*
model: claude-sonnet-4-5-20250929
num_runs: 10" \
  "local-test"

# Explicit list
python -m src.stability_runner_batch \
  "tasks:
  - htan_demographics_typos
  - htan_demographics_synonyms
model: claude-sonnet-4-5-20250929
num_runs: 5" \
  "local-test"
```

---

## FAQ

**Q: Can I mix patterns and explicit tasks?**
A: No, use one format per issue. Create multiple issues if needed.

**Q: Can I cancel a running batch?**
A: Yes, cancel the workflow run in GitHub Actions. Completed results will be saved.

**Q: How do I test a subset of bulk_wes tasks?**
A: Use pattern `htan_bulk_wes_level1_*` for just level 1, or list them explicitly.

**Q: What happens if one task fails?**
A: The batch continues with remaining tasks. Failed tasks are reported separately.

**Q: Can I use different num_runs for different tasks?**
A: No, all tasks in a batch use the same num_runs. Create separate issues if needed.
