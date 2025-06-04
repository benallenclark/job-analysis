import matplotlib.pyplot as plt
import pandas as pd

def plot_subplot2grid(all_skills, top_n=50):
    skill_counts = pd.Series(all_skills).value_counts().nlargest(top_n)[::-1]
    cumulative = skill_counts.cumsum()
    total = cumulative.iloc[-1]

    thresholds = {
        "50%": cumulative[cumulative >= 0.50 * total].index[0],
        "65%": cumulative[cumulative >= 0.65 * total].index[0],
        "80%": cumulative[cumulative >= 0.80 * total].index[0]
    }
    threshold_positions = {k: skill_counts.index.get_loc(v) for k, v in thresholds.items()}
    coverage_colors = {'50%': 'red', '65%': 'orange', '80%': 'green'}

    fig = plt.figure(figsize=(16, 6))
    ax1 = plt.subplot2grid((1, 2), (0, 0))
    ax2 = plt.subplot2grid((1, 2), (0, 1))

    # Left: Line chart with threshold lines
    ax1.plot(skill_counts.values, marker='o')
    for label, x in threshold_positions.items():
        ax1.axvline(x, color=coverage_colors[label], linestyle='--')
    ax1.set_title("Skill Frequencies with Threshold Markers")
    ax1.set_ylabel("Frequency")
    ax1.set_xlabel("Skill Index")
    ax1.grid(True, linestyle='--', alpha=0.5)

    # Right: Cumulative curve with threshold markers
    ax2.plot(cumulative.values / total, marker='o', color='black')
    for label, x in threshold_positions.items():
        ax2.axvline(x, color=coverage_colors[label], linestyle='--')
        ax2.text(x, 0.05, label, color=coverage_colors[label], fontweight='bold', ha='center')
    ax2.set_title("Cumulative Coverage")
    ax2.set_ylabel("Percent of Total")
    ax2.set_ylim(0, 1.05)
    ax2.set_xlabel("Skill Index")
    ax2.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.show()
