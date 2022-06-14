from typing import List, Union, TypeVar
import pandas as pd


from pandas import Series
import numpy as np


# To specify type hints for series
SeriesListOfFloats = TypeVar("pandas.core.series.Series(List[float])")
SeriesOfFloats = TypeVar("pandas.core.series.Series(float)")
SeriesOfStr = TypeVar("pandas.core.series.Series(str)")
SeriesOfInt = TypeVar("pandas.core.series.Series(int)")


def scores_to_probs(scores: Union[SeriesListOfFloats, SeriesOfFloats]) -> Series:
    """Converts a series of lists of softmax scores to probabilities. Assumes input scores to be
    a list of floats of maximum length 2.

    Args:
        scores (Union[Series[List[float]], Series[float]]): Series containing output
        from softmax from a binary classification or raw probabilities

    Returns:
        Series: Probability of class 1
    """

    if scores.dtype == "float":
        return scores
    else:
        return scores.apply(lambda x: x[1])


def labels_to_int(labels: Union[SeriesOfStr, SeriesOfInt], label2id: dict) -> Series:
    """Converts label to int mapping. Only makes sense for binary models. If
    already int will return as is.

    Args:
        labels (Union[Series[str], Series[int]]): Series containing labels.
        Either as string (e.g. "ASD") or as int.
        label2id (dict): Dictionary mapping the labels to 0 and 1

    Returns:
        Series: _description_
    """
    if labels.dtype == "int":
        return labels
    else:
        return labels.apply(lambda x: label2id[x])


def aggregate_predictions(
    df: pd.DataFrame, id_col: str, predictions_col: str, label_col: str
):
    """Calculates the mean prediction by a grouping col (id_col).

    Args:
        df (pd.DataFrame): Dataframe with 'scores_col', 'label_col' and `id_col` columns
        id_col (str): Column to group by
        predictions_col (str): column containing predictions
        label_col (str): column containing labels
    """

    def mean_scores(x: pd.Series):
        gathered = np.stack(x)
        return gathered.mean(axis=0)

    def get_first_entry(x: pd.Series):
        return x.unique()[0]

    return df.groupby(id_col).agg(
        {predictions_col: mean_scores, label_col: get_first_entry}
    )


def idx_to_class(idx: List[int], mapping: dict) -> List[str]:
    """Returns the label from an id2label mapping

    Args:
        idx (List[int]): index
        mapping (dict): dictionary mapping index to label

    Returns:
        List[str]: Labels matching the indices
    """
    return [mapping[id] for id in idx]


def get_metadata_cols(
    df: pd.DataFrame, cols: List[str], skip: List[str]
) -> pd.DataFrame:
    """Extracts model metadata to a 1 row dataframe

    Args:
        df (pd.DataFrame): Dataframe with predictions and metadata.
        cols (List[str]): Which columns contain metadata.
            The columns should only contain a single value.
        skip (List[str]): columns to definitely not include.

    Raises:
        ValueError: If a metadata col contains more than a single unique value.

    Returns:
        pd.DataFrame: 1 row dataframe with metadata
    """

    metadata = {}

    # if metadata not specified save all columns with only 1 unique value
    if cols[0] == "all":
        for col in df.columns:
            # Necessary to skip predictions column if it is a list, otherwise errors
            if col in skip:
                continue
            n_unique = df[col].nunique()
            if n_unique == 1:
                metadata[col] = df[col].unique()[0]

    # otherwise iterate over specified columns
    else:
        all_columns = df.columns
        for col in cols:
            if col in all_columns:
                val = df[col].unique()
                if len(val) > 1:
                    raise ValueError(
                        f"The column '{col}' contains more than one unique value."
                    )
                metadata[col] = val[0]
            else:
                raise ValueError(
                    f"The metadata column '{col}' is not contained in the data"
                )
    return pd.DataFrame.from_records([metadata])


def add_metadata_cols(df: pd.DataFrame, metadata: pd.DataFrame) -> pd.DataFrame:
    """Adds 1 row dataframe with metadata to the long format performance dataframe

    Args:
        df (pd.DataFrame): Dataframe to add metadata to.
        metadata (pd.Dataframe): 1 row dataframe with metadata

    Returns:
        pd.DataFrame: Dataframe with added metadata
    """
    nrows = df.shape[0]

    meta_dict = {}
    for col in metadata.columns:
        meta_dict[col] = [metadata[col][0]] * nrows
    meta_df = pd.DataFrame.from_records(meta_dict)

    return df.reset_index(drop=True).join(meta_df)


####### For model plotter (that has been removed for now)
def string_to_list(str_or_list: Union[List, str]):
    """Converts

    Args:
        str_or_list (Union[List, str]): _description_

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """
    if isinstance(str_or_list, str):
        return [str_or_list]
    elif isinstance(str_or_list, list):
        return str_or_list
    else:
        raise ValueError(f"{str_or_list} is neither a string nor list")


def subset_df_from_dict(df: pd.DataFrame, subset_by: dict):
    for col, value in subset_by.items():
        df = df[df[col] == value]
    return df


if __name__ == "__main__":
    df = pd.DataFrame(
        {
            "id": [1, 1, 2, 2],
            "scores": [
                [0.1, 0.7, 0.1, 0.1],
                [0.1, 0.7, 0.1, 0.1],
                [0.1, 0.1, 0.7, 0.1],
                [0.1, 0.7, 0.1, 0.1],
            ],
            "label": ["ASD", "ASD", "TD", "TD"],
        }
    )

    aggregate_predictions(df, "id")
