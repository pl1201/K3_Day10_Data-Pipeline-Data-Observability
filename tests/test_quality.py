from __future__ import annotations

import pandas as pd

from observability.quality import _duplicate_safe_dataframe


def test_duplicate_check_supports_list_columns() -> None:
    df = pd.DataFrame(
        [
            {"paper_id": "p-1", "authors": ["A", "B"], "metadata": {"kind": "paper"}},
            {"paper_id": "p-1", "authors": ["A", "B"], "metadata": {"kind": "paper"}},
        ]
    )

    assert int(_duplicate_safe_dataframe(df).duplicated().sum()) == 1
