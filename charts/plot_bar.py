from collections import Counter
import matplotlib.pyplot as plt

def plot_top_skills_bar(job_skill_map, selected_skills, top_n=50):
    selected_skills = set(s.lower() for s in selected_skills)
    skill_counts = Counter()

    for required_skills in job_skill_map.values():
        for skill in required_skills:
            skill_lower = skill.lower()
            if skill_lower not in selected_skills:
                skill_counts[skill_lower] += 1

    if not skill_counts:
        print("No remaining skills to recommend.")
        return

    top_skills = skill_counts.most_common(top_n)
    skills, counts = zip(*top_skills)

    plt.figure(figsize=(12, 8))
    plt.barh(skills[::-1], counts[::-1])
    plt.xlabel('Job Coverage (Excludes Your Skills)')
    plt.title(f'Top {top_n} Skills You May Be Missing')
    plt.tight_layout()
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.show()
