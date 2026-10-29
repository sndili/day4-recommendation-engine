"""
Day 4 - Customer Recommendation Engine
Squad Python Specialization - Data Science, AI & Analytics

Core Python only for the engine (csv, collections, math are fine). No ML libraries.
"""
from __future__ import annotations

import csv
from pathlib import Path

DATA_PATH = Path("data") / "purchases.csv"
OUTPUT_PATH = Path("output") / "recommendations.csv"


def read_purchases(path: Path = DATA_PATH) -> tuple[list[dict], list[dict]]:
    """Return (valid_rows, rejected_rows). Decide what makes a purchase row unusable."""
    valid_rows = []
    rejected_rows = []
    seen_rows = set()

    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        required_columns = {
            "purchase_id",
            "customer_id",
            "customer_name",
            "product_id",
            "product_name",
            "category",
            "purchase_date",
            "quantity",
        }

        if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
            raise ValueError("The purchases CSV is missing required columns.")

        for row_number, row in enumerate(reader, start=2):
            # Standardize text fields and IDs.
            for column in row:
                if row[column] is not None:
                    row[column] = row[column].strip()

            row["customer_id"] = row["customer_id"].upper()
            row["product_id"] = row["product_id"].upper()

            reason = None

            if not row["customer_id"] or not row["product_id"]:
                reason = "Missing customer ID or product ID"
            elif not row["customer_name"]:
                reason = "Missing customer name"
            elif not row["product_name"] or not row["category"]:
                reason = "Missing product name or category"
            elif not row["purchase_id"]:
                reason = "Missing purchase ID"
            elif not row["purchase_date"]:
                reason = "Missing purchase date"
            else:
                try:
                    quantity = int(row["quantity"])
                    if quantity <= 0:
                        reason = "Quantity must be greater than zero"
                    else:
                        row["quantity"] = quantity
                except (ValueError, TypeError):
                    reason = "Invalid quantity"

            if reason is None:
                # Ignore exact duplicate purchase records.
                duplicate_key = tuple(
                    row[column]
                    for column in reader.fieldnames
                )

                if duplicate_key in seen_rows:
                    reason = "Duplicate purchase row"
                else:
                    seen_rows.add(duplicate_key)

            if reason is not None:
                rejected_rows.append({
                    "row_number": row_number,
                    "row": row,
                    "reason": reason,
                })
            else:
                valid_rows.append(row)

    return valid_rows, rejected_rows


def jaccard(a: set, b: set) -> float:
    """|A intersection B| / |A union B|. Define (and test) what happens when both are empty."""
    union = a | b

    if not union:
        return 1.0

    intersection = a & b
    return len(intersection) / len(union)


class RecommendationEngine:
    """Recommends products a customer has not bought, based on similar customers."""

    def __init__(self, purchases: list[dict], min_similarity: float = 0.0) -> None:
        if not 0.0 <= min_similarity <= 1.0:
            raise ValueError("min_similarity must be between 0 and 1.")

        self.min_similarity = min_similarity

        # Store each customer's distinct purchased products.
        self.customer_products = {}
        self.customer_names = {}

        # Store each product's name and category.
        self.product_names = {}
        self.product_categories = {}

        # Track the customers who bought each product.
        product_customers = {}

        for row in purchases:
            customer_id = row["customer_id"]
            product_id = row["product_id"]

            self.customer_products.setdefault(customer_id, set())
            self.customer_products[customer_id].add(product_id)

            self.customer_names[customer_id] = row["customer_name"]
            self.product_names[product_id] = row["product_name"]
            self.product_categories[product_id] = row["category"]

            product_customers.setdefault(product_id, set())
            product_customers[product_id].add(customer_id)

        # Popularity is the number of distinct customers who bought a product.
        self.product_popularity = {
            product_id: len(customers)
            for product_id, customers in product_customers.items()
        }

    def history(self, customer_id: str) -> set[str]:
        """Return the distinct products bought by a customer."""
        if customer_id not in self.customer_products:
            raise KeyError(f"Unknown customer ID: {customer_id}")

        return self.customer_products[customer_id].copy()

    def similarity(self, customer_a: str, customer_b: str) -> float:
        """Calculate Jaccard similarity between two customers."""
        history_a = self.history(customer_a)
        history_b = self.history(customer_b)

        return jaccard(history_a, history_b)

    def similar_customers(self, customer_id: str, k: int = 3) -> list[tuple[str, float]]:
        """Return the k most similar other customers as (customer_id, score), best first."""
        if customer_id not in self.customer_products:
            raise KeyError(f"Unknown customer ID: {customer_id}")

        if k <= 0:
            return []

        similarities = []

        for other_id in self.customer_products:
            # A customer must not be their own neighbour.
            if other_id == customer_id:
                continue

            score = self.similarity(customer_id, other_id)

            # Ignore customers below the minimum similarity.
            if score >= self.min_similarity:
                similarities.append((other_id, score))

        # Sort by similarity descending, then customer ID ascending.
        similarities.sort(key=lambda item: (-item[1], item[0]))

        return similarities[:k]

    def candidate_products(self, customer_id: str, k: int = 3) -> dict[str, dict]:
        """Products bought by similar customers but not by this one, with the evidence for each."""
        customer_history = self.history(customer_id)
        neighbours = self.similar_customers(customer_id, k)
        candidates = {}

        for neighbour_id, similarity_score in neighbours:
            for product_id in self.history(neighbour_id):
                if product_id in customer_history:
                    continue

                if product_id not in candidates:
                    candidates[product_id] = {
                        "supporting_customers": [],
                        "similarity_total": 0.0,
                    }

                candidates[product_id]["supporting_customers"].append(
                    neighbour_id
                )
                candidates[product_id]["similarity_total"] += similarity_score

        # Use popular products if no neighbours qualify (Fallback).
        if not candidates:
            for product_id in self.product_names:
                if product_id not in customer_history:
                    candidates[product_id] = {
                        "supporting_customers": [],
                        "similarity_total": 0.0,
                    }

        return candidates

    def score(self, evidence: dict) -> float:
        """Your ranking rule. Combine similarity with at least one other signal."""
        popularity = self.product_popularity.get(
            evidence.get("product_id", ""), 0
        )
        return evidence["similarity_total"] + 0.1 * popularity

    def recommend(self, customer_id: str, n: int = 3) -> list[dict]:
        """Return up to n ranked recommendations for one customer."""
        customer_history = self.history(customer_id)

        if n <= 0:
            return []

        candidates = self.candidate_products(customer_id)
        recommendations = []

        for product_id, evidence in candidates.items():
            recommendation_evidence = {
                **evidence,
                "product_id": product_id,
            }
            score = self.score(recommendation_evidence)

            recommendations.append({
                "customer_id": customer_id,
                "customer_name": self.customer_names[customer_id],
                "product_id": product_id,
                "product_name": self.product_names[product_id],
                "category": self.product_categories[product_id],
                "score": score,
                "supporting_customers": evidence["supporting_customers"],
            })

        recommendations.sort(
            key=lambda row: (-row["score"], row["product_id"])
        )

        for rank, row in enumerate(recommendations[:n], start=1):
            row["rank"] = rank

        return recommendations[:n]

    def recommend_all(self, n: int = 3) -> list[dict]:
        all_recommendations = []

        for customer_id in sorted(self.customer_products):
            recommendations = self.recommend(customer_id, n)

            if recommendations:
                all_recommendations.extend(recommendations)
            else:
                # Keep the customers with no available recommendations.
                all_recommendations.append({
                    "customer_id": customer_id,
                    "customer_name": self.customer_names[customer_id],
                    "rank": "",
                    "product_id": "",
                    "product_name": "",
                    "category": "",
                    "score": "",
                    "supporting_customers": [],
                })

        return all_recommendations

    def export_csv(self, rows: list[dict], path: Path = OUTPUT_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        columns = [
            "customer_id",
            "customer_name",
            "rank",
            "product_id",
            "product_name",
            "category",
            "score",
            "supporting_customers",
        ]

        with open(path, "w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()

            for row in rows:
                csv_row = row.copy()

                # Format scores to three decimal places.
                if csv_row.get("score") != "":
                    csv_row["score"] = f"{csv_row['score']:.3f}"

                # Store supporting customer IDs - separated by semicolon.
                csv_row["supporting_customers"] = ";".join(
                    csv_row.get("supporting_customers", [])
                )

                writer.writerow(csv_row)


if __name__ == "__main__":
    # TODO: build the engine, print recommendations for two customers, export all
    pass
