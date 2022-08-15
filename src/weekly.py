import pandas as pd
from dash import Dash, Input, Output, dcc, html

from config import weekly_questions
from utils import (
    create_bar_chart,
    create_empty_image,
    create_numeric_columns,
    create_pie_chart,
    create_time_series_chart,
    get_animal_picture,
    read_most_recent_file,
    round_to_end_of_week,
)

# Read in most recent file
df = read_most_recent_file("src/data/Results/Weekly/*")

# Create numeric-only versions of data columns
df = create_numeric_columns(
    df,
    weekly_questions["bar_chart_questions"] + weekly_questions["pie_chart_questions"],
)

# Group dates to weeks
df["Week ending"] = (
    df["Completion time"].apply(lambda x: round_to_end_of_week(x)).dt.floor("D")
)
most_recent_week = df["Week ending"].max()

# Match with whether or not they're are a developer
df_roles = pd.read_csv("src/data/Reference/Roles.csv")
df = pd.merge(df, df_roles, on="Name", how="left")
missing_in_roles_table = list(set(df.loc[df["Role"].isna(), "Name"].to_list()))
if len(missing_in_roles_table) > 0:
    print(f"Please add {', '.join(missing_in_roles_table)} to the roles table")
    df = df.fillna({"Role": "Developer"})


# Setting up the dash app
app = Dash()

question_dropdown = dcc.Dropdown(
    options=weekly_questions["bar_chart_questions"]
    + weekly_questions["pie_chart_questions"]
    + weekly_questions["picture_questions"],
    value=weekly_questions["bar_chart_questions"][0],
)

app.layout = html.Div(
    children=[
        html.H1(children="DI Team Dashboard"),
        question_dropdown,
        html.Div(
            children=[
                html.Div([dcc.Graph(id="survey_results_top")]),
                html.Div([dcc.Graph(id="survey_results_bottom")]),
            ]
        ),
    ]
)


@app.callback(
    Output(component_id="survey_results_top", component_property="figure"),
    Input(component_id=question_dropdown, component_property="value"),
)
def update_top_graph(selected_metric):
    if selected_metric in weekly_questions["bar_chart_questions"]:
        fig = create_bar_chart(df, selected_metric, most_recent_week, "week")
        fig.update_layout(yaxis=dict(tickmode="linear", tick0=0, dtick=1))
        fig.update_traces(width=1)

    elif selected_metric in weekly_questions["pie_chart_questions"]:
        fig = create_pie_chart(df, selected_metric, most_recent_week, "week")

    elif selected_metric in weekly_questions["picture_questions"]:
        fig = get_animal_picture(df, most_recent_week)

    return fig


@app.callback(
    Output(component_id="survey_results_bottom", component_property="figure"),
    Input(component_id=question_dropdown, component_property="value"),
)
def update_bottom_graph(selected_metric):
    if selected_metric in weekly_questions["bar_chart_questions"]:
        over_time = df.groupby(["Week ending", "Role"])[
            f"Numeric: {selected_metric}"
        ].mean()
        over_time = over_time.rename("average").reset_index()
        fig = create_time_series_chart(over_time, selected_metric, separate_roles=True)

    elif selected_metric in weekly_questions["pie_chart_questions"]:
        over_time = df.groupby(["Week ending"])[f"Numeric: {selected_metric}"].mean()
        over_time = over_time.rename("average").reset_index()
        fig = create_time_series_chart(over_time, selected_metric)

    else:
        fig = create_empty_image()

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
