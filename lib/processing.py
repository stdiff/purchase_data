"""

"""

from typing import Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats

from pylab import rcParams

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

class Inspector:

    def __init__(self, df:pd.DataFrame, m_cats:int=20):
        """
        Construct an inspection DataFrame of the given one
        Note that missing values are ignored for n_unique

        :param df: DataFrame to analyze
        :param m_cats: maximum number of values of a categorical variable
        """
        self.data = df ## Do not take a copy. A reference is better.
        self._m_cats = m_cats
        self.inspection = None
        self.make_an_inspection()


    def make_an_inspection(self):
        self.inspection = pd.DataFrame(self.data.dtypes, columns=["dtype"])
        self.inspection["count_na"] = self.data.isna().sum()
        self.inspection["rate_na"] = self.data.isna().mean()
        self.inspection["n_unique"] = self.data.apply(lambda x: len(x.dropna(how="any").unique()), axis=0)
        self.inspection["distinct"] = self.inspection["n_unique"] == self.data.shape[0]
        self.m_cats = self._m_cats
        self.inspection["sample_value"] = self.data.apply(self.sample_value, axis=0)
        return self


    @property
    def m_cats(self):
        return self._m_cats

    @m_cats.setter
    def m_cats(self, m_cats:int=20):
        """
        The threshold of the categorical and continuous variables for numerical variable.
        (A variable of "object" is always categorical.)

        Detect the type of fields.

        binary: takes only two values. (This is also categorical.)
        categorical: is a object type or takes less than or equal to m_cats values
        continuous: takes more than m_cats values

        Remark:
        - We ignore NA to count the number of possible values of a field.
        - A categorical variable can be nominal (not ordered) or ordered.

        :param m_cats: maximum number of values of a categorical variable
        :return: self
        """
        self._m_cats = m_cats

        def get_vtype(s: pd.Series) -> str:
            if s["n_unique"] <= 1:
                return "constant"
            elif s["n_unique"] == 2:
                return "binary"
            elif s["dtype"] == "object" or s["n_unique"] <= self._m_cats:
                return "categorical"
            else:
                return "continuous"

        self.inspection["variable"] = self.inspection.apply(get_vtype, axis=1)


    def sample_value(self, s:pd.Series, seed:int=None) -> Any:
        """
        return a non-missing value of the column in a random way.
        If the column has only missing values, then it will be returned.

        :return: a value
        """
        if seed is not None:
            np.random.seed(seed)

        s = s.dropna(how="any").unique()

        if len(s):
            return np.random.choice(s,1)[0]
        else:
            return np.nan


    def set_variable_type(self, field:str, variable:str):
        """
        Change the type of variable manually.

        :param field: field name
        :param variable: "continuous", "binary" or "categorical"
        """
        valid_types = ["constant", "continuous", "binary", "categorical"]
        if variable in valid_types:
            self.inspection.loc[field,"variable"] = variable
        else:
            print("variable must be one of the following: %s" % ", ".join(['"%s"' % x for x in valid_types]))


    def __repr__(self):
        return self.inspection.__repr__()


    def _repr_html_(self):
        return self.inspection._repr_html_()


    def get_cats(self) -> list:
        """
        :return: the list of categorical variables (including binary variables)
        """

        df_cats = self.inspection[self.inspection.variable.apply(lambda x: x in ["binary", "categorical"])]
        return list(df_cats.index)


    def get_cons(self) -> list:
        """
        :return: the list of continuous variables
        """
        df_cats = self.inspection[self.inspection.variable == "continuous"]
        return list(df_cats.index)

    def get_fields_with_na(self) -> list:
        """
        :return: the list of fields containing missing values
        """

        return list(self.inspection[self.inspection["count_na"] > 0].index)


    ## information about distribution in DataFrame
    def distribution_cats(self, fields:list=None):
        """
        return a DataFrame showing the distribution of the categorical variables.

        :param fields: list of (categorical) fields to check
        :return: DataFrame of distributions
        """

        if fields is None:
            fields = self.get_cats()

        df_dist = []

        for field in fields:
            s = self.data[field]

            df_tmp = s.value_counts(dropna=False).sort_index().reset_index()
            df_tmp.columns = ["value", "count"]
            df_tmp["field"] = field
            df_tmp.set_index(["field","value"], inplace=True)
            df_tmp["rate"] = df_tmp["count"]/len(s)

            df_dist.append(df_tmp)

        return pd.concat(df_dist, axis=0)


    def distribution_cons(self,fields:list=None):
        """
        return a DataFrame showing the distribution of the continuous variables.
        This is basically the same as df.describe().T

        :param fields: list of continuous fields to check
        :return: DataFrame of distributions
        """

        if fields is None:
            fields = self.get_cons()

        return self.data[fields].describe().T

    ## Check if two variables are significantly different
    def significance_test(self, field1:str, field2:str, method:str="spearman") -> pd.Series:
        """
        Execute a statistical test as follows
        - Both fields are categorical => chi-square test
        - Both fields are continuous => correlation
        - Otherwise => one-way ANOVA on ranks

        :param field1: field to compare
        :param field2: field to compare
        :param method: "spearman" (default) or "pearson"
        :return: Series with index: field1, field2, test, statistic, pval
        """

        cats = self.get_cats()
        cons = self.get_cons()

        if field1 in cats and field2 in cats:
            #### chi2-test
            test = "chi-square test"
            contigency_table = pd.crosstab(self.data[field1], self.data[field2])

            if (contigency_table < 5).sum().sum() > 0:
                print("The contigency table (%s vs %s) contains too small cell(s)." % (field1,field2))
                #print("Consult the documentation of stats.chi2_contingency")

            statistic, pval, dof, exp = stats.chi2_contingency(contigency_table)

        elif field1 in cons and field2 in cons:
            #### correlation
            if method == "spearman":
                test = "Spearman correlation"
                cor = stats.spearmanr
            else:
                test = "Peason correlation"
                cor = stats.pearsonr

            statistic, pval = cor(self.data[field1], self.data[field2])

        else:
            #### one-way ANOVA on ranks
            test = "one-way ANOVA on ranks"
            if field1 in cats and field2 in cons:
                cat, con = field1, field2
            elif field1 in cons and field2 in cats:
                cat, con = field2, field1
            else:
                raise ValueError("You gave a wrong field.")

            vals = self.data[cat].unique()

            samples = [self.data.loc[self.data[cat] == v, con] for v in vals]

            if any([len(s) < 5 for s in samples]):
                print("The groups withe less than 5 samples will be ignored.")
                samples = [x for x in samples if len(x) >= 5]

            statistic, pval = stats.kruskal(*samples)

        s = pd.Series([field1, field2, test, statistic, pval],
                      index=["field1", "field2", "test", "statistic", "pval"])
        return s


    def significance_test_features(self, target) -> pd.DataFrame:
        """
        Check the significance of feature variables against the target variables

        :param target: the target variable
        :return: DataFrame containing the result of tests
        """
        fields = [f for f in self.data.columns if f != target]

        results = [self.significance_test(field, target) for field in fields]
        return pd.concat(results, axis=1).T


    def visualize_two_fields(self, field1:str, field2:str,
                             proportion:bool=False,
                             rotation:float=0.0):
        """
        Draw an informative diagramm for given two fields (feature and target).
        Note that this method can accept no constant field.

        :param field1: feature variable
        :param field2: target variable
        :param proportion: proportion instead of distribution
        :param rotation: rotation of xticks
        """

        cats = self.get_cats()
        cons = self.get_cons()

        width, height = rcParams['figure.figsize']
        aspect = width / height

        if field1 in cats and field2 in cats:
            ## bar chart
            df_tmp = pd.crosstab(self.data[field1], self.data[field2])

            if proportion:
                bucket_size = df_tmp.sum(axis=1)
                for col in df_tmp.columns:
                    df_tmp[col] = df_tmp[col] / bucket_size ## normalize

                df_tmp.plot.bar(stacked=True)
                title = "Proportion of %s by %s" % (field2, field1)

            else:
                df_tmp = df_tmp / df_tmp.sum(axis=0) ## normalise
                df_tmp.plot.bar(stacked=False)
                title = "Distribution of %s by %s" % (field1, field2)

        elif field1 in cats and field2 in cons:
            ## violine
            sns.violinplot(field1, field2, data=self.data,
                           inner="quartile")
            title = "Distribution of %s by %s" % (field2, field1)

        elif field1 in cons and field2 in cats:
            ## KDE
            sns.FacetGrid(self.data, hue=field2,
                          height=height, aspect=aspect, legend_out=False)\
               .map(sns.kdeplot, field1, shade=True).add_legend()
            plt.ylabel("density")
            title = "Kernel distribution estimate of %s by %s" % (field1,field2)

        elif field1 in cons and field2 in cons:
            ## joint plot
            sns.jointplot(field1, field2, data=self.data, kind="reg",
                          height=height)
            title = ""

        else:
            raise ValueError("You gave a wrong field.")

        plt.xticks(rotation=rotation)
        plt.title(title)
        plt.show()

