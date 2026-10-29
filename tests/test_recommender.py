
import csv
import tempfile
import unittest
from pathlib import Path

from recommender import (
    RecommendationEngine,
    jaccard,
    read_purchases,
)


class TestRecommendationEngine(unittest.TestCase):

    def setUp(self):
        self.purchases = [
            {
                "customer_id": "C101",
                "customer_name": "Amina",
                "product_id": "P01",
                "product_name": "Milk",
                "category": "Dairy",
            },
            {
                "customer_id": "C101",
                "customer_name": "Amina",
                "product_id": "P02",
                "product_name": "Bread",
                "category": "Bakery",
            },
            {
                "customer_id": "C102",
                "customer_name": "Brian",
                "product_id": "P01",
                "product_name": "Milk",
                "category": "Dairy",
            },
            {
                "customer_id": "C102",
                "customer_name": "Brian",
                "product_id": "P03",
                "product_name": "Eggs",
                "category": "Fresh",
            },
            {
                "customer_id": "C103",
                "customer_name": "Carol",
                "product_id": "P03",
                "product_name": "Eggs",
                "category": "Fresh",
            },
        ]

        self.engine = RecommendationEngine(self.purchases)

    def test_jaccard_similarity(self):
        self.assertAlmostEqual(
            jaccard({"P01", "P02"}, {"P02", "P03"}),
            1 / 3,
        )

    def test_jaccard_empty_sets(self):
        self.assertEqual(jaccard(set(), set()), 1.0)

    def test_customer_history(self):
        self.assertEqual(
            self.engine.history("C101"),
            {"P01", "P02"},
        )

    def test_unknown_customer_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.engine.history("C999")

    def test_similar_customers_excludes_self(self):
        neighbours = self.engine.similar_customers("C101", k=2)

        self.assertEqual(neighbours[0][0], "C102")
        self.assertNotIn(
            "C101",
            [customer_id for customer_id, score in neighbours],
        )

    def test_recommendations_exclude_owned_products(self):
        recommendations = self.engine.recommend("C101", n=3)
        owned_products = self.engine.history("C101")

        for recommendation in recommendations:
            self.assertNotIn(
                recommendation["product_id"],
                owned_products,
            )

    def test_recommend_all_includes_every_customer(self):
        rows = self.engine.recommend_all(n=3)

        expected_customers = set(self.engine.customer_products)
        actual_customers = {row["customer_id"] for row in rows}

        self.assertEqual(actual_customers, expected_customers)

    def test_export_csv_has_required_columns(self):
        rows = self.engine.recommend_all(n=3)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "recommendations.csv"
            self.engine.export_csv(rows, output_path)

            with open(
                output_path,
                "r",
                encoding="utf-8",
                newline="",
            ) as file:
                reader = csv.DictReader(file)
                expected_columns = [
                    "customer_id",
                    "customer_name",
                    "rank",
                    "product_id",
                    "product_name",
                    "category",
                    "score",
                    "supporting_customers",
                ]

                self.assertEqual(reader.fieldnames, expected_columns)
                self.assertGreater(len(list(reader)), 0)


class TestPurchaseCleaning(unittest.TestCase):

    def test_purchase_data_cleaning(self):
        valid, rejected = read_purchases()

        self.assertEqual(len(valid), 60)
        self.assertEqual(len(rejected), 3)


if __name__ == "__main__":
    unittest.main()
