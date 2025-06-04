from collections import defaultdict
import matplotlib.pyplot as plt

def plot_skill_coverage_comparison(job_skill_map, user_skills: list[str]):
    user_skills = set(skill.lower() for skill in user_skills)

    # Build reverse mapping: skill -> set of jobs
    skill_to_jobs = defaultdict(set)
    for job_id, skills in job_skill_map.items():
        for skill in skills:
            skill_to_jobs[skill.lower()].add(job_id)

    # Determine fully matched jobs with current user skills
    fully_matched_jobs = set()
    for job_id, skills in job_skill_map.items():
        if set(skill.lower() for skill in skills).issubset(user_skills):
            fully_matched_jobs.add(job_id)

    # Now simulate adding one skill at a time to see how many *new* jobs it unlocks
    remaining_skills = set(skill_to_jobs.keys()) - user_skills
    seen_jobs = fully_matched_jobs.copy()
    unlock_recommendations = []

    for skill in remaining_skills:
        unlocked_jobs = set()
        test_skills = user_skills | {skill}
        for job_id, skills in job_skill_map.items():
            skill_set = set(skill.lower() for skill in skills)
            if skill_set.issubset(test_skills) and job_id not in seen_jobs:
                unlocked_jobs.add(job_id)
        if unlocked_jobs:
            unlock_recommendations.append((skill, len(unlocked_jobs)))
    
    # Sort by most jobs newly unlocked
    unlock_recommendations.sort(key=lambda x: x[1], reverse=True)
    top_unlocks = unlock_recommendations[:10]

    # Prepare chart: 2 lines – current vs optimal unlock
    total_jobs = len(job_skill_map)
    current_skills = user_skills.copy()
    current_coverage = [len(fully_matched_jobs) / total_jobs * 100]
    added_skills = []

    for skill, _ in top_unlocks:
        added_skills.append(skill)
        current_skills.add(skill)
        matched = 0
        for job_id, skills in job_skill_map.items():
            if set(skill.lower() for skill in skills).issubset(current_skills):
                matched += 1
        current_coverage.append(matched / total_jobs * 100)

    # X-axis: 0 skills, 1 skill, ..., N skills
    x_vals = list(range(len(current_coverage)))
    x_labels = ["0"] + [str(i+1) for i in range(len(top_unlocks))]

    # Plot chart
    plt.figure(figsize=(10, 6))
    plt.plot(x_vals, current_coverage, marker='o', label='Cumulative Coverage if You Add Recommended Skills')
    plt.title('Skill-Based Job Unlock Progression')
    plt.xlabel('Number of Recommended Skills Added')
    plt.ylabel('Job Coverage (%)')
    plt.xticks(x_vals, x_labels)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(loc='lower right')

    # Display recommended skills
    recommendation_text = "Top 10 Skills That Unlock the Most Jobs:\n" + "\n".join(
        [f"{i+1}. {skill.title()} ({count} jobs)" for i, (skill, count) in enumerate(top_unlocks)]
    )

    plt.gcf().text(
        1.02, 0.5, recommendation_text,
        fontsize=10, va="center", ha="left",
        bbox=dict(facecolor='white', edgecolor='gray', boxstyle='round,pad=0.5'),
        transform=plt.gca().transAxes,
    )

    plt.tight_layout()
    plt.subplots_adjust(right=0.85)  
    plt.show()

