import tkinter as tk
from tkinter import ttk
from threading import Thread
from charts.word_cloud_job_titles import run_word_clouds
from threading import Thread
from charts.plot_skill_salary_correlation import plot_skill_salary_correlation
from data_loader import load_skills, load_job_skill_map, load_unique_skills
from charts.plot_top_companies_by_skill import plot_top_companies_by_skill
from charts.plot_skill_cooccurrence_network import plot_skill_cooccurrence_network
from charts.plot_bar import plot_top_skills_bar
from charts.plot_cumulative_line import plot_cumulative_line
from charts.plot_stackplot import plot_stackplot
from charts.plot_subplot2grid import plot_subplot2grid
from charts.plot_pareto_chart import plot_pareto_chart
from charts.plot_diminishing_returns import plot_diminishing_returns
from charts.plot_skill_coverage_comparison import plot_skill_coverage_comparison
from charts.plot_greedy_unlock_curve import compute_greedy_unlock_data, plot_greedy_unlock_curve
from charts.plot_skill_job_heatmap import plot_skill_job_heatmap
from charts.plot_skill_network import compute_skill_edges, plot_skill_network
from charts.plot_skill_galaxy import plot_skill_galaxy
from charts.plot_skill_clusters import plot_skill_clusters
from charts.plot_skill_clusters_radial import plot_skill_clusters_radial
from charts.plot_salary_distribution import plot_salary_distribution

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from charts.plot_remote_vs_onsite import plot_remote_vs_onsite
import plotly.express as px
import pandas as pd
from threading import Thread

def compute_and_plot_skill_gap(user_selected_skills, 
                               job_skill_map, 
                               job_info_map, 
                               max_missing=3, 
                               top_n=10):
    """
    1) user_selected_skills: list of skill‐strings (e.g. ["python","sql"]).
    2) job_skill_map:   { job_id: set([...required skills...]), ... }
    3) job_info_map:    { job_id: (title, company), ... }
    4) max_missing:     only include jobs where len(missing) <= max_missing
    5) top_n:           how many missing‐skill bars to show
    
    Produces a horizontal bar chart `skill_gap_analysis.html` showing
    the top_n most frequently missing skills (across all jobs where
    the user is missing ≤ max_missing skills).
    """

    # Normalize the user's skills
    user_set = set(s.strip().lower() for s in user_selected_skills)

    # Count how often each missing skill appears (only for jobs missing ≤ max_missing total).
    missing_counts = {}
    for job_id, req_skills in job_skill_map.items():
        # lowercase & stripped skills in job_skill_map should already be normalized,
        # but just in case:
        req_lower = set(s.strip().lower() for s in req_skills)

        missing = req_lower - user_set
        if 0 < len(missing) <= max_missing:
            for skill in missing:
                missing_counts[skill] = missing_counts.get(skill, 0) + 1

    # Build a DataFrame of (skill, frequency), take top_n
    gap_df = (
        pd.DataFrame.from_dict(missing_counts, orient='index', columns=['frequency'])
          .nlargest(top_n, 'frequency')
          .reset_index()
          .rename(columns={'index': 'skill'})
    )

    if gap_df.empty:
        # If no missing skills (or no jobs within max_missing), show a simple message.
        import webbrowser
        html_text = f"""
        <html>
          <body style="background-color:#2b2b2b; color:white; font-family:sans-serif;">
            <h2 style="text-align:center; padding-top:50px;">
              No jobs found where you're missing ≤ {max_missing} skill(s).
            </h2>
          </body>
        </html>
        """
        path = "skill_gap_analysis.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_text)
        webbrowser.open_new_tab(path)
        return

    # Create a horizontal bar chart
    fig = px.bar(
        gap_df,
        x='frequency',
        y='skill',
        orientation='h',
        title=(
            f"Top {top_n} Skills You’re Missing "
            f"(for jobs needing ≤ {max_missing} additional skills)"
        ),
    )
    fig.update_layout(
        template="plotly_dark",
        yaxis={'categoryorder': 'total ascending'},
        xaxis_title="Number of Postings Missing This Skill",
        yaxis_title="Skill"
    )

    # Write to HTML and auto‐open
    out_file = "skill_gap_analysis.html"
    fig.write_html(out_file, auto_open=True)



# ──────────────────────────────────────────────────────────────────────────────
# Helper to bind mousewheel scrolling to a specific canvas
def bind_mousewheel(widget, target_canvas):
    def _on_mousewheel(event):
        target_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    widget.bind("<Enter>", lambda e: widget.bind_all("<MouseWheel>", _on_mousewheel))
    widget.bind("<Leave>", lambda e: widget.unbind_all("<MouseWheel>"))


# ──────────────────────────────────────────────────────────────────────────────
# Main application
root = tk.Tk()
root.title("Skill Chart Generator")
root.geometry("1000x600")  # wider so we have space for two columns

# Load data once
raw_skills       = load_skills()
current_skills   = raw_skills.copy()
all_skills       = load_unique_skills()  # list of (skill, freq)
job_skill_map, job_info_map = load_job_skill_map()
skill_vars       = {}  # { skill: tk.BooleanVar() }

# ──────────────────────────────────────────────────────────────────────────────
# Column 0: Skill Selection Frame (Search + Scrollable Checkboxes)  ───────────
skill_frame = ttk.LabelFrame(root, text="Skill Selection", padding=(5,5))
skill_frame.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=5, pady=5)

# Make column 0 stretch vertically
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=0)  # fixed width

# Search entry
search_entry = ttk.Entry(skill_frame, width=30)
search_entry.grid(row=0, column=0, padx=5, pady=(5, 10))
search_entry.insert(0, "Search for skills...")

# Scrollable checkbox area
checkbox_container = tk.Frame(skill_frame)
checkbox_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

# Configure row/column so that the canvas expands
skill_frame.grid_rowconfigure(1, weight=1)
skill_frame.grid_columnconfigure(0, weight=1)

skill_canvas    = tk.Canvas(checkbox_container, width=300, height=300)
skill_scrollbar = ttk.Scrollbar(checkbox_container, orient="vertical", command=skill_canvas.yview)
skill_list_frame= tk.Frame(skill_canvas)

skill_list_frame.bind(
    "<Configure>",
    lambda e: skill_canvas.configure(scrollregion=skill_canvas.bbox("all"))
)

skill_canvas.create_window((0,0), window=skill_list_frame, anchor="nw")
skill_canvas.configure(yscrollcommand=skill_scrollbar.set)

skill_canvas.pack(side="left", fill="both", expand=True)
skill_scrollbar.pack(side="right", fill="y")

# Mousewheel binding
bind_mousewheel(skill_canvas, skill_canvas)


def render_skill_checkboxes(skills_to_show):
    """Rebuild the checkbox list inside skill_list_frame."""
    for widget in skill_list_frame.winfo_children():
        widget.destroy()
    for skill, freq in skills_to_show:
        if skill not in skill_vars:
            skill_vars[skill] = tk.BooleanVar()
        label = f"{skill} ({round(freq * 100)}%)"
        cb = ttk.Checkbutton(
            skill_list_frame,
            text=label,
            variable=skill_vars[skill],
            onvalue=True,
            offvalue=False
        )
        cb.pack(anchor="w", padx=5, pady=2)

def get_user_selected_skills():
    return [skill for skill, var in skill_vars.items() if var.get()]


# Debounce filter logic
filter_job = None
def filter_skills_delayed(event=None):
    global filter_job
    if filter_job:
        root.after_cancel(filter_job)
    filter_job = root.after(500, apply_filter)

def apply_filter():
    search_text = search_entry.get().strip().lower()
    filtered = [(s, f) for s, f in all_skills if search_text in s]
    render_skill_checkboxes(filtered)

search_entry.bind("<KeyRelease>", filter_skills_delayed)

# Initially render all skills
render_skill_checkboxes(all_skills)


# ──────────────────────────────────────────────────────────────────────────────
# Column 1: Right Side (Actions, Charts, Clusters, Job Matches)  ──────────────
right_container = ttk.Frame(root)
right_container.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

root.grid_columnconfigure(1, weight=1)
right_container.grid_rowconfigure(3, weight=1)  # make job matches area expand


# ─── Actions Frame (Update, Find Jobs, Show Connections) ────────────────────
actions_frame = ttk.LabelFrame(right_container, text="Actions", padding=(5,5))
actions_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(0,5))
actions_frame.grid_columnconfigure(0, weight=1)
actions_frame.grid_columnconfigure(1, weight=1)

# Status label
status_label = ttk.Label(actions_frame, text="Selected: None")
status_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,5))

def update_skills():
    global current_skills
    selected = get_user_selected_skills()
    current_skills[:] = [s for s in raw_skills if s not in selected]
    status_label.config(text=f"Selected: {', '.join(selected) or 'None'}")

def find_matching_jobs():
    # Clear existing results
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    user_skills = set(get_user_selected_skills())
    matched = []
    for job_id, req_skills in job_skill_map.items():
        if req_skills.issubset(user_skills):
            matched.append(job_info_map[job_id])

    if matched:
        for title, company in matched:
            ttk.Label(scrollable_frame, text=f"✅ {title} @ {company}", anchor="w").pack(fill="x", padx=5, pady=2)
    else:
        ttk.Label(scrollable_frame, text="❌ No exact matches found.", foreground="red").pack(fill="x", padx=5, pady=2)

# Update Skills button
btn_update = ttk.Button(actions_frame, text="Update Skills", command=update_skills)
btn_update.grid(row=1, column=0, padx=5, pady=2, sticky="ew")

# Find Matching Jobs button
btn_find = ttk.Button(actions_frame, text="Find Matching Jobs", command=find_matching_jobs)
btn_find.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

# Show Connections checkbox
show_edges_var = tk.BooleanVar(value=False)
chk_show_conn = ttk.Checkbutton(
    actions_frame,
    text="Show Connections",
    variable=show_edges_var,
    command=lambda: Thread(target=lambda: plot_skill_galaxy(job_skill_map, show_edges=show_edges_var.get())).start()
)
chk_show_conn.grid(row=2, column=0, columnspan=2, pady=5, sticky="w")


# ─── Charts Frame (all chart buttons) ───────────────────────────────────────
charts_frame = ttk.LabelFrame(right_container, text="Charts", padding=(5,5))
charts_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0,5))
for i in range(2):
    charts_frame.grid_columnconfigure(i, weight=1)

# Diminishing Returns Chart
btn_diminishing = ttk.Button(
    charts_frame,
    text="Diminishing Returns",
    command=lambda: plot_diminishing_returns(get_user_selected_skills()),
    width=25
)
btn_diminishing.grid(row=0, column=0, padx=5, pady=2, sticky="ew")

# Coverage Comparison Chart
btn_coverage = ttk.Button(
    charts_frame,
    text="Coverage Comparison",
    command=lambda: plot_skill_coverage_comparison(job_skill_map, get_user_selected_skills()),
    width=25
)
btn_coverage.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

# Greedy Unlock Chart (background thread)
def start_greedy_chart():
    user_skills = get_user_selected_skills()
    def run_chart():
        jm, _ = job_skill_map, job_info_map
        coverage_progress, selected_skills = compute_greedy_unlock_data(jm, user_skills=user_skills)
        root.after(0, lambda: show_greedy_fig(coverage_progress, selected_skills))
    def show_greedy_fig(coverage_progress, selected_skills):
        fig = plot_greedy_unlock_curve(coverage_progress, selected_skills)
        fig_win = tk.Toplevel(root)
        fig_win.title("Greedy Unlock Curve")
        canvas = FigureCanvasTkAgg(fig, master=fig_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    Thread(target=run_chart, daemon=True).start()

btn_greedy = ttk.Button(
    charts_frame,
    text="Greedy Unlock Curve",
    command=start_greedy_chart,
    width=25
)
btn_greedy.grid(row=1, column=0, padx=5, pady=2, sticky="ew")

# Skill–Job Heatmap
btn_heatmap = ttk.Button(
    charts_frame,
    text="Skill–Job Heatmap",
    command=lambda: plot_skill_job_heatmap(job_skill_map),
    width=25
)
btn_heatmap.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

# Skill Network Graph
btn_network = ttk.Button(
    charts_frame,
    text="Skill Network Graph",
    command=lambda: plot_skill_network(compute_skill_edges(load_job_skill_map()[0])),
    width=25
)
btn_network.grid(row=2, column=0, padx=5, pady=2, sticky="ew")

# Skill Galaxy (3D Plot with toggle above)
btn_galaxy = ttk.Button(
    charts_frame,
    text="Skill Galaxy (3D)",
    command=lambda: Thread(target=lambda: plot_skill_galaxy(job_skill_map, show_edges=show_edges_var.get())).start(),
    width=25
)
btn_galaxy.grid(row=2, column=1, padx=5, pady=2, sticky="ew")

# Bar Chart
btn_bar = ttk.Button(
    charts_frame,
    text="Bar Chart",
    command=lambda: plot_top_skills_bar(job_skill_map, get_user_selected_skills()),
    width=25
)
btn_bar.grid(row=3, column=0, padx=5, pady=2, sticky="ew")

# Cumulative Line Chart
btn_cumline = ttk.Button(
    charts_frame,
    text="Cumulative Line",
    command=lambda: plot_cumulative_line(current_skills),
    width=25
)
btn_cumline.grid(row=3, column=1, padx=5, pady=2, sticky="ew")

# Stackplot
btn_stack = ttk.Button(
    charts_frame,
    text="Stackplot",
    command=lambda: plot_stackplot(current_skills),
    width=25
)
btn_stack.grid(row=4, column=0, padx=5, pady=2, sticky="ew")

# Subplot2Grid
btn_subplot = ttk.Button(
    charts_frame,
    text="Subplot2Grid",
    command=lambda: plot_subplot2grid(current_skills),
    width=25
)
btn_subplot.grid(row=4, column=1, padx=5, pady=2, sticky="ew")

# Pareto Chart
btn_pareto = ttk.Button(
    charts_frame,
    text="Pareto Chart",
    command=lambda: plot_pareto_chart(current_skills),
    width=25
)
btn_pareto.grid(row=5, column=0, padx=5, pady=2, sticky="ew")

# Salary Distribution
btn_salary = ttk.Button(
    charts_frame,
    text="Salary Distribution",
    command=lambda: plot_salary_distribution(),
    width=25
)
btn_salary.grid(row=6, column=0, padx=5, pady=2, sticky="ew")

# 3D Skill Clusters
btn_clusters3d = ttk.Button(
    charts_frame,
    text="Skill Clusters (3D)",
    command=lambda: Thread(target=lambda: plot_skill_clusters(job_skill_map)).start(),
    width=25
)
btn_clusters3d.grid(row=5, column=1, padx=5, pady=2, sticky="ew")

# 2D Skill Clusters (Radial)
btn_clusters2d = ttk.Button(
    charts_frame,
    text="Skill Clusters (2D)",
    command=lambda: Thread(target=lambda: plot_skill_clusters_radial(job_skill_map)).start(),
    width=25
)
btn_clusters2d.grid(row=6, column=1, columnspan=1, padx=5, pady=2, sticky="ew")

btn_skill_gap = ttk.Button(
    charts_frame,
    text="Skill Gap Analysis",
    command=lambda: Thread(
        target=lambda: compute_and_plot_skill_gap(
            get_user_selected_skills(),
            job_skill_map,
            job_info_map,
            max_missing=3,
            top_n=10
        )
    ).start(),
    width=25
)
# Place it below Salary Distribution (row=7, col=0)
btn_skill_gap.grid(row=7, column=0, padx=5, pady=2, sticky="ew")

# ─── Word Cloud of Job Titles ───────────────────────────────────────────────
btn_word_cloud = ttk.Button(
    charts_frame,
    text="Word Cloud: Job Titles",
    command=lambda: Thread(target=lambda: run_word_clouds("preview_jobs.db")).start(),
    width=25
)
# Place it below Skill Gap Analysis (adjust row/column as needed)
btn_word_cloud.grid(row=7, column=1, padx=5, pady=2, sticky="ew")

# ─── Remote vs. On-Site Pie Chart ─────────────────────────────────────────
btn_remote_onsite = ttk.Button(
    charts_frame,
    text="Remote vs. On-Site",
    command=lambda: Thread(
        target=lambda: plot_remote_vs_onsite("preview_jobs.db")
    ).start(),
    width=25
)
# Adjust row/column to place it where you like; e.g., row=7, column=1:
btn_remote_onsite.grid(row=8, column=0, padx=5, pady=2, sticky="ew")

from charts.plot_certification_distribution import plot_certification_distribution
# ─── Certification Distribution Chart ─────────────────────────────────────
btn_cert_dist = ttk.Button(
    charts_frame,
    text="Certifications Distribution",
    command=lambda: Thread(
        target=lambda: plot_certification_distribution("preview_jobs.db"),
        daemon=True
    ).start(),
    width=25
)
# Place it at row=15, spanning both columns:
btn_cert_dist.grid(row=8, column=1, columnspan=1, padx=5, pady=2, sticky="ew")


from charts.plot_certification_salary_impact import plot_certification_salary_impact
# ─── Certification Salary Impact Chart ────────────────────────────────────
btn_cert_salary_imp = ttk.Button(
    charts_frame,
    text="Cert Salary Impact",
    command=lambda: Thread(
        target=lambda: plot_certification_salary_impact("preview_jobs.db"),
        daemon=True
    ).start(),
    width=25
)
# Place at row=9, spanning one column
btn_cert_salary_imp.grid(row=9, column=0, columnspan=1, padx=5, pady=2, sticky="ew")




# ─── Show Top Companies (uses GUI‐selected skills) ─────────────────────────
from charts.plot_top_companies_by_skill import plot_top_companies_by_skill

btn_top_companies = ttk.Button(
    charts_frame,
    text="Show Top Companies",
    command=lambda: Thread(
        target=lambda: plot_top_companies_by_skill(
            get_user_selected_skills(),   # pass the list of checked skills
            "preview_jobs.db"
        ),
        daemon=True
    ).start(),
    width=25
)
# Place it on the next free row, e.g. row=8, spanning both columns:
btn_top_companies.grid(row=9, column=1, columnspan=1, padx=5, pady=(5,10), sticky="ew")


from charts.plot_certification_cooccurrence_network import plot_certification_cooccurrence_network
# ─── Certification Co-Occurrence Network ──────────────────────────────────
btn_cert_coocc = ttk.Button(
    charts_frame,
    text="Cert Co-Occurrence",
    command=lambda: Thread(
        target=lambda: plot_certification_cooccurrence_network(
            "preview_jobs.db",
            min_pair_count=5,
            min_node_freq=5,
            spring_k=0.5,
            spring_iterations=50
        ),
        daemon=True
    ).start(),
    width=25
)
# Place it at row=18, spanning both columns
btn_cert_coocc.grid(row=10, column=0, columnspan=1, padx=5, pady=2, sticky="ew")



# ─── Skill–Salary Correlation Chart ─────────────────────────────────────────
btn_skill_salary_corr = ttk.Button(
    charts_frame,
    text="Skill–Salary Correlation",
    command=lambda: Thread(
        target=lambda: plot_skill_salary_correlation("preview_jobs.db"),
        daemon=True
    ).start(),
    width=25
)
# Put it at row=11, column=0 (adjust if needed)
btn_skill_salary_corr.grid(row=10, column=1, columnspan=1, padx=5, pady=2, sticky="ew")
from charts.plot_skill_gap_similarity_matrix import plot_skill_gap_similarity_matrix
# ─── Skill‐Gap Similarity Matrix ────────────────────────────────────────────
btn_skill_gap_sim = ttk.Button(
    charts_frame,
    text="Missing‐Skill Similarity",
    command=lambda: Thread(
        target=lambda: plot_skill_gap_similarity_matrix(
            get_user_selected_skills(),   # pass the GUI‐selected skills
            "preview_jobs.db"
        ),
        daemon=True
    ).start(),
    width=25
)
btn_skill_gap_sim.grid(row=11, column=0, columnspan=1, padx=5, pady=2, sticky="ew")

from charts.plot_company_skill_focus import plot_company_skill_focus
# ─── Company Skill Focus Chart ─────────────────────────────────────────────
btn_company_focus = ttk.Button(
    charts_frame,
    text="Company Skill Focus",
    command=lambda: Thread(
        target=lambda: plot_company_skill_focus(
            get_user_selected_skills(),   # pass GUI‐selected skills
            "preview_jobs.db", 
            top_n_companies=5, 
            top_n_skills=10
        ),
        daemon=True
    ).start(),
    width=25
)
# Place it at an unused row, e.g., row=13, column=0 (adjust as needed)
btn_company_focus.grid(row=11, column=1, columnspan=1, padx=5, pady=2, sticky="ew")

from charts.plot_title_salary_bubble_chart import plot_title_salary_bubble_chart
# ─── Title‐Salary Bubble Chart ───────────────────────────────────────────────
btn_title_salary = ttk.Button(
    charts_frame,
    text="Title‐Salary Bubble",
    command=lambda: Thread(
        target=lambda: plot_title_salary_bubble_chart("preview_jobs.db"),
        daemon=True
    ).start(),
    width=25
)
# Place it at an unused row, e.g., row=14, column=0 (adjust as needed)
btn_title_salary.grid(row=12, column=0, columnspan=1, padx=5, pady=2, sticky="ew")

from charts.plot_skill_similarity_tSNE import plot_skill_similarity_tSNE
# ─── Skill‐Similarity t-SNE ─────────────────────────────────────────────────
btn_skill_tsne = ttk.Button(
    charts_frame,
    text="Skill t-SNE",
    command=lambda: Thread(
        target=lambda: plot_skill_similarity_tSNE(
            "preview_jobs.db",
            perplexity=30,
            max_iter=500
        ),
        daemon=True
    ).start(),
    width=25
)
btn_skill_tsne.grid(row=12, column=1, columnspan=1, padx=5, pady=2, sticky="ew")


from charts.plot_company_skill_cluster_sankey import plot_company_skill_cluster_sankey
# ─── Company → Skill‐Cluster Sankey ──────────────────────────────────────
btn_company_skill_sankey = ttk.Button(
    charts_frame,
    text="Company ↔ Skill Clusters",
    command=lambda: Thread(
        target=lambda: plot_company_skill_cluster_sankey(
            "preview_jobs.db",
            n_skill_clusters=10,
            min_jobs_per_company=5,
            top_skills_per_cluster=5
        ),
        daemon=True
    ).start(),
    width=25
)
btn_company_skill_sankey.grid(row=13, column=0, columnspan=1, padx=5, pady=2, sticky="ew")


from charts.plot_certification_presence_by_skill_cluster import (
    plot_certification_presence_by_skill_cluster
)
# ─── Certification Presence by Skill Cluster ──────────────────────────────
btn_cert_by_cluster = ttk.Button(
    charts_frame,
    text="Certs by Skill Cluster",
    command=lambda: Thread(
        target=lambda: plot_certification_presence_by_skill_cluster(
            "preview_jobs.db",
            min_edge_weight=3,       # keep skill‐edges with co‐occurrence ≥ 3
            min_skill_degree=1,      # include skills appearing at least once
            top_n_certs_per_cluster=10
        ),
        daemon=True
    ).start(),
    width=25
)
btn_cert_by_cluster.grid(row=13, column=1, columnspan=1, padx=5, pady=2, sticky="ew")





# ─── Job Matches Frame (scrollable) ────────────────────────────────────────
matches_frame = ttk.LabelFrame(right_container, text="Job Matches", padding=(5,5))
matches_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=(5,5))

right_container.grid_rowconfigure(2, weight=1)

canvas_matches = tk.Canvas(matches_frame, background="#f0f0f0")
scrollbar_matches = ttk.Scrollbar(matches_frame, orient="vertical", command=canvas_matches.yview)
scrollable_frame = ttk.Frame(canvas_matches)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas_matches.configure(scrollregion=canvas_matches.bbox("all"))
)

canvas_matches.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas_matches.configure(yscrollcommand=scrollbar_matches.set)

canvas_matches.pack(side="left", fill="both", expand=True)
scrollbar_matches.pack(side="right", fill="y")

# Mousewheel scrolling for matches
bind_mousewheel(canvas_matches, canvas_matches)


# ──────────────────────────────────────────────────────────────────────────────
# Final setup
print("GUI loaded successfully. Ready.")
root.mainloop()
