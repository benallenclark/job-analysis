from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from itertools import islice

# Simulated job_skill_map for testing (normally you'd load this from your actual data)
job_skill_map = {
    f"job{i}": set(np.random.choice(['python', 'sql', 'excel', 'tableau', 'r', 'power bi', 'communication', 'leadership',
                                     'problem solving', 'project management', 'vba', 'java', 'c++', 'hadoop', 'spark'], 
                                    size=np.random.randint(2, 6), replace=False))
    for i in range(1, 101)
}




# ------------------------------------------
# Heatmap Matrix Implementation
# ------------------------------------------
def plot_skill_job_heatmap(job_skill_map, top_n_skills=20, sample_n_jobs=50):
    all_skills = defaultdict(int)
    for skills in job_skill_map.values():
        for skill in skills:
            all_skills[skill.lower()] += 1
    top_skills = [s for s, _ in sorted(all_skills.items(), key=lambda x: x[1], reverse=True)[:top_n_skills]]
    sampled_jobs = dict(islice(job_skill_map.items(), sample_n_jobs))

    matrix = np.zeros((len(sampled_jobs), len(top_skills)))
    job_ids = list(sampled_jobs.keys())
    for i, job_id in enumerate(job_ids):
        skills = set(sk.lower() for sk in sampled_jobs[job_id])
        for j, skill in enumerate(top_skills):
            matrix[i][j] = 1 if skill in skills else 0

    df = pd.DataFrame(matrix, index=job_ids, columns=top_skills)

    plt.figure(figsize=(12, 8))
    sns.heatmap(df, cmap="Blues", cbar=False, linewidths=0.5, linecolor='gray')
    plt.title("Skill-Job Requirement Heatmap (Top Skills × Sample Jobs)")
    plt.xlabel("Skills")
    plt.ylabel("Jobs")
    plt.tight_layout()
    plt.show()
    
# plot_skill_job_heatmap(job_skill_map)