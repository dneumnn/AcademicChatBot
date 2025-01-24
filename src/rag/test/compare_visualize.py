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
    Convert avg_score (e.g. '88.8') or worst_score (e.g. '40') from string to float.
    Returns None if conversion fails.
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
    match = re.match(r"(\d+(\.\d+)?)\%$", acceptable_score_str.strip())
    if match:
        return float(match.group(1))
    return None

def load_and_prepare_data(json_file):
    """
    Loads JSON data from `json_file`, parses numeric fields,
    and returns a DataFrame with columns:
      question, model, difficulty, avg_score, acceptable_score, worst_score, ...
    """
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    processed = []
    for item in data:
        difficulty    = item.get("difficulty", "")
        model         = item.get("model", "")
        question      = item.get("question", "")
        answer        = item.get("answer", "")

        avg_score_str        = item.get("avg_score", None)
        acceptable_score_str = item.get("acceptable_score", None)
        worst_score_str      = item.get("worst_score", None)

        avg_score        = parse_score(avg_score_str)
        worst_score      = parse_score(worst_score_str)
        acceptable_score = parse_acceptable_score(acceptable_score_str)

        processed.append({
            "question": question,
            "model": model,
            "difficulty": difficulty,
            "avg_score": avg_score,
            "acceptable_score": acceptable_score,
            "worst_score": worst_score,
            "answer": answer
        })

    df = pd.DataFrame(processed)
    return df

def main():
    parser = argparse.ArgumentParser(
        description="Compare data from two JSON files, generate comparison plots and summary."
    )
    parser.add_argument(
        "file1",
        type=str,
        help="Path to the first JSON file."
    )
    parser.add_argument(
        "file2",
        type=str,
        help="Path to the second JSON file."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="comparison_visuals",
        help="Directory to save output plots (default: 'comparison_visuals')."
    )

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # 1. Load and prepare the data from both files
    df1 = load_and_prepare_data(args.file1)
    df2 = load_and_prepare_data(args.file2)

    # OPTIONAL: Drop rows where avg_score is None (if you want to compare only those that have scores)
    # df1 = df1.dropna(subset=["avg_score"])
    # df2 = df2.dropna(subset=["avg_score"])

    # 2. Merge the two DataFrames on a common key
    #    Common key could be ("question", "model") if each question-model pair is unique
    merge_key = ["question", "model"]

    # Renaming columns to differentiate between file1 and file2
    rename_dict_1 = {col: col+"_1" for col in ["difficulty", "avg_score", "acceptable_score", "worst_score", "answer"]}
    rename_dict_2 = {col: col+"_2" for col in ["difficulty", "avg_score", "acceptable_score", "worst_score", "answer"]}

    df1_renamed = df1.rename(columns=rename_dict_1)
    df2_renamed = df2.rename(columns=rename_dict_2)

    # Merging (inner join: only rows present in both data sets)
    merged_df = pd.merge(
        df1_renamed, df2_renamed,
        on=["question","model"],  # the key columns
        how="inner"              # 'inner' keeps only matching rows
    )

    # 3. Compute differences in important columns
    #    e.g. difference in avg_score, acceptable_score, worst_score
    merged_df["avg_score_diff"]        = merged_df["avg_score_2"] - merged_df["avg_score_1"]
    merged_df["acceptable_score_diff"] = merged_df["acceptable_score_2"] - merged_df["acceptable_score_1"]
    merged_df["worst_score_diff"]      = merged_df["worst_score_2"] - merged_df["worst_score_1"]

    # 4. Some basic summary stats
    print("=== Comparison Summary ===")
    print(f"Number of matching question-model pairs: {len(merged_df)}\n")

    # Average difference in avg_score
    mean_diff_avg = merged_df["avg_score_diff"].mean()
    print(f"Mean difference in avg_score (file2 - file1): {mean_diff_avg:.2f}")

    # 5. Generate plots
    #    Example 1: Distribution of average score differences
    plt.figure(figsize=(8,5))
    sns.histplot(data=merged_df, x="avg_score_diff", kde=True)
    plt.title("Distribution of avg_score Differences (No Rerank - Norm)")
    plt.xlabel("Difference in avg_score")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "avg_score_diff_distribution.png"))
    plt.close()

    #    Example 2: Boxplot of avg_score differences by difficulty_1 (or difficulty_2)
    #    Caution: difficulty_1 and difficulty_2 might differ if the same question
    #    is labeled differently in each file. For simplicity, let's use difficulty_1.
    #    If you want a more robust approach, you may have to unify difficulty definitions.
    if "difficulty_1" in merged_df.columns:
        plt.figure(figsize=(8,5))
        sns.boxplot(data=merged_df, x="difficulty_1", y="avg_score_diff")
        plt.title("avg_score Differences by Difficulty (No Rerank - Norm)")
        plt.xlabel("Difficulty (from File1)")
        plt.ylabel("avg_score Difference")
        plt.tight_layout()
        plt.savefig(os.path.join(args.output_dir, "avg_score_diff_by_difficulty.png"))
        plt.close()

    #    Example 3: Average score in File1 vs File2 (scatter plot)
    plt.figure(figsize=(6,6))
    sns.scatterplot(data=merged_df, x="avg_score_1", y="avg_score_2", hue="model", alpha=0.7)
    plt.plot([0,100],[0,100], ls="--", c="red")  # reference line
    plt.title("avg_score in Norm vs. No Rerank")
    plt.xlabel("avg_score (File1)")
    plt.ylabel("avg_score (File2)")
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "avg_score_scatter_file1_vs_file2.png"))
    plt.close()

    #    Example 4: Compare acceptable_score by model
    #    We'll compute the mean acceptable_score_1 and _2 per model and do a side-by-side bar plot
    comp_acceptable = merged_df.groupby("model")[["acceptable_score_1", "acceptable_score_2"]].mean().reset_index()
    # Melt for easier plotting
    comp_acceptable_melted = comp_acceptable.melt(id_vars="model",
                                                  value_vars=["acceptable_score_1","acceptable_score_2"],
                                                  var_name="File",
                                                  value_name="MeanAcceptableScore")
    # Convert "acceptable_score_1" to "File1", "acceptable_score_2" to "File2" for clarity
    comp_acceptable_melted["File"] = comp_acceptable_melted["File"].replace({
        "acceptable_score_1": "Norm",
        "acceptable_score_2": "No Rerank"
    })

    plt.figure(figsize=(8,5))
    sns.barplot(data=comp_acceptable_melted, x="model", y="MeanAcceptableScore", hue="File")
    plt.title("Mean Acceptable Score by Model (Comparison)")
    plt.xlabel("Model")
    plt.ylabel("Acceptable Score (%)")
    plt.xticks(rotation=45)
    plt.legend(title="Source File")
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "acceptable_score_by_model_comparison.png"))
    plt.close()

    # 6. Identify which questions changed the most in avg_score
    #    Let's print top 5 that increased the most and top 5 that decreased the most.
    sorted_by_diff = merged_df.sort_values(by="avg_score_diff", ascending=True)
    print("\n=== Questions with Largest Negative Difference (File2 - File1) ===")
    print("(i.e., these are significantly lower in File2 compared to File1)\n")
    print(sorted_by_diff.head(5)[["question","model","avg_score_1","avg_score_2","avg_score_diff"]].to_string(index=False))

    print("\n=== Questions with Largest Positive Difference (File2 - File1) ===")
    print("(i.e., these are significantly higher in File2 compared to File1)\n")
    print(sorted_by_diff.tail(5)[["question","model","avg_score_1","avg_score_2","avg_score_diff"]].to_string(index=False))

    print("\n=== Finished generating comparison plots and summary. ===")
    print(f"Plots have been saved to: {args.output_dir}")

if __name__ == "__main__":
    main()
