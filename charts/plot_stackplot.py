import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def plot_stackplot(all_skills, top_n=50):
    # Count frequencies (and reverse for visual clarity)
    skill_counts = pd.Series(all_skills).value_counts().nlargest(top_n)[::-1]

    # Compute cumulative sums
    cumulative = skill_counts.cumsum()
    total = cumulative.iloc[-1]

    # Get threshold indexes
    thresholds = {
        "50%": cumulative[cumulative >= 0.50 * total].index[0],
        "65%": cumulative[cumulative >= 0.65 * total].index[0],
        "80%": cumulative[cumulative >= 0.80 * total].index[0]
    }
    threshold_positions = {k: skill_counts.index.get_loc(v) for k, v in thresholds.items()}

    # Prepare data
    y_vals = skill_counts.values
    x = np.arange(len(y_vals))

    y_50 = np.where(x <= threshold_positions['50%'], y_vals, 0)
    y_65 = np.where((x > threshold_positions['50%']) & (x <= threshold_positions['65%']), y_vals, 0)
    y_80 = np.where((x > threshold_positions['65%']) & (x <= threshold_positions['80%']), y_vals, 0)
    y_rest = np.where(x > threshold_positions['80%'], y_vals, 0)

    # Plot
    plt.figure(figsize=(12, 6))
    plt.stackplot(x, y_50, y_65, y_80, y_rest, labels=["0–50%", "50–65%", "65–80%", "80–100%"],
                  colors=["red", "orange", "green", "gray"], alpha=0.7)
    plt.legend(loc="upper right")
    plt.title("Cumulative Skill Impact by Coverage Tier")
    plt.xlabel("Skill Rank")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.show()
