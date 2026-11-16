# NyayaBench Benchmark Versions

This file tracks all frozen benchmark sets used for NyayaBench scoring and evaluation.

## Standard Scorer Validation Set v1.0

- **File**: `nyayabench_standard_v1.json`
- **Prompts**: 50
- **Created**: 2026-03-08
- **SHA-256**: `168d5f6aa6b6e30f448d77b7023c38cf933b5571e5ee5fe7fdfcc542d62dd0c0`
- **Status**: FROZEN — do not modify
- **Purpose**: Labeled arguments for scorer validation. Each case has a ground-truth RF category.
- **Distribution**:
  - RF-01: 5, RF-02: 4, RF-03: 4, RF-04: 4, RF-05: 4
  - RF-06: 5, RF-07a: 5, RF-07b: 5, RF-08: 4, RF-09: 4
  - RF-10: 3, RF-11: 3
- **Boundary Cases**: 15 (testing problematic category boundaries)

## Reasoning Prompts Set v1.0

- **File**: `nyayabench_reasoning_prompts_v1.json`
- **Prompts**: 50
- **Created**: 2026-03-08
- **SHA-256**: `8d287b610afb48ecd8dcc4f52475d8f3bef04309557d4e56f43e63b33f3ff75f`
- **Status**: DEPRECATED — prompted meta-analysis instead of direct reasoning

## Reasoning Prompts Set v2.0

- **File**: `nyayabench_reasoning_prompts_v2.json`
- **Prompts**: 50
- **Created**: 2026-03-08
- **SHA-256**: `1877f81dfdddadb46d83df2a7dab66cf8e62acc277849d8da97d2c378813dc3c`
- **Status**: FROZEN — do not modify
- **Note**: Redesigned from v1.0 to elicit direct reasoning instead of meta-analysis. Every prompt asks for a recommendation, decision, or analysis. No prompts contain "does this prove" or "is this valid" patterns.
- **Purpose**: Open-ended reasoning questions for multi-model benchmarking. No fixed ground truth.
- **Domain Distribution**:
  - Medicine/Health: 10
  - Technology/Engineering: 10
  - Economics/Finance: 10
  - Science/Environment: 10
  - Law/Ethics/Society: 10

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2026-03-08 | Initial frozen benchmark sets |

## Integrity Verification

To verify file integrity, run:

```bash
sha256sum /app/dataset/tests/nyayabench_standard_v1.json
sha256sum /app/dataset/tests/nyayabench_reasoning_prompts_v1.json
```

The hashes must match the values listed above for the benchmark to be considered valid.
