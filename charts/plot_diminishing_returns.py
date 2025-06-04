from collections import defaultdict
import matplotlib.pyplot as plt
from data_loader import load_job_skill_map

def plot_diminishing_returns(user_skills: list[str]):
    job_skill_map, _ = load_job_skill_map()

    # -------------------------------------------
    # Build skill-to-job mapping
    # -------------------------------------------
    skill_to_jobs = defaultdict(set)
    for job_id, skills in job_skill_map.items():
        for skill in skills:
            skill_to_jobs[skill.lower()].add(job_id)

    # -------------------------------------------
    # Filter out user skills
    # -------------------------------------------
    user_skills = set(s.lower() for s in user_skills)
    remaining_skills = {skill: jobs for skill, jobs in skill_to_jobs.items() if skill not in user_skills}

    # -------------------------------------------
    # Rank remaining skills
    # -------------------------------------------
    skill_job_coverage = sorted(
        ((skill, len(jobs)) for skill, jobs in remaining_skills.items()),
        key=lambda x: x[1], reverse=True
    )

    # -------------------------------------------
    # Track cumulative job unlocks
    # -------------------------------------------
    seen_jobs = set()
    x = []
    y = []

    for i, (skill, job_ids) in enumerate(skill_job_coverage, start=1):
        new_jobs = remaining_skills[skill] - seen_jobs
        seen_jobs.update(new_jobs)
        x.append(i)
        y.append(len(seen_jobs))

    total_jobs = len(job_skill_map)
    y_percent = [round(100 * count / total_jobs, 2) for count in y]

    # -------------------------------------------
    # Plot diminishing returns line
    # -------------------------------------------
    plt.figure(figsize=(10, 6))
    plt.plot(x, y_percent, marker='o', linestyle='-', color='blue')
    plt.title("Diminishing Returns: Skill Learning vs. Job Unlocks")
    plt.xlabel("Number of New Skills Learned")
    plt.ylabel("Cumulative Job Coverage (%)")
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # -------------------------------------------
    # Show stable milestones (50%, 60%, ..., 100%)
    # -------------------------------------------
    for milestone in [50, 60, 70, 80, 90, 95, 100]:
        for i, percent in enumerate(y_percent):
            if percent >= milestone:
                plt.axvline(x=i+1, color='green', linestyle='--', alpha=0.4,
                            label=f'{milestone}% @ {i+1} skills')
                break
            

    # -------------------------------------------
    # Recommend top 10 skills
    # -------------------------------------------
    top_next_skills = []
    seen_jobs = set()
    for skill, _ in skill_job_coverage:
        if skill in user_skills:
            continue
        new_jobs = remaining_skills[skill] - seen_jobs
        if not new_jobs:
            continue
        seen_jobs.update(new_jobs)
        top_next_skills.append((skill, len(new_jobs)))
        if len(top_next_skills) == 10:
            break
        
    # Create recommendation text
    rec_data = [f"{s.title()} ({c} jobs)" for s, c in top_next_skills]
    rec_text = "Top 10 Skill Recommendations:\n" + "\n".join([f"{i+1}. {row}" for i, row in enumerate(rec_data)])
    
    # -------------------------------------------
    # Coverage milestone summary (added here)
    # -------------------------------------------
    milestone_table = []
    for milestone in [50, 60, 70, 80, 90, 95, 100]:
        for i, percent in enumerate(y_percent):
            if percent >= milestone:
                milestone_table.append(f"{milestone}% of jobs = {i+1} skills")
                break
    milestone_text = "Coverage Milestones:\n" + "\n".join(milestone_table)
    
    # Display recommendation as text on the side of the plot
    table_data = [f"{s.title()} ({c} jobs)" for s, c in top_next_skills]
    table_text = "\n".join([f"{i+1}. {row}" for i, row in enumerate(table_data)])

    # Show Top 10 Skill Recommendations
    plt.gca().text(
        1.02, .97, rec_text,
        fontsize=10, va="top", ha="left",
        bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.5'),
        transform=plt.gca().transAxes,
        clip_on=False
    )
    
    # Show Coverage Milestones (below recommendations)
    plt.gca().text(
        1.02, 0.57, milestone_text,
        fontsize=10, va="top", ha="left",
        bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.5'),
        transform=plt.gca().transAxes,
        clip_on=False
    )





    for i in range(1, len(y_percent)):
        delta = y_percent[i] - y_percent[i - 1]
        if delta < 0.5:
            plt.axvline(x=i, color='red', linestyle='--',
                        label=f'Diminishing Return Starts @ {i} skills')
            break



    # Move legend outside, below Coverage Milestones
    plt.legend(
        loc='upper left',
        bbox_to_anchor=(1.01, 0.28),  # X=right margin, Y=lower than milestones
        borderaxespad=0,
        fontsize=9,
    )


    plt.tight_layout()
    plt.show()
