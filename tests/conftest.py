from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def grid_path() -> Path:
    return ROOT / "configs" / "grid.yaml"
