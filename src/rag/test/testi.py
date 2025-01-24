#!/usr/bin/env python3

import argparse
import json
import os
import re

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd


def parse_score(score_str):
    """
    Convert avg_score (e.g. '88.8') or worst_score (e.g. '40')
    from string to float. Returns None if conversion fails.
    """
    try:
        return float(score_str)
    except (ValueError, TypeError):
        return None


def parse_acceptable_score(acceptable_score_str):
    """
    Convert acceptable_score (e.g. '80.00%') to float.
    For '80.00%', returns 80.0.
    Returns None if conversion fails.
    """
    if not acceptable_score_str:
        return None
    # Remove trailing '%'
    match = re.match(r"(\d+(\.\d+)?)\%$", acceptable_score_str.strip())
    if match:
        return float(match.group(1))
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate data visualizations from a JSON file."
    )
    parser.add_argument(
        "json_file",
        type=str,
        help="Path to the JSON file containing the data."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="visualizations",
        help="Directory where plots will be saved (default: 'visualizations')."
    )

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Load data from JSON
    with open(args.json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Convert data into a structured list
    processed_data = []
    for item in data:
        difficulty = item.get("difficulty", "")
        model = item.get("model", "")
        question = item.get("question", "")
        answer = item.get("answer", "")

        avg_score_str = item.get("avg_score", None)
        acceptable_score_str = item.get("acceptable_score", None)
        worst_score_str = item.get("worst_score", None)  # if present

        avg_score = parse_score(avg_score_str)
        worst_score = parse_score(worst_score_str)
        acceptable_score = parse_acceptable_score(acceptable_score_str)

        processed_data.append({
            "question": question,
            "answer": answer,
            "difficulty": difficulty,
            "avg_score": avg_score,
            "acceptable_score": acceptable_score,
            "worst_score": worst_score,
            "model": model
        })

    # Convert list of dicts into a pandas DataFrame
    df = pd.DataFrame(processed_data)

    # Drop rows where avg_score is None, as they won't help in easiest/hardest
    df = df.dropna(subset=["avg_score"])

    # 1. Plot: Distribution of Difficulties
    plt.figure(figsize=(6, 4))
    difficulty_order = ["easy", "medium", "hard"]
    # Only include those difficulties actually present
    actual_diffs = [d for d in difficulty_order if d in df["difficulty"].unique()]
    sns.countplot(data=df, x="difficulty", order=actual_diffs)
    plt.title("Distribution of Difficulties")
    plt.xlabel("Difficulty")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "difficulty_distribution.png"))
    plt.close()

    # 2. Plot: Average Score by Model
    plt.figure(figsize=(8, 5))
    model_order = df["model"].value_counts().index
    sns.barplot(data=df, x="model", y="avg_score", order=model_order, estimator=np.mean, ci=None)
    plt.title("Average Score by Model")
    plt.xlabel("Model")
    plt.ylabel("Average Score")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "avg_score_by_model.png"))
    plt.close()

    # 3. Plot: Box Plot of Scores by Model
    plt.figure(figsize=(8, 5))
    sns.boxplot(data=df, x="model", y="avg_score", order=model_order)
    plt.title("Score Distribution by Model")
    plt.xlabel("Model")
    plt.ylabel("Average Score")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "boxplot_scores_by_model.png"))
    plt.close()

    # 4. Plot: Easiest & Hardest Questions (Overall)
    sorted_df = df.sort_values(by="avg_score", ascending=True)
    # Hardest: bottom 5
    hardest_5 = sorted_df.head(5)
    # Easiest: top 5
    easiest_5 = sorted_df.tail(5)

    # Hardest
    plt.figure(figsize=(10, 5))
    sns.barplot(data=hardest_5, x="question", y="avg_score", color="red")
    plt.title("Hardest Questions (Lowest Avg Score)")
    plt.xlabel("Question")
    plt.ylabel("Average Score")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "hardest_questions.png"))
    plt.close()

    # Easiest
    plt.figure(figsize=(10, 5))
    sns.barplot(data=easiest_5, x="question", y="avg_score", color="green")
    plt.title("Easiest Questions (Highest Avg Score)")
    plt.xlabel("Question")
    plt.ylabel("Average Score")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "easiest_questions.png"))
    plt.close()

    # 5. Plot: Average Score vs Acceptable Score (if acceptable_score is present)
    compare_df = df.dropna(subset=["acceptable_score"])
    if not compare_df.empty:
        plt.figure(figsize=(7, 5))
        sns.scatterplot(
            data=compare_df,
            x="avg_score",
            y="acceptable_score",
            hue="model",
            alpha=0.7
        )
        plt.title("Average Score vs. Acceptable Score")
        plt.xlabel("Average Score")
        plt.ylabel("Acceptable Score (%)")
        plt.tight_layout()
        plt.savefig(os.path.join(args.output_dir, "avg_vs_acceptable.png"))
        plt.close()

    # 6. Plot: Worst Score by Model (if present)
    if "worst_score" in df.columns and df["worst_score"].notna().any():
        plt.figure(figsize=(8, 5))
        sns.boxplot(data=df, x="model", y="worst_score", order=model_order)
        plt.title("Worst Score Distribution by Model")
        plt.xlabel("Model")
        plt.ylabel("Worst Score")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(args.output_dir, "worst_score_by_model.png"))
        plt.close()

    # 7. Plot: Acceptable Score by Model (if present)
    if not compare_df.empty:
        plt.figure(figsize=(8, 5))
        sns.barplot(
            data=compare_df,
            x="model",
            y="acceptable_score",
            order=model_order,
            estimator=np.mean,
            ci=None
        )
        plt.title("Acceptable Score by Model")
        plt.xlabel("Model")
        plt.ylabel("Acceptable Score (%)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(args.output_dir, "acceptable_score_by_model.png"))
        plt.close()

    # 8. Print Easiest & Hardest Questions by Model to console
    print("\n==== Easiest & Hardest Questions by Model ====")
    grouped = df.groupby("model")
    for model_name, group_df in grouped:
        if group_df.empty:
            continue
        # Hardest question for this model
        hardest_idx = group_df["avg_score"].idxmin()
        # Easiest question for this model
        easiest_idx = group_df["avg_score"].idxmax()

        hardest_row = group_df.loc[hardest_idx]
        easiest_row = group_df.loc[easiest_idx]

        print(f"\nModel: {model_name}")
        print(f"  Hardest question (lowest avg_score):")
        print(f"    Question: {hardest_row['question']}")
        print(f"    Score: {hardest_row['avg_score']}")
        print(f"  Easiest question (highest avg_score):")
        print(f"    Question: {easiest_row['question']}")
        print(f"    Score: {easiest_row['avg_score']}")

    # 9. Create Score-by-Difficulty Plots for Each Model
    print("\n==== Creating Score-by-Difficulty Plots for Each Model ====")
    for model_name, group_df in grouped:
        # If the group is empty, skip
        if group_df.empty:
            continue

        # Group by difficulty and compute the mean of avg_score, acceptable_score
        summary_df = (
            group_df.groupby("difficulty")[["avg_score", "acceptable_score"]]
            .mean(numeric_only=True)
            .reset_index()
        )

        # If both columns are missing or all NaN, skip
        if summary_df[["avg_score", "acceptable_score"]].isna().all().all():
            continue

        # Melt the summary for easy plotting
        melted = summary_df.melt(
            id_vars=["difficulty"],
            value_vars=["avg_score", "acceptable_score"],
            var_name="score_type",
            value_name="score_value",
        )

        # Keep only the difficulties that appear
        diffs_present = summary_df["difficulty"].dropna().unique().tolist()
        # Intersect with standard ordering
        diffs_plot_order = [d for d in ["easy", "medium", "hard"] if d in diffs_present]

        # Create a bar plot
        plt.figure(figsize=(8, 5))
        sns.barplot(
            data=melted,
            x="difficulty",
            y="score_value",
            hue="score_type",
            order=diffs_plot_order,
            ci=None
        )
        plt.title(f"{model_name} - Avg & Acceptable Scores by Difficulty")
        plt.xlabel("Difficulty")
        plt.ylabel("Score Value")
        plt.legend(title="Score Type", loc="best")
        plt.tight_layout()

        # Make a safe filename for each model
        safe_model_name = "".join(c if c.isalnum() or c in ("-", "_", ".") else "_"
                                  for c in model_name)
        out_filename = f"score_by_difficulty_{safe_model_name}.png"
        plt.savefig(os.path.join(args.output_dir, out_filename))
        plt.close()

        print(f"  Created score-by-difficulty plot for model: {model_name}")

    # 10. Compute and print the overall hardest question(s) and the largest-variance question(s)
    #     across *all models*.
    print("\n==== Overall Hardest Question(s) and Largest Variance Question(s) ====")

    # Group by question to find mean and standard deviation of avg_score across all models
    question_stats = df.groupby("question")["avg_score"].agg(["mean", "std"]).reset_index()

    # 10a. Hardest question(s): those with the lowest mean avg_score
    min_mean = question_stats["mean"].min()
    hardest_questions = question_stats[question_stats["mean"] == min_mean]

    if not hardest_questions.empty:
        print(f"\nOverall Hardest Question(s) (lowest mean avg_score = {min_mean:.2f}):")
        for _, row in hardest_questions.iterrows():
            q_text = row["question"]
            mean_score = row["mean"]
            std_score = row["std"]
            print(f"  - '{q_text}' (mean avg_score={mean_score:.2f}, std={std_score:.2f})")

    # 10b. Largest variance question(s): those with the highest std
    max_std = question_stats["std"].max()
    largest_var_questions = question_stats[question_stats["std"] == max_std]

    if not largest_var_questions.empty and not np.isnan(max_std):
        print(f"\nQuestion(s) with Largest Variance (highest std = {max_std:.2f}):")
        for _, row in largest_var_questions.iterrows():
            q_text = row["question"]
            mean_score = row["mean"]
            std_score = row["std"]
            print(f"  - '{q_text}' (mean avg_score={mean_score:.2f}, std={std_score:.2f})")

    # Done
    print(f"\nAll plots have been saved to '{args.output_dir}'.\n")


if __name__ == "__main__":
    main()
