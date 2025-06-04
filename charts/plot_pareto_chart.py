def plot_pareto_chart(all_skills, top_n=50):
    import matplotlib.pyplot as plt
    import pandas as pd

    skill_counts = pd.Series(all_skills).value_counts().nlargest(top_n)
    cumulative = skill_counts.cumsum()
    total = cumulative.iloc[-1]
    cumulative_percent = cumulative / total

    fig, ax1 = plt.subplots(figsize=(14, 6))

    ax1.bar(skill_counts.index, skill_counts.values, color='skyblue')
    ax1.set_ylabel("Frequency")
    ax1.set_xlabel("Skill")
    ax1.tick_params(axis='x', rotation=45)

    ax2 = ax1.twinx()
    ax2.plot(skill_counts.index, cumulative_percent.values, color='red', marker='o', linewidth=2)
    ax2.set_ylabel("Cumulative %")
    ax2.set_ylim(0, 1.05)
    ax2.axhline(y=0.5, color='gray', linestyle='--')
    ax2.axhline(y=0.8, color='gray', linestyle='--')

    plt.title("Pareto Chart of Skills by Frequency and Cumulative Impact")
    fig.tight_layout()
    plt.grid(True, axis='y', linestyle='--', alpha=0.4)
    plt.show()
