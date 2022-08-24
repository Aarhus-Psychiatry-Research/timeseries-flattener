import numpy as np

from psycopmlutils.timeseriesflattener import create_feature_combinations


def generate_blood_sample_feature_combinations(
    LOOKBEHIND_DAYS=[365, 730, 1825, 9999],
    RESOLVE_MULTIPLE=["mean", "max", "min"],
):
    create_feature_combinations(
        [
            {
                "predictor_df": "hba1c",
                "lookbehind_days": LOOKBEHIND_DAYS,
                "resolve_multiple": ["mean", "max", "min", "count"],
                "fallback": np.nan,
            },
            {
                "predictor_df": "alat",
                "lookbehind_days": LOOKBEHIND_DAYS,
                "resolve_multiple": RESOLVE_MULTIPLE,
                "fallback": np.nan,
            },
            {
                "predictor_df": "hdl",
                "lookbehind_days": LOOKBEHIND_DAYS,
                "resolve_multiple": RESOLVE_MULTIPLE,
                "fallback": np.nan,
            },
            {
                "predictor_df": "ldl",
                "lookbehind_days": LOOKBEHIND_DAYS,
                "resolve_multiple": RESOLVE_MULTIPLE,
                "fallback": np.nan,
            },
            {
                "predictor_df": "shceduled_glc",
                "lookbehind_days": LOOKBEHIND_DAYS,
                "resolve_multiple": RESOLVE_MULTIPLE,
                "fallback": np.nan,
            },
            {
                "predictor_df": "unshceduled_p_glc",
                "lookbehind_days": LOOKBEHIND_DAYS,
                "resolve_multiple": RESOLVE_MULTIPLE,
                "fallback": np.nan,
            },
            {
                "predictor_df": "triglycerides",
                "lookbehind_days": LOOKBEHIND_DAYS,
                "resolve_multiple": RESOLVE_MULTIPLE,
                "fallback": np.nan,
            },
            {
                "predictor_df": "hdl",
                "lookbehind_days": LOOKBEHIND_DAYS,
                "resolve_multiple": RESOLVE_MULTIPLE,
                "fallback": np.nan,
            },
            {
                "predictor_df": "ldl",
                "lookbehind_days": LOOKBEHIND_DAYS,
                "resolve_multiple": RESOLVE_MULTIPLE,
                "fallback": np.nan,
            },
            {
                "predictor_df": "fasting_ldl",
                "lookbehind_days": LOOKBEHIND_DAYS,
                "resolve_multiple": RESOLVE_MULTIPLE,
                "fallback": np.nan,
            },
            {
                "predictor_df": "alat",
                "lookbehind_days": LOOKBEHIND_DAYS,
                "resolve_multiple": RESOLVE_MULTIPLE,
                "fallback": np.nan,
            },
            {
                "predictor_df": "crp",
                "lookbehind_days": LOOKBEHIND_DAYS,
                "resolve_multiple": RESOLVE_MULTIPLE,
                "fallback": np.nan,
            },
            {
                "predictor_df": "egfr",
                "lookbehind_days": LOOKBEHIND_DAYS,
                "resolve_multiple": RESOLVE_MULTIPLE,
                "fallback": np.nan,
            },
            {
                "predictor_df": "albumine_creatinnine_ratio",
                "lookbehind_days": LOOKBEHIND_DAYS,
                "resolve_multiple": RESOLVE_MULTIPLE,
                "fallback": np.nan,
            },
        ],
    )
