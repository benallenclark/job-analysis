import tkinter as tk
from data_loader import load_skills
from data_loader import load_job_skill_map
from data_loader import load_unique_skills
from charts.plot_bar import plot_top_skills_bar
from charts.plot_cumulative_line import plot_cumulative_line
from charts.plot_stackplot import plot_stackplot
from charts.plot_subplot2grid import plot_subplot2grid
from charts.plot_pareto_chart import plot_pareto_chart
from charts.plot_diminishing_returns import plot_diminishing_returns
from charts.plot_skill_coverage_comparison import plot_skill_coverage_comparison
from charts.plot_greedy_unlock_curve import plot_greedy_unlock_curve
from charts.plot_skill_job_heatmap import plot_skill_job_heatmap
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from charts.plot_skill_network import compute_skill_edges, plot_skill_network
from charts.plot_skill_galaxy import plot_skill_galaxy
from charts.plot_greedy_unlock_curve import compute_greedy_unlock_data, plot_greedy_unlock_curve
import tkinter as tk
from tkinter import ttk
from threading import Thread
from charts.plot_skill_galaxy import plot_skill_galaxy
from charts.plot_skill_clusters import plot_skill_clusters




def show_skill_galaxy():
    job_skill_map, _ = load_job_skill_map()
    plot_skill_galaxy(job_skill_map, show_edges=show_edges_var.get())

def run_skill_clusters():
    job_skill_map, _ = load_job_skill_map()
    print("Launching 3D skill cluster visualization...")
    plot_skill_clusters(job_skill_map)






def start_greedy_chart():
    user_skills = get_user_selected_skills()  # Capture user-selected skills

    def run_chart():
        # Step 1: Load data and compute unlock curve using user-selected skills
        job_skill_map, _ = load_job_skill_map()
        coverage_progress, selected_skills = compute_greedy_unlock_data(
            job_skill_map,
            user_skills=user_skills
        )

        # Step 2: Schedule UI update in main thread
        root.after(0, lambda: show_fig(coverage_progress, selected_skills))

    def show_fig(coverage_progress, selected_skills):
        from charts.plot_greedy_unlock_curve import plot_greedy_unlock_curve
        fig = plot_greedy_unlock_curve(coverage_progress, selected_skills)

        fig_window = tk.Toplevel(root)
        fig_window.title("Greedy Unlock Curve")

        canvas = FigureCanvasTkAgg(fig, master=fig_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    Thread(target=run_chart, daemon=True).start()






    
# Base skill list
raw_skills = load_skills()
current_skills = raw_skills.copy()
excluded_skills = []

all_skills = load_unique_skills()
filtered_skills = all_skills.copy()
filter_job = None  # global debounce tracker

skill_vars = {}  # key = skill name, value = tk.BooleanVar

# Create GUI
root = tk.Tk()
root.title("Skill Chart Generator")
root.geometry("600x900")

# # Entry for typing excluded skills
# entry = tk.Entry(root, width=50)
# entry.pack(pady=5)
# entry.insert(0, "Type skills you already have, separated by commas")

# Label to show exclusions
status_label = tk.Label(root, text="Excluded: None")
status_label.pack()

def render_skill_checkboxes(skills_to_show):
    for widget in skill_list_frame.winfo_children():
        widget.destroy()
    for skill, freq in skills_to_show:
        if skill not in skill_vars:
            skill_vars[skill] = tk.BooleanVar()
        label = f"{skill} ({round(freq * 100)}%)"
        cb = tk.Checkbutton(skill_list_frame, text=label, variable=skill_vars[skill], anchor="w", justify="left")
        cb.pack(fill="x", padx=5, pady=1)

        
def get_user_selected_skills():
    return [skill for skill, var in skill_vars.items() if var.get()]


# Update function
def update_skills():
    global current_skills, excluded_skills
    selected_skills = get_user_selected_skills()
    current_skills[:] = [s for s in raw_skills if s not in selected_skills]
    status_label.config(text=f"Selected: {', '.join(selected_skills) or 'None'}")

def bind_mousewheel(widget, target_canvas):
    def _on_mousewheel(event):
        target_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    widget.bind("<Enter>", lambda e: widget.bind_all("<MouseWheel>", _on_mousewheel))
    widget.bind("<Leave>", lambda e: widget.unbind_all("<MouseWheel>"))



job_skill_map, job_info_map = load_job_skill_map()

# def find_matching_jobs():
#     user_skills = set([s.strip().lower() for s in entry.get().split(",") if s.strip()])
#     matched_jobs = []

#     for job_id, required_skills in job_skill_map.items():
#         if required_skills.issubset(user_skills):
#             matched_jobs.append(job_info_map[job_id])

#     if matched_jobs:
#         match_text = "\n".join([f"✅ {title} @ {company}" for title, company in matched_jobs])
#     else:
#         match_text = "❌ No exact matches found."

def find_matching_jobs():
    # Clear existing results
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    user_skills = set(get_user_selected_skills())
    matched_jobs = []

    for job_id, required_skills in job_skill_map.items():
        if required_skills.issubset(user_skills):
            matched_jobs.append(job_info_map[job_id])

    if matched_jobs:
        for title, company in matched_jobs:
            tk.Label(scrollable_frame, text=f"✅ {title} @ {company}", anchor="w", justify="left").pack(fill="x", padx=5, pady=2)
    else:
        tk.Label(scrollable_frame, text="❌ No exact matches found.", fg="red").pack(fill="x", padx=5, pady=2)

    
# Update button
tk.Button(root, text="Update Skills", command=update_skills).pack(pady=5)

tk.Button(root, text="Find Matching Jobs", command=find_matching_jobs).pack(pady=5)

tk.Button(root, text="Diminishing Returns Chart", command=lambda: plot_diminishing_returns(get_user_selected_skills())).pack(pady=5)

tk.Button(root, text="Coverage Comparison Chart", command=lambda: plot_skill_coverage_comparison(job_skill_map, get_user_selected_skills())).pack(pady=5)

tk.Button(root, text="Greedy Unlock Chart", command=start_greedy_chart).pack(pady=5)

tk.Button(root, text="Skill–Job Heatmap", command=lambda: plot_skill_job_heatmap(job_skill_map)).pack(pady=5)

tk.Button(root, text="Skill Network Graph", command=lambda: plot_skill_network(
    compute_skill_edges(load_job_skill_map()[0])
)).pack(pady=5)
show_edges_var = tk.BooleanVar(value=False)


tk.Checkbutton(root, text="Show Connections", variable=show_edges_var, command=show_skill_galaxy).pack(pady=3)

tk.Button(root, text="Skill Clusters (3D)", command=lambda: Thread(target=run_skill_clusters).start()).pack(pady=5)

# Chart buttons
buttons = [
    ("Bar Chart", lambda: plot_top_skills_bar(job_skill_map, get_user_selected_skills())),
    ("Cumulative Line Chart", lambda: plot_cumulative_line(current_skills)),
    ("Stackplot", lambda: plot_stackplot(current_skills)),
    ("Subplot2Grid", lambda: plot_subplot2grid(current_skills)),
    ("Pareto Chart", lambda: plot_pareto_chart(current_skills)),
]

for label, action in buttons:
    tk.Button(root, text=label, command=action, height=2, width=40).pack(pady=4)
    
    
    
search_entry = tk.Entry(root, width=50)
search_entry.pack(pady=5)
search_entry.insert(0, "Search for skills...")

def filter_skills_delayed(event=None):
    global filter_job
    if filter_job is not None:
        root.after_cancel(filter_job)  # cancel any pending filter call
    filter_job = root.after(1500, apply_filter)  # wait 1.5s after typing stops

def apply_filter():
    search_text = search_entry.get().strip().lower()
    filtered = [(s, f) for s, f in all_skills if search_text in s]
    render_skill_checkboxes(filtered)


search_entry.bind("<KeyRelease>", filter_skills_delayed)

skill_frame_container = tk.Frame(root)
skill_canvas = tk.Canvas(skill_frame_container, height=200, width=460)
skill_scrollbar = tk.Scrollbar(skill_frame_container, orient="vertical", command=skill_canvas.yview)
skill_list_frame = tk.Frame(skill_canvas)

skill_list_frame.bind(
    "<Configure>",
    lambda e: skill_canvas.configure(
        scrollregion=skill_canvas.bbox("all")
    )
)

skill_canvas.create_window((0, 0), window=skill_list_frame, anchor="nw")
skill_canvas.configure(yscrollcommand=skill_scrollbar.set)

skill_frame_container.pack(pady=10)
skill_canvas.pack(side="left", fill="both", expand=True)
skill_scrollbar.pack(side="right", fill="y")


    
# Scrollable frame setup for job match results
container = tk.Frame(root)
container.pack(fill="both", expand=True, padx=10, pady=10)


canvas = tk.Canvas(container, bg="#00e1ff", highlightthickness=0)  # light gray background
scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)

scrollable_frame = tk.Frame(canvas, bg="#f2f2f2")  # match canvas background

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")
render_skill_checkboxes(all_skills)

# Enable mouse wheel scrolling when hovering either container
bind_mousewheel(skill_canvas, skill_canvas)
bind_mousewheel(canvas, canvas)



print("GUI loaded successfully. Ready.")

root.mainloop()
