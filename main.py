
"""Run the Customer Recommendation Engine."""

from recommender import (
    DATA_PATH,
    OUTPUT_PATH,
    RecommendationEngine,
    read_purchases,
)


def print_similarity_matrix(engine):
    # Print the similarity matrix for the first five customers.
    customers = sorted(engine.customer_products)[:5]

    print("\n=== Similarity matrix (first five customers) ===")
    print("       " + " ".join(f"{customer:>6}" for customer in customers))

    for customer_a in customers:
        scores = [
            f"{engine.similarity(customer_a, customer_b):6.2f}"
            for customer_b in customers
        ]
        print(f"{customer_a:>6} " + " ".join(scores))


def print_customer_recommendations(engine, customer_id):
    # Print one customer's history, neighbours and recommendations.
    history = sorted(engine.history(customer_id))
    customer_name = engine.customer_names[customer_id]

    print(f"\nCustomer {customer_id} ({customer_name}) bought: {history}")

    neighbours = engine.similar_customers(customer_id)

    print("Most similar customers:")
    if neighbours:
        for neighbour_id, similarity in neighbours:
            print(f"  {neighbour_id}  jaccard={similarity:.2f}")
    else:
        print("  No qualifying neighbours.")

    print("Recommendations:")
    recommendations = engine.recommend(customer_id)

    if not recommendations:
        print("  No recommendations available.")
        return

    for row in recommendations:
        support_count = len(row["supporting_customers"])

        if support_count:
            reason = f"{support_count} similar customers bought it"
        else:
            reason = "popular-product fallback; no neighbour support"

        print(
            f"  {row['rank']}. {row['product_name']} "
            f"({row['category']})  "
            f"score={row['score']:.3f}  because {reason}"
        )


def main():
    valid_purchases, rejected_purchases = read_purchases(DATA_PATH)

    engine = RecommendationEngine(valid_purchases)

    print_similarity_matrix(engine)

    # Print examples for two customers.
    for customer_id in ["C105", "C101"]:
        if customer_id in engine.customer_products:
            print_customer_recommendations(engine, customer_id)

    all_recommendations = engine.recommend_all(n=3)
    engine.export_csv(all_recommendations, OUTPUT_PATH)

    print("\n=== Run summary ===")
    print(
        f"Purchases read: {len(valid_purchases) + len(rejected_purchases)}"
        f" | used: {len(valid_purchases)}"
        f" | rejected: {len(rejected_purchases)}"
    )
    print(
        f"Customers: {len(engine.customer_products)}"
        f" | Products: {len(engine.product_names)}"
        f" | Recommendations written: {len(all_recommendations)}"
    )
    print(f"CSV saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
