"""Tools for calculating model performance metrics."""

from pathlib import Path
from typing import Optional, Union

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from psycopmlutils.model_performance.utils import (
    add_metadata_cols,
    aggregate_predictions,
    idx_to_class,
    labels_to_int,
    scores_to_probs,
    select_metadata_cols,
)


class ModelPerformance:
    """Evaluators of model performance."""

    def performance_metrics_from_df(
        prediction_df: pd.DataFrame,
        prediction_col_name: str,
        label_col_name: str,
        id_col_name: Optional[str] = None,
        metadata_col_names: Optional[list[str]] = None,
        id2label: Optional[  # pylint: disable=redefined-outer-name
            dict[int, str]
        ] = None,
        to_wide: Optional[bool] = False,
    ) -> pd.DataFrame:
        """Calculate performance metrics from a dataframe.

        Row-level performance is identified by the `level` column as 'overall'.
        If the class was instantiated with an id_col_name, id-level performance is added and identified via the ´level´ column as 'id'.

        Args:
            prediction_df (pd.DataFrame): Dataframe with 1 row per prediction.
            prediction_col_name (str): column containing probabilities for each class or a list of floats for binary classification.
            label_col_name (str): column containing ground truth label
            id_col_name (str, optional): Column name for the id, used for grouping.
            metadata_col_names (Optional[list[str]], optional): Column(s) containing metadata to add to the performance dataframe.
                Each column should only contain 1 unique value. E.g. model_name, modality.. If set to "all" will auto-detect
                metadata columns and add them all.
            id2label (dict[int, str]): dict mapping indices to labels. Not needed for binary models if labels are 0 and 1. Defaults to None.
            to_wide (bool): Whether to return performance as wide format.

        Returns:
            pd.Dataframe: Dataframe with performance metrics.
        """

        concat_axis = 1 if to_wide else 0

        performance_description = ModelPerformance._evaluate_single_model(
            prediction_df=prediction_df,
            aggregate_by_id=False,
            prediction_col_name=prediction_col_name,
            label_col_name=label_col_name,
            id_col_name=id_col_name,
            to_wide=to_wide,
            id2label=id2label,
        )

        if id_col_name:
            # add identifier for row-level metrics
            if to_wide:
                performance_description = performance_description.add_prefix("row-")
            else:
                performance_description["level"] = "row"

            # Calculate performance by id and add to the dataframe
            performance_by_id = ModelPerformance._evaluate_single_model(
                prediction_df=prediction_df,
                aggregate_by_id=True,
                prediction_col_name=prediction_col_name,
                label_col_name=label_col_name,
                id_col_name=id_col_name,
                to_wide=to_wide,
                id2label=id2label,
            )

            performance_description = pd.concat(
                [performance_description, performance_by_id],
                axis=concat_axis,
            )

        if metadata_col_names:
            # Add metadata if specified
            metadata = select_metadata_cols(
                df=prediction_df,
                metadata_cols=metadata_col_names,
                skip_cols=[prediction_col_name, label_col_name],
            )

            performance_description = add_metadata_cols(
                performance_description,
                metadata,
            )

        return performance_description

    def performance_metrics_from_file(
        jsonl_path: Union[str, Path],
        prediction_col_name: str,
        label_col_name: str,
        id_col_name: Optional[str] = None,
        metadata_col_names: Optional[list[str]] = None,
        id2label: Optional[  # pylint: disable=redefined-outer-name
            dict[int, str]
        ] = None,
        to_wide: Optional[bool] = False,
    ) -> pd.DataFrame:
        """Load a .jsonl file and returns performance metrics.

        Args:
            jsonl_path (Union[str, Path]): Path to .jsonl file # noqa: DAR102
            prediction_col_name (str): column containing probabilities for each class or a list of floats for binary classification.
            label_col_name (str): column containing ground truth label
            id_col_name (str, optional): Column name for the id, used for grouping.
            metadata_col_names (Optional[list[str]], optional): Column(s) containing metadata to add to the performance dataframe.
                Each column should only contain 1 unique value. E.g. model_name, modality.. If set to "all" will auto-detect
                metadata columns and add them all.
            id2label (dict[int, str]): dict mapping indices to labels. Not needed for binary models if labels are 0 and 1. Defaults to None.
            to_wide (bool): Whether to return performance as wide format.

        Raises:
            ValueError: If file is not a .jsonl file

        Returns:
            pd.DataFrame: Dataframe with performance metrics
        """
        if isinstance(jsonl_path, str):
            jsonl_path = Path(jsonl_path)  # pylint: disable=self-cls-assignment

        if jsonl_path.suffix != ".jsonl":
            raise ValueError(
                f"Only .jsonl files are supported for import, not {jsonl_path.suffix}",
            )
        df = pd.read_json(jsonl_path, orient="records", lines=True)
        return ModelPerformance.performance_metrics_from_df(
            prediction_df=df,
            prediction_col_name=prediction_col_name,
            label_col_name=label_col_name,
            id_col_name=id_col_name,
            to_wide=to_wide,
            id2label=id2label,
            metadata_col_names=metadata_col_names,
        )

    def performance_metrics_from_folder(
        folder: Union[str, Path],
        pattern: str,
        prediction_col_name: str,
        label_col_name: str,
        id_col_name: Optional[str] = None,
        metadata_col_names: Optional[list[str]] = None,
        id2label: Optional[  # pylint: disable=redefined-outer-name
            dict[int, str]
        ] = None,
        to_wide=False,
    ) -> pd.DataFrame:
        """Load and calculates performance metrics for all files matching a
        pattern in a folder.

        Only supports jsonl for now.

        Args:
            folder (Union[str, Path]): Path to folder. # noqa: DAR102
            pattern (str): Pattern to match on filename.
            prediction_col_name (str): column containing probabilities for each class or a list of floats for binary classification.
            label_col_name (str): column containing ground truth label
            id_col_name (str, optional): Column name for the id, used for grouping.
            metadata_col_names (Optional[list[str]], optional): Column(s) containing metadata to add to the performance dataframe.
            id2label (dict[int, str]): dict mapping indices to labels. Not needed for binary models if labels are 0 and 1. Defaults to None.
            to_wide (bool): Whether to return performance as wide format.


        Returns:
            pd.Dataframe: Dataframe with performance metrics for each file
        """
        folder = Path(folder)  # pylint: disable=self-cls-assignment

        dfs = [
            ModelPerformance.performance_metrics_from_file(
                jsonl_path=p,
                prediction_col_name=prediction_col_name,
                label_col_name=label_col_name,
                id_col_name=id_col_name,
                metadata_col_names=metadata_col_names,
                id2label=id2label,
                to_wide=to_wide,
            )
            for p in folder.glob(pattern)
        ]
        return pd.concat(dfs)

    def _evaluate_single_model(  # pylint: disable=too-many-locals
        prediction_df: pd.DataFrame,
        aggregate_by_id: bool,
        prediction_col_name: str,
        label_col_name: str,
        id_col_name: str,
        to_wide: bool,
        id2label: dict[int, str] = None,  # pylint: disable=redefined-outer-name
    ) -> pd.DataFrame:
        """Calculate performance metrics from a dataframe. Optionally adds
        aggregated performance by id.

        Args:
            df (pd.DataFrame): Dataframe with one prediction per row # noqa: DAR102
            aggregate_by_id (bool): Whether to only calculate predictions on row level or also aggregate by id
            prediction_col_name (str): column containing probabilities for each class or a list of floats for binary classification.
            label_col_name (str): column containing ground truth label
            id_col_name (str): Column name for the id, used for grouping.
            to_wide (bool): Whether to return performance as wide format.
            id2label (dict[int, str]): dict mapping indices to labels. Not needed for binary models if labels are 0 and 1. Defaults to None.

        Returns:
            pd.Dataframe: Dataframe with performance metrics containing the columns
            ´class´, ´score_type`, and ´value´ if long format. If to_wide, returns
            a 1 row dataframe with columns with the naming convention: "metric-aggregation_level_or_class
        """
        level_prefix = "id" if aggregate_by_id else None

        if aggregate_by_id:
            prediction_df = (  # pylint: disable=self-cls-assignment
                aggregate_predictions(
                    prediction_df,
                    id_col_name,
                    prediction_col_name,
                    label_col_name,
                )
            )

        # get predicted labels
        if prediction_df[prediction_col_name].dtype != "float":
            argmax_indices = prediction_df[prediction_col_name].apply(np.argmax)
            if id2label:
                predictions = idx_to_class(argmax_indices, id2label)
            else:
                predictions = argmax_indices
        else:
            predictions = np.round(prediction_df[prediction_col_name])

        metrics = ModelPerformance.compute_metrics(
            prediction_df[label_col_name],
            predictions,
            to_wide,
            level_prefix,
        )

        # calculate roc if binary model
        # convoluted way to take first element of scores column and test how how many items it contains
        first_score = prediction_df[prediction_col_name].take([0]).values[0]
        if isinstance(first_score, float) or len(first_score) == 2:
            label2id = {v: k for k, v in id2label.items()} if id2label else None
            probs = scores_to_probs(prediction_df[prediction_col_name])
            label_int = labels_to_int(prediction_df[label_col_name], label2id)
            auc_df = ModelPerformance.calculate_roc_auc(
                label_int,
                probs,
                to_wide,
                level_prefix,
            )

            if to_wide:
                metrics = metrics.join(auc_df)
            else:
                metrics = pd.concat([metrics, auc_df]).reset_index()

        return metrics

    @staticmethod
    def calculate_roc_auc(
        labels: Union[pd.Series, list],
        predicted: Union[pd.Series, list],
        to_wide: bool,
        add_level_prefix: Optional[str] = None,
    ) -> pd.DataFrame:
        """Calculate the area under the receiver operating characteristic
        curve.

        Potentially extendable to calculate other metrics that require probabilities
        instead of label predictions

        Args:
            labels (Union[pd.Series, list]): True labels as 0 or 1
            predicted (Union[pd.Series, list]): Predictions as values between 0 and 1
            to_wide (bool): Whether to return roc_auc as wide format.
            add_level_prefix (Optional[str]): Whether to add a prefix to the metric names.
                Can be used to indicate aggregation level.

        Returns:
            pd.DataFrame: DataFrame in metric format
        """
        roc_auc = roc_auc_score(labels, predicted)

        if to_wide:
            performance = {"auc-overall": roc_auc}
            if add_level_prefix:
                performance = {
                    add_level_prefix + "-" + k: v for k, v in performance.items()
                }
            performance = pd.DataFrame([performance])
        else:
            performance = pd.DataFrame(
                [
                    {
                        "level": add_level_prefix,
                        "class": "overall",
                        "score_type": "auc",
                        "value": roc_auc,
                    },
                ],
            )
        return performance

    @staticmethod
    def compute_metrics(
        labels: Union[pd.Series, list],
        predicted: Union[pd.Series, list[Union[str, int]]],
        to_wide: bool,
        add_level_prefix: Optional[str] = None,
    ) -> pd.DataFrame:
        """Compute a whole bunch of performance metrics for both binary and
        multiclass tasks.

        Args:
            labels (Union[pd.Series, list]): True class
            predicted (Union[pd.Series, list]): Predicted class
            to_wide (bool): Whether to return performance as wide or long format
            add_level_prefix (Optional[str]): Whether to add a prefix to the metric names.
                Can be used to indicate aggregation level.

        Returns:
            pd.DataFrame: Dataframe with performance metrics
        """
        # sorting to get correct output from f1, prec, and recall
        groups = sorted(set(labels))
        performance = {}

        performance["acc-overall"] = accuracy_score(labels, predicted)
        performance["f1_macro-overall"] = f1_score(labels, predicted, average="macro")
        performance["f1_micro-overall"] = f1_score(labels, predicted, average="micro")
        performance["precision_macro-overall"] = precision_score(
            labels,
            predicted,
            average="macro",
        )
        performance["precision_micro-overall"] = precision_score(
            labels,
            predicted,
            average="micro",
        )
        performance["recall_macro-overall"] = recall_score(
            labels,
            predicted,
            average="macro",
        )
        performance["recall_micro-overall"] = recall_score(
            labels,
            predicted,
            average="micro",
        )
        performance["confusion_matrix-overall"] = confusion_matrix(labels, predicted)

        # calculate scores by class
        f1_by_class = f1_score(labels, predicted, average=None)
        precision_by_class = precision_score(labels, predicted, average=None)
        recall_by_class = recall_score(labels, predicted, average=None)

        for i, group in enumerate(groups):  # pylint: disable=invalid-name
            performance[f"f1-{group}"] = f1_by_class[i]
            performance[f"precision-{group}"] = precision_by_class[i]
            performance[f"recall-{group}"] = recall_by_class[i]

        if add_level_prefix:
            performance = {
                add_level_prefix + "-" + k: v for k, v in performance.items()
            }
        # to df
        performance = pd.DataFrame.from_records([performance])
        if to_wide:
            return performance
        # convert to long format
        performance = pd.melt(performance)
        # split score and class into two columns
        if add_level_prefix:
            performance[["level", "score_type", "class"]] = performance[
                "variable"
            ].str.split("-", 2, expand=True)
            # drop unused columns and re-arrange
            return performance[["level", "class", "score_type", "value"]]
        else:
            performance[["score_type", "class"]] = performance["variable"].str.split(
                "-",
                1,
                expand=True,
            )
            return performance[["class", "score_type", "value"]]


if __name__ == "__main__":
    multiclass_df = pd.DataFrame(
        {
            "id": [1, 1, 2, 2, 3, 3, 4, 4],
            "scores": [
                # id 1
                [0.8, 0.1, 0.05, 0.05],
                [0.4, 0.7, 0.1, 0.1],
                # id 2
                [0.1, 0.05, 0.8, 0.05],
                [0.1, 0.7, 0.1, 0.1],
                # id 3
                [0.1, 0.1, 0.7, 0.1],
                [0.2, 0.5, 0.2, 0.1],
                # id 4
                [0.1, 0.1, 0.2, 0.6],
                [0.1, 0.2, 0.1, 0.6],
            ],
            "label": ["ASD", "ASD", "DEPR", "DEPR", "TD", "TD", "SCHZ", "SCHZ"],
            "model_name": ["test"] * 8,
        },
    )

    id2label = {0: "ASD", 1: "DEPR", 2: "TD", 3: "SCHZ"}

    multiclass_res = ModelPerformance.performance_metrics_from_df(
        multiclass_df,
        label_col_name="label",
        prediction_col_name="scores",
        id_col_name="id",
        id2label=id2label,
        metadata_col_names="all",
        to_wide=False,
    )

    binary_df = pd.DataFrame(
        {
            "id": [1, 1, 2, 2],
            "scores": [[0.8, 0.2], [0.5, 0.5], [0.4, 0.6], [0.9, 0.1]],
            "label": ["TD", "TD", "DEPR", "DEPR"],
            "optional_grouping1": ["grouping1"] * 4,
            "optional_grouping2": ["grouping2"] * 4,
        },
    )

    binary_res = ModelPerformance.performance_metrics_from_df(
        binary_df,
        label_col_name="label",
        prediction_col_name="scores",
        id_col_name="id",
        id2label=id2label,
        metadata_col_names=None,
        to_wide=True,
    )


__all__ = [
    "ModelPerformance",
    "binary_df",
    "binary_res",
    "id2label",
    "multiclass_df",
    "multiclass_res",
]
