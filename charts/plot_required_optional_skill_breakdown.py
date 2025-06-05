# charts/plot_required_optional_skill_breakdown.py
import sqlite3
from typing import List

import pandas as pd
import plotly.express as px


def plot_required_optional_skill_breakdown(
    db_path: str,
    selected_skills: List[str]
):
    """
    Fetch the top 10 required and top 10 optional skills (by frequency)
    from the `skills` table, excluding any skill the user has already selected.
    Then display a grouped bar chart to show those “high‐value” skills they lack.

    Args:
        db_path (str): Path to your SQLite database (e.g., "preview_jobs.db").
        selected_skills (List[str]): A list of skill names the user already has;
            these will be filtered out of the top-10 lists.

    Example:
        # Suppose your GUI lets the user check off ["python", "aws"]
        plot_required_optional_skill_breakdown("preview_jobs.db", ["python", "aws"])
    """
    # 1) Connect to the SQLite database
    conn = sqlite3.connect(db_path)

    # 2) We need two separate queries:
    #    a) Top 10 required skills (required = 1), excluding selected_skills
    #    b) Top 10 optional skills (required = 0), excluding selected_skills
    #
    #    We’ll use SQL’s COUNT(*) + GROUP BY name ORDER BY COUNT DESC LIMIT 10,
    #    and we’ll dynamically bind the `selected_skills` list so that 
    #    any skill in that list is omitted.
    #
    #    NOTE: For parameter substitution, we’ll build the right number of placeholders (`?`)
    #    and then pass `selected_skills` as the tuple of parameters.

    # Build a placeholder string like "?, ?, ?, ..." of length = len(selected_skills)
    placeholders = ",".join("?" for _ in selected_skills) if selected_skills else ""
    # If the user hasn’t selected anything, we don’t need a WHERE name NOT IN (…) clause at all.

    # 2a) Top 10 Required Skills
    if selected_skills:
        sql_required = f"""
        SELECT 
          name AS skill,
          COUNT(*) AS freq
        FROM skills
        WHERE required = 1
          AND name NOT IN ({placeholders})
        GROUP BY name
        ORDER BY freq DESC
        LIMIT 10;
        """
        params_required = tuple(selected_skills)
    else:
        # No selected skills: just pick top 10 required
        sql_required = """
        SELECT 
          name AS skill,
          COUNT(*) AS freq
        FROM skills
        WHERE required = 1
        GROUP BY name
        ORDER BY freq DESC
        LIMIT 10;
        """
        params_required = ()

    df_req = pd.read_sql_query(sql_required, conn, params=params_required)
    df_req["skill_type"] = "Required"  # mark these rows as Required

    # 2b) Top 10 Optional Skills
    if selected_skills:
        sql_optional = f"""
        SELECT 
          name AS skill,
          COUNT(*) AS freq
        FROM skills
        WHERE required = 0
          AND name NOT IN ({placeholders})
        GROUP BY name
        ORDER BY freq DESC
        LIMIT 10;
        """
        params_optional = tuple(selected_skills)
    else:
        sql_optional = """
        SELECT 
          name AS skill,
          COUNT(*) AS freq
        FROM skills
        WHERE required = 0
        GROUP BY name
        ORDER BY freq DESC
        LIMIT 10;
        """
        params_optional = ()

    df_opt = pd.read_sql_query(sql_optional, conn, params=params_optional)
    df_opt["skill_type"] = "Optional"  # mark these rows as Optional

    # 3) Close the DB connection
    conn.close()

    # 4) Combine the two dataframes into one
    df_combined = pd.concat([df_req, df_opt], ignore_index=True)

    # If there happen to be any overlaps (same skill name appearing in both
    # “Required” and “Optional” top‐10), they will show as separate rows with skill_type
    # labels. That’s fine—Plotly will color by skill_type. You’ll see two bars
    # for that skill (one Required, one Optional). Usually a skill is either
    # required or optional in a given posting, so overlap is unlikely.

    # 5) Plot as a grouped bar chart with Plotly Express:
    #    - x-axis: skill name
    #    - y-axis: frequency (how many times it appeared)
    #    - color: “Required” vs. “Optional”
    #    - hover: show exact counts
    #    - title: remind them they’re seeing the “Top 10 required/optional skills
    #      (excluding skills you already have)”

    fig = px.bar(
        df_combined,
        x="skill",
        y="freq",
        color="skill_type",
        barmode="group",
        title="Top 10 Required vs. Optional Skills You Don’t Already Have",
        labels={
            "skill": "Skill Name",
            "freq": "Count",
            "skill_type": "Type"
        }
    )

    # 6) Tweak layout for readability
    fig.update_layout(
        xaxis_tickangle=-45,            # slant labels if they’re long
        uniformtext_mode="hide",        # hide text inside bars if it’s too small
        bargap=0.2,                      # small gap between skill bars
        legend_title_text="",            # remove “skill_type” header in legend
        margin=dict(l=40, r=40, t=80, b=120)  # give some breathing room
    )

    # 7) Finally, show the figure. In a GUI context you might instead
    #    write HTML to a file or embed it in a web view, but fig.show()
    #    will pop up the chart for you during development.
    fig.show()
