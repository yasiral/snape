import unittest
import pandas as pd

from snape.make_dataset import *
import glob
import os


class TestMakeDataset(unittest.TestCase):
    def test_create_classification_dataset(self):
        df = create_classification_dataset(n_samples=100, n_features=10, n_informative=3, n_redundant=0,
                                           n_repeated=0, n_clusters_per_class=2, weights=[0.5, 0.5], n_classes=2)
        self.assertEqual(df.shape[0], 100, "Sample Size Doesn't Match")
        self.assertEqual(df.shape[1], 11, "Feature Count")
        self.assertEqual(df['y'].value_counts().shape[0], 2, "Expected Shape of Classes Do Not Match")

    def test_create_regression_dataset(self):
        df = create_regression_dataset(n_samples=100, n_features=10, n_informative=3, effective_rank=1,
                                       tail_strength=0.5, noise=0.0)

        self.assertEqual(df.shape[0], 100, "Sample Size Doesn't Match")
        self.assertEqual(df.shape[1], 11, "Feature Count")

    def test_create_categorical_features(self):
        df = pd.DataFrame(np.random.randn(100, 4), columns=list('ABCD'))
        cat_df = create_categorical_features(df, 2, [['a', 'b'], ['red', 'blue']])
        self.assertEqual(cat_df.dtypes.value_counts()['category'], 2)  # there should be 2 category variables

    def test_insert_special_char(self):
        df = pd.DataFrame(np.random.randn(100, 1), columns=list('A'))
        df_spec = insert_special_char("$", df)
        self.assertTrue(df_spec['A'].str.contains('$').all())
        df_spec = insert_special_char("%", df)
        self.assertTrue(df_spec['A'].str.contains('$').all())

    def test_insert_missing_values(self):
        df = pd.DataFrame(np.random.randn(100, 4), columns=list('ABCD'))
        df_result = insert_missing_values(df, 1)
        self.assertTrue(df_result.isnull().any().any())
        df_result = insert_missing_values(df, 0)
        self.assertFalse(df_result.isnull().any().any())

    def test_star_schema(self):
        df = create_classification_dataset(n_samples=100, n_features=10, n_informative=3, n_redundant=0,
                                           n_repeated=0, n_clusters_per_class=2, weights=[0.5, 0.5], n_classes=2)
        df = create_categorical_features(df, 2, [['a', 'b'], ['red', 'blue']])
        df = insert_special_char('$', df)
        df = insert_special_char('%', df)
        df = insert_missing_values(df, .8)
        fact_df = make_star_schema(df)
        # Assert file generation
        file_list = glob.glob('./*_dim.csv')
        diff_list = list(filter(lambda x: x.endswith('_dim.csv'), file_list))
        self.assertEqual(len(diff_list), 2)
        # Delete the tester files
        for file_path in file_list:
            os.remove(file_path)
        # Assert key column creation
        columns = fact_df.columns
        key_cols = list(filter(lambda x: x.endswith('_key'), columns))
        self.assertEqual(len(key_cols), 3)
        # Assert key columns don't contain any nulls
        key_df = fact_df[key_cols]
        na_df = key_df.dropna()
        self.assertEqual(len(na_df), len(key_df), msg="Nulls exist in the dimension key columns in the star schema.")
        # Assert that an index named 'primary_key' was added.
        self.assertTrue('primary_key' in fact_df.columns, msg="Index named pk was not added to the fact table")
        self.assertEqual(len(fact_df.primary_key.value_counts()),len(fact_df), msg="Primary key isn't unique.")


if __name__ == '__main__':
    unittest.main()
