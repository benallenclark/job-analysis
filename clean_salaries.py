# clean_salaries.py

import sqlite3
import re
from datetime import datetime

DB_PATH = "preview_jobs.db"
LOG_PATH = "salary_clean_log.txt"


def parse_salary_string(sal_str):
    """
    Given a raw salary text, return a tuple:
      (salary_min, salary_max, salary_avg, salary_period)

    salary_period is "yearly" if the text mentions "year",
                     "hourly"   if it mentions "hour",
                     or None if it’s "n/a" or couldn’t parse.

    salary_min/max/avg are in USD per year:
      - if the original is hourly, we multiply by 2080 (40 h/week * 52 weeks)
      - if it’s a range (e.g. "$60k - $80k a year"), we parse both ends
      - if it’s "From $40 an hour", we treat $40 /hour as min, and leave max=None
      - if it’s a single number (rare), we set min= max= that value
      - if sal_str is "n/a" or blank, return (None, None, None, None)
    """
    if not sal_str or sal_str.strip() == "" or sal_str.strip().lower() == "n/a":
        return (None, None, None, None)

    text = sal_str.strip().lower()

    # Decide whether we're dealing with yearly vs hourly
    period = None
    if "year" in text:
        period = "yearly"
    elif "hour" in text:
        period = "hourly"

    # Case A: a true range (e.g. "$60k - $80k a year" or "$54,007.07 - $70,209.18 a year")
    if "-" in text:
        parts = text.split("-")
        lo_part = parts[0]
        hi_part = parts[1]

        lo_num_match = re.search(r"\$?([\d,]+(?:\.\d+)?)", lo_part)
        hi_num_match = re.search(r"\$?([\d,]+(?:\.\d+)?)", hi_part)

        if lo_num_match and hi_num_match:
            lo_raw = lo_num_match.group(1)
            hi_raw = hi_num_match.group(1)

            lo = float(lo_raw.replace(",", ""))
            hi = float(hi_raw.replace(",", ""))

            if lo_part.strip().endswith("k") or "k" in lo_part:
                lo *= 1000
            if hi_part.strip().endswith("k") or "k" in hi_part:
                hi *= 1000

            if period == "hourly":
                lo *= 2080
                hi *= 2080

            avg = (lo + hi) / 2
            return (lo, hi, avg, period)

    # Case B: a “From $40 an hour” or “From $40k a year”
    if text.startswith("from"):
        match = re.search(r"from\s*\$?([\d,]+(?:\.\d+)?)k?", text)
        if match:
            raw_num = match.group(1)
            val = float(raw_num.replace(",", ""))
            if raw_num.lower().endswith("k"):
                val *= 1000
            if period == "hourly":
                val *= 2080
            return (val, None, val, period)

    # Case C: a single number (e.g. "$40k a year", though rare)
    single_match = re.search(r"\$?([\d,]+(?:\.\d+)?)k?", text)
    if single_match:
        raw_num = single_match.group(1)
        val = float(raw_num.replace(",", ""))
        if raw_num.lower().endswith("k"):
            val *= 1000
        if period == "hourly":
            val *= 2080
        return (val, val, val, period)

    return (None, None, None, None)


def main():
    # Open log file with UTF-8 encoding
    with open(LOG_PATH, "w", encoding="utf-8") as log:
        log.write(f"--- Salary Cleaning Log: {datetime.now()} ---\n\n")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1) Add four new columns if they don’t already exist; log each attempt.
    columns = ["salary_min REAL", "salary_max REAL", "salary_avg REAL", "salary_period TEXT"]
    for col_def in columns:
        col_name = col_def.split()[0]
        try:
            cur.execute(f"ALTER TABLE jobs ADD COLUMN {col_def};")
            conn.commit()
            with open(LOG_PATH, "a", encoding="utf-8") as log:
                log.write(f"Added column '{col_name}'.\n")
        except sqlite3.OperationalError:
            with open(LOG_PATH, "a", encoding="utf-8") as log:
                log.write(f"Column '{col_name}' already exists; skipping.\n")

    # 2) Replace empty or NULL salary with "n/a"; log each affected row.
    rows_to_fix = cur.execute("""
        SELECT job_id, salary
          FROM jobs
         WHERE salary IS NULL OR TRIM(salary) = ''
    """).fetchall()

    for job_id, old_salary in rows_to_fix:
        with open(LOG_PATH, "a", encoding="utf-8") as log:
            log.write(f"job_id={job_id}: salary '{old_salary}' → 'n/a'\n")

    cur.execute("""
        UPDATE jobs
           SET salary = 'n/a'
         WHERE salary IS NULL OR TRIM(salary) = ''
    """)
    conn.commit()

    # 3) Parse and populate new columns for every row; log before/after for each.
    all_rows = cur.execute("SELECT job_id, salary FROM jobs;").fetchall()

    for job_id, raw_salary in all_rows:
        # Compute parsed values
        lo, hi, avg, period = parse_salary_string(raw_salary)

        # Fetch old values (should be NULL on first run)
        old_vals = cur.execute("""
            SELECT salary_min, salary_max, salary_avg, salary_period
              FROM jobs
             WHERE job_id = ?
        """, (job_id,)).fetchone()

        old_min, old_max, old_avg, old_period = old_vals

        # Update new columns
        cur.execute("""
            UPDATE jobs
               SET salary_min = ?,
                   salary_max = ?,
                   salary_avg = ?,
                   salary_period = ?
             WHERE job_id = ?
        """, (lo, hi, avg, period, job_id))

        # Log before vs after
        with open(LOG_PATH, "a", encoding="utf-8") as log:
            log.write(
                f"job_id={job_id}: raw_salary='{raw_salary}' | "
                f"salary_min: {old_min} → {lo}, "
                f"salary_max: {old_max} → {hi}, "
                f"salary_avg: {old_avg} → {avg}, "
                f"salary_period: {old_period} → {period}\n"
            )

    conn.commit()
    conn.close()

    with open(LOG_PATH, "a", encoding="utf-8") as log:
        log.write("\n--- Cleaning complete ---\n")


if __name__ == "__main__":
    main()
