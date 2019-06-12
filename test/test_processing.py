from unittest import TestCase

import numpy as np
import pandas as pd
from sklearn.datasets import load_boston

from lib.processing import InspectDf


def generate_data() -> pd.DataFrame:
    """
    return a data set for this unit test.

    :return: data set
    """

    bunch = load_boston()
    df = pd.DataFrame(bunch.data, columns=[c.replace(" ", "_") for c in bunch.feature_names])
    df["target"] = bunch.target
    df["PTRATIO"] = df["PTRATIO"].apply(str)
    df["TAX"] = np.arange(df.shape[0])

    ## masking
    np.random.seed(2)
    col_chosen = ["B", "NOX", "RM", "CRIM"]
    na_rates = [0.25, 0.50, 0.75, 1.0]
    ncol = df.shape[0]

    for col, na_rate in zip(col_chosen, na_rates):
        mask = np.random.binomial(1, p=na_rate, size=ncol).astype(np.float)
        mask[mask == 1] = np.nan
        df[col] = df[col] * mask

    return df


class ProcessingTest(TestCase):
    def test_an_inspection(self):
        """
        check the inspection
        """
        np.random.seed(1)
        df = generate_data()
        df_inspection = InspectDf(df, m_cats=20)

        ## variable type detection
        self.assertEqual(df_inspection.inspection.loc["CHAS", "variable"], "binary")
        self.assertEqual(df_inspection.inspection.loc["NOX", "variable"], "constant")
        self.assertEqual(df_inspection.inspection.loc["TAX","distinct"], True)
        self.assertEqual(df_inspection.inspection["distinct"].sum(),1)

        ## column of objects is always categorical
        self.assertEqual(df_inspection.inspection.loc["PTRATIO", "variable"], "categorical")

        ## nan must be ignored
        self.assertEqual(len(df["NOX"].unique()), 2)
        self.assertEqual(df_inspection.inspection.loc["NOX","n_unique"], 1)

        ## change the threshold between categorical and continuous
        self.assertEqual(df_inspection.inspection.loc["ZN", "variable"], "continuous")
        df_inspection.m_cats = 30 ## ZN must become categorical
        self.assertEqual(df_inspection.inspection.loc["ZN", "variable"], "categorical")

        ## get a non-missing value
        self.assertTrue(pd.isna(df_inspection.inspection.loc["CRIM","sample_value"]))
        self.assertFalse(pd.isna(df_inspection.inspection.loc["RM","sample_value"]))


    # def test_distribution(self):
    #     """
    #     check DataFrames for distributions
    #     """
    #
    #     df = pd.read_csv(test_data)
    #     nrow = df.shape[0]
    #     df_inspection = InspectDf(df, m_cats=20)
    #
    #     df_cat = df_inspection.distribution_cats()
    #
    #     ## Missing values are also counted
    #     self.assertEqual(
    #         df_cat.loc["workclass"].loc[np.nan, "count"],
    #         1836
    #     )
    #
    #     self.assertAlmostEqual(
    #         df_cat.loc["workclass"].loc["Private", "count"] / nrow,
    #         df_cat.loc["workclass"].loc["Private", "rate"]
    #     )
    #
    #     df_con = df_inspection.distribution_cons()
    #
    #     ## Since it is just a transpose of describe(),
    #     ## the number of columns is equal to 8
    #     self.assertEqual(
    #         df_con.shape,
    #         (len(df_inspection.get_cons()), 8)
    #     )
    #
    #
    # def test_significance(self):
    #     """
    #     Check significance tests
    #     """
    #
    #     df = pd.read_csv(test_data)
    #     df_inspection = InspectDf(df, m_cats=20)
    #
    #     s = df_inspection.significance_test("fnlwgt","age")
    #
    #     self.assertTrue(
    #         isinstance(s, pd.Series)
    #     )
    #
    #     ## field1, field2, test, statistic, p-value
    #     self.assertEqual(
    #         len(s),
    #         5
    #     )
    #
    #     ## Default correlation
    #     self.assertEqual(
    #         s["test"],
    #         "Spearman correlation"
    #     )
    #
    #     df_pval = df_inspection.significance_test_features("label")
    #
    #     self.assertEqual(
    #         df_pval.shape[1],
    #         5
    #     )
    #
    #     df_pval.set_index("field1", inplace=True)
    #
    #     self.assertEqual(
    #         df_pval.loc["age", "test"],
    #         "one-way ANOVA on ranks"
    #     )
    #
    #     self.assertEqual(
    #         df_pval.loc["education-num", "test"],
    #         "chi-square test"
    #     )
