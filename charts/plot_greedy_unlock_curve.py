def compute_greedy_unlock_data(job_skill_map, user_skills=None, max_skills=30, progress_callback=None):
    total_jobs = len(job_skill_map)
    skill_to_jobs = {}
    for job_id, skills in job_skill_map.items():
        for skill in skills:
            skill_to_jobs.setdefault(skill.lower(), set()).add(job_id)

    uncovered_jobs = set(job_skill_map.keys())
    coverage_progress = []

    normalized_user_skills = set(s.lower() for s in user_skills or [])
    for skill in normalized_user_skills:
        uncovered_jobs -= skill_to_jobs.get(skill, set())

    initial_coverage = (total_jobs - len(uncovered_jobs)) / total_jobs * 100
    coverage_progress.append(initial_coverage)

    greedy_skills = []
    while uncovered_jobs and len(greedy_skills) < max_skills:
        best_skill = None
        best_coverage = 0
        for skill, jobs in skill_to_jobs.items():
            if skill in normalized_user_skills or skill in greedy_skills:
                continue  # 👈 skip already known or picked skills

            new_coverage = len(uncovered_jobs & jobs)
            if new_coverage > best_coverage:
                best_coverage = new_coverage
                best_skill = skill

        if not best_skill:
            break

        greedy_skills.append(best_skill)
        uncovered_jobs -= skill_to_jobs[best_skill]
        coverage = (total_jobs - len(uncovered_jobs)) / total_jobs * 100
        coverage_progress.append(coverage)

        if progress_callback:
            percent = len(greedy_skills) / max_skills * 100
            progress_callback(percent)

    return coverage_progress, greedy_skills



def plot_greedy_unlock_curve(coverage_progress, selected_skills):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(range(len(coverage_progress)), coverage_progress, marker="o")
    ax.set_title("Greedy Unlock Curve (Top 30 Skills)")
    ax.set_xlabel("Number of Skills Learned")
    ax.set_ylabel("Job Coverage (%)")
    ax.grid(True, linestyle="--", alpha=0.6)

    # Add skill labels in a text box on the right
    top_skills = selected_skills[:min(20, len(selected_skills))]
    skill_text = "\n".join([f"{i+1}. {skill}" for i, skill in enumerate(top_skills)])

    # Use the figure itself to add a text box
    fig.text(0.75, 0.5, f"Top Skills:\n{skill_text}", fontsize=10,
             verticalalignment='center', horizontalalignment='left',
             bbox=dict(boxstyle="round", facecolor="whitesmoke", edgecolor="gray"))

    fig.tight_layout(rect=[0, 0, 0.7, 1])  # shrink chart to make room for skill list
    return fig
