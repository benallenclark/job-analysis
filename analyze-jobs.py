from data_loader import load_skills
from charts.plot_bar import plot_top_skills_bar
from charts.plot_cumulative_line import plot_cumulative_line
from charts.plot_stackplot import plot_stackplot
from charts.plot_subplot2grid import plot_subplot2grid
from charts.plot_pareto_chart import plot_steamgraph

skills = load_skills()

# Comment/uncomment as needed or add CLI flags later
# plot_top_skills_bar(skills)
# plot_cumulative_line(skills)
plot_stackplot(skills)
# plot_subplot2grid(skills)
# plot_steamgraph(skills)