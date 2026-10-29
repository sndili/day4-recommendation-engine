# Mama Mboga Online : Customer Recommendation Engine

## Overview

This project builds a simple product recommendation engine for Mama Mboga Online, a grocery delivery business in Nairobi. The engine recommends products that a customer has not purchased before by identifying customers with similar purchase histories. It uses Python sets, dictionaries, Jaccard similarity, a custom scoring rule and CSV files. The project uses core Python libraries and does not require external dependencies.

## Project Objectives

- Clean and validate purchase records using Python's `csv` module.
- Represent customer purchase histories using sets.
- Calculate customer similarity using Jaccard similarity.
- Find similar customers and identify products they have purchased.
- Rank recommendations using similarity and product popularity.
- Export recommendations for all customers to a CSV file.
- Test the main functions and expected behaviours.

## Project Structure

```text
day4-recommendation-engine/
├── data/
│   └── purchases.csv
├── output/
│   └── recommendations.csv
├── tests/
│   └── test_recommender.py
├── main.py
├── recommender.py
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.10 or later
- The provided dataset - `data/purchases.csv` 


## How to Run

Open a terminal in the project directory.

Run the recommendation engine:

```bash
python main.py
```

Run the automated tests:

```bash
python -m unittest discover -s tests -v
```

The program prints a similarity matrix, customer histories, similar customers, ranked recommendations and a run summary. It saves the recommendations to `output/recommendations.csv`.

## Data Cleaning

The `read_purchases()` function reads the purchase CSV and separates valid records from rejected records.

The cleaning process:

1. Checks that all required columns are present.
2. Removes leading and trailing whitespace from field values.
3. Converts customer and product IDs to uppercase for consistency.
4. Rejects records with missing required IDs, names, categories, purchase IDs or dates.
5. Rejects quantities that are not valid integers or are zero or negative.
6. Rejects exact duplicate purchase records after normalization.

Each rejected record includes its CSV row number, original row data after cleaning and rejection reason.

The dataset produced the following results:

| Measure | Result |
|---|---:|
| Purchase records read | 63 |
| Valid records used | 60 |
| Rejected records | 3 |
| Customers | 20 |
| Products | 15 |

## Recommendation Method

### 1. Customer purchase histories

Each customer is represented by a set of distinct product IDs. Sets make it easy to identify products two customers have in common. Repeated purchases of the same product do not increase the customer's history size because the recommendation engine focuses on whether a customer has purchased a product, rather than how many units they bought.

### 2. Jaccard similarity

Jaccard similarity measures the overlap between two customers product histories.

**Formula:**

```text
Jaccard(A, B) = |A ∩ B| / |A ∪ B|
```

- `A ∩ B` represents the products both customers purchased.
- `A ∪ B` represents all distinct products purchased by either customer.

The score ranges from 0 to 1. A score of 0 means the customers have no products in common. A score of 1 means their product sets are identical. When both sets are empty, this implementation returns 1.0 by convention.

### 3. Similar customers

The engine ranks other customers by Jaccard similarity and selects the top three by default. The customer being evaluated is excluded from their own neighbour list. Ties are resolved by customer ID to make the results deterministic.

### 4. Candidate products

The engine collects products purchased by similar customers that the target customer has not purchased. For each candidate product, it records the supporting customers and adds their similarity scores together. If no candidate products are found through neighbours, the engine falls back to products the customer has not purchased and ranks them using product popularity.

### 5. Recommendation scoring

The scoring rule combines the total similarity of supporting customers with product popularity.

```text
Score = Similarity Total + (0.1 * Product Popularity)
```

Product popularity is the number of distinct customers who purchased that product. A higher score gives a product a higher ranking. If scores are tied, product ID determines the order.

#### Prcatical Example

Consider customer `C105`, whose purchase history contains `P02` and `P15`.

Product `P10`, Pampers Size 3, has the following evidence:

- Similarity total from supporting customers: `0.65`
- Product popularity: `6` distinct customers

Therefore:

```text
Score = 0.65 + (0.1 * 6)
      = 0.65 + 0.60
      = 1.25
```

Product `P12`, Omo 2kg, receives the same score of `1.25`. Because the scores are tied, `P10` appears before `P12` based on product ID.

This rule is simple and explainable. It rewards products supported by similar customers while also accounting for overall popularity.

## Output

The engine exports `output/recommendations.csv` with these columns:

| Column | Description |
|---|---|
| `customer_id` | Customer identifier |
| `customer_name` | Customer name |
| `rank` | Recommendation rank |
| `product_id` | Recommended product identifier |
| `product_name` | Recommended product name |
| `category` | Product category |
| `score` | Recommendation score |
| `supporting_customers` | Semicolon-separated supporting customer IDs |

Every customer appears in the export. If a customer has no available recommendations, the export contains one row for that customer with blank product-related fields.

The program also prints a summary of records read, records used, rejected records, customers, products and recommendation rows written.

## Testing

The automated tests cover:

- Jaccard similarity and empty sets
- Customer purchase history
- Unknown customer handling
- Similar customer selection and self-exclusion
- Exclusion of previously purchased products
- Recommendation coverage for all customers
- CSV column names and export
- Purchase data cleaning

Run the tests with:

```bash
python -m unittest discover -s tests -v
```

All nine tests passed as highlighted below:

```text
test_purchase_data_cleaning (test_recommender.TestPurchaseCleaning.test_purchase_data_cleaning) ... ok
test_customer_history (test_recommender.TestRecommendationEngine.test_customer_history) ... ok
test_export_csv_has_required_columns (test_recommender.TestRecommendationEngine.test_export_csv_has_required_columns) ... ok
test_jaccard_empty_sets (test_recommender.TestRecommendationEngine.test_jaccard_empty_sets) ... ok
test_jaccard_similarity (test_recommender.TestRecommendationEngine.test_jaccard_similarity) ... ok
test_recommend_all_includes_every_customer (test_recommender.TestRecommendationEngine.test_recommend_all_includes_every_customer) ... ok
test_recommendations_exclude_owned_products (test_recommender.TestRecommendationEngine.test_recommendations_exclude_owned_products) ... ok
test_similar_customers_excludes_self (test_recommender.TestRecommendationEngine.test_similar_customers_excludes_self) ... ok
test_unknown_customer_raises_key_error (test_recommender.TestRecommendationEngine.test_unknown_customer_raises_key_error) ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.012s

OK
```

## Limitations

- Recommendations are based on purchase history, not customer demographics or product descriptions.
- The popularity fallback may recommend broadly popular products without neighbour support.
- The scoring weights are manually chosen and have not been evaluated against real customer outcomes.

## Conclusion

This project demonstrates how sets, dictionaries, similarity measures, ranking rules, CSV processing and automated tests can be combined to build a small product recommendation system using core Python.