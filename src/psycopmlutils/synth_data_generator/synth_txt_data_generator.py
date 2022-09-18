"""Script for creating synthetic text data for testing purposes.

Produces a .csv file with the following columns: citizen_id, timestamp,
text.
"""
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from psycopmlutils.synth_data_generator.synth_col_generators import (
    generate_data_columns,
)


def generate_synth_txt_data(
    predictors: Dict,
    n_samples: int,
    text_prompt: str = "The quick brown fox jumps over the lazy dog",
    na_prob: Optional[float] = 0.1,
    na_ignore_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Takes a dict and generates synth data from it.

    Args:
        predictors (Dict): A dict representing each column. Key is col_name (str), values are column_type (str), output_type (float|int), min (int), max(int).
        n_samples (int): Number of samples (rows) to generate.
        text_prompt (str): Text prompt to use for generating text data. Defaults to "The quick brown fox jumps over the lazy dog".
        na_prob (float): Probability of changing a value in a predictor column to NA.
        na_ignore_cols (List[str]): Columns to ignore when creating NAs

    Returns:
        pd.DataFrame: The synthetic dataset
    """

    # Initialise dataframe
    df = pd.DataFrame(columns=list(predictors.keys()))

    # Generate data
    df = generate_data_columns(
        predictors=predictors, n_samples=n_samples, df=df, text_prompt=text_prompt
    )

    # randomly replace predictors with NAs
    if na_prob:
        mask = np.random.choice([True, False], size=df.shape, p=[na_prob, 1 - na_prob])
        df_ = df.mask(mask)

        # For all columns in df.columns if column is not in na_ignore_cols
        for col in df.columns:
            if col not in na_ignore_cols:
                df[col] = df_[col]

    return df


if __name__ == "__main__":
    column_specifications = {
        "citizen_ids": {"column_type": "uniform_int", "min": 0, "max": 1_200_000},
        "timestamp": {"column_type": "datetime_uniform", "min": 0, "max": 5 * 365},
        "text": {"column_type": "text"},
    }

    out_df = generate_synth_txt_data(
        predictors=column_specifications,
        n_samples=100,
        text_prompt="The patient",
    )

    save_path = Path(__file__).parent.parent.parent.parent
    out_df.to_csv(save_path / "tests" / "test_data" / "synth_txt_data.csv")
