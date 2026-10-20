"""Load the authorized sales dataset for ResearchMind."""

from pathlib import Path

import pandas as pd

DEFAULT_DATASET_PATH = Path("data/raw/BaseVendas.csv")
MAX_DATASET_ROWS = 1000


def load_sales_data(
    file_path: str | Path = DEFAULT_DATASET_PATH,
) -> pd.DataFrame:
    """Load at most the first 1,000 data rows from the sales CSV."""
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Sales dataset not found: {path}. Place BaseVendas.csv in data/raw/."
        )

    try:
        data = pd.read_csv(
            path,
            sep=";",
            encoding="utf-8-sig",
            nrows=MAX_DATASET_ROWS,
        )
    except (pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise ValueError(
            "Could not read the sales dataset. Check its encoding and delimiter."
        ) from exc

    if data.empty:
        raise ValueError("The sales dataset contains no data rows.")

    return data


def get_sales_data_summary(
    file_path: str | Path = DEFAULT_DATASET_PATH,
) -> dict[str, object]:
    """Return a summary of the authorized dataset."""
    data = load_sales_data(file_path)

    return {
        "rows": len(data),
        "columns": data.columns.tolist(),
        "column_types": {column: str(dtype) for column, dtype in data.dtypes.items()},
    }
