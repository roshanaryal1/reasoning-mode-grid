"""modegrid: model x mode grid harness for LA-P4, "Reasoning Mode Beats Model Identity".

The package covers the whole study pipeline:

    plan     expand configs/grid.yaml into a randomised run manifest
    run      execute API runs and write capture files
    blind    build blinded rater packets
    unblind  map rater scores back to runs
    agreement  Krippendorff's alpha per rubric dimension
    analyze  variance decomposition (mode vs model vs residual) per dimension
"""

__version__ = "0.1.0"

DIMS: tuple[str, ...] = tuple(f"D{i}" for i in range(1, 10))

DIM_NAMES: dict[str, str] = {
    "D1": "hardware-constraint",
    "D2": "recency",
    "D3": "tool-factuality",
    "D4": "model-factuality",
    "D5": "benchmark-factuality",
    "D6": "citation-quality",
    "D7": "actionability",
    "D8": "security-model",
    "D9": "internal-consistency",
}

# The two harmonised mode levels used in the confirmatory analysis.
PRIMARY_MODES: tuple[str, str] = ("fast", "reasoning")
