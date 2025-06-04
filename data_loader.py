import sqlite3
from collections import defaultdict, Counter

def load_skills(db_path='preview_jobs.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM skills")
    skills_data = cursor.fetchall()
    conn.close()
    return [s[0].strip().lower() for s in skills_data if s[0]]


def load_job_skill_map(db_path='preview_jobs.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT job_id, name FROM skills WHERE required=1")
    skills_data = cursor.fetchall()

    cursor.execute("SELECT job_id, title, company FROM jobs")
    jobs_data = cursor.fetchall()
    conn.close()

    # Group required skills per job
    job_skill_map = defaultdict(set)
    for job_id, skill in skills_data:
        job_skill_map[job_id].add(skill.strip().lower())

    # Lookup for job_id → title, company
    job_info_map = {job_id: (title, company) for job_id, title, company in jobs_data}

    return job_skill_map, job_info_map

def load_unique_skills():
    job_skill_map, _ = load_job_skill_map()
    
    skill_counts = Counter()
    for required_skills in job_skill_map.values():
        for skill in required_skills:
            skill_counts[skill.lower()] += 1
    
    total_jobs = len(job_skill_map)
    return sorted(
        [(skill, count / total_jobs) for skill, count in skill_counts.items()],
        key=lambda x: x[1],
        reverse=True
    )
