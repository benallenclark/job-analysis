import pandas as pd
import matplotlib.pyplot as plt

def plot_cumulative_line(all_skills, top_n=50):
    skill_counts = pd.Series(all_skills).value_counts().nlargest(top_n)[::1]
    cumulative = skill_counts.cumsum()
    total = skill_counts.sum()

    thresholds = {
        "50%": cumulative[cumulative >= 0.50 * total].index[0],
        "65%": cumulative[cumulative >= 0.65 * total].index[0],
        "80%": cumulative[cumulative >= 0.80 * total].index[0]
    }
    threshold_positions = {k: skill_counts.index.get_loc(v) for k, v in thresholds.items()}

    plt.figure(figsize=(14, 6))
    plt.plot(range(len(skill_counts)), skill_counts.values, marker='o', linestyle='-')
    plt.vlines(range(len(skill_counts)), 0, skill_counts.values, linestyles='dashed', colors='lightgrey', linewidth=1)

    for label, x in threshold_positions.items():
        plt.axvline(x=x, color={'50%': 'red', '65%': 'orange', '80%': 'green'}[label],
                    linestyle='--', linewidth=2)
        plt.text(x, max(skill_counts.values)*0.95, label, ha='center', va='top', fontweight='bold')

    plt.xticks(range(len(skill_counts)), labels=skill_counts.index, rotation=45, ha='right')
    plt.gca().spines['bottom'].set_position(('data', 0))
    plt.xticks(rotation=45, ha='right')  # ha='right' aligns label start at tick
    plt.xlabel('Skill')
    plt.ylabel('Frequency')
    plt.title('Cumulative Skill Impact (Top 50)')
    plt.tight_layout()
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.show()




# # Plotting: Line chart
# # Count frequency and sort from lowest to highest
# # skill_counts = pd.Series(all_skills).value_counts().nlargest(50)
# # Reverse the index and values to make the highest frequency start on the right
# # skill_counts = skill_counts[::1]
# plt.figure(figsize=(14, 6))
# plt.plot(skill_counts.index, skill_counts.values, marker='o', linestyle='-')
# # Add vertical dashed lines from x-axis to each point
# plt.vlines(
#     x=range(len(skill_counts)),             # positions (same as tick indices)
#     ymin=0,                                 # start from y=0
#     ymax=skill_counts.values,               # end at the skill frequency
#     linestyles='dashed',
#     colors='lightgrey',
#     linewidth=1
# )


# plt.gca().spines['bottom'].set_position(('data', 0))


# plt.xlabel('Skill')
# plt.ylabel('Frequency')
# plt.title('Most Frequent Skills (Top 50)')
# plt.tight_layout()
# plt.grid(True, axis='y', linestyle='--', alpha=0.7)
# plt.show()