import pandas as pd
from dash import Dash, Input, Output, dcc, html
from PIL import Image, ImageDraw, ImageFont
import plotly.express as px

from config import monthly_questions, discrete_colours
from utils import (
    read_most_recent_file,
    create_numeric_columns,
    round_to_end_of_week,
    create_bar_chart,
    create_pie_chart,
    create_time_series_chart,
    create_empty_image,
)

# Read in most recent file
df = read_most_recent_file("src/data/Results/Monthly/*")

# Create numeric-only versions of data columns
df = create_numeric_columns(
    df,
    monthly_questions["bar_chart_questions"] + monthly_questions["pie_chart_questions"],
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
    options=monthly_questions["bar_chart_questions"]
    + monthly_questions["pie_chart_questions"]
    + monthly_questions["free_text_questions"],
    value=monthly_questions["bar_chart_questions"][0],
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
    if selected_metric in monthly_questions["bar_chart_questions"]:
        fig = create_bar_chart(df, selected_metric, most_recent_week)
        fig.update_layout(yaxis=dict(tickmode="linear", tick0=0, dtick=1))
        fig.update_traces(width=1)

    elif selected_metric in monthly_questions["pie_chart_questions"]:
        fig = create_pie_chart(df, selected_metric, most_recent_week)

    elif selected_metric in monthly_questions["free_text_questions"]:
        response_text = df.loc[
            df["Week ending"] == most_recent_week, selected_metric
        ].to_list()

        img = Image.new("RGB", (5000, 1280), (255, 255, 255))
        d1 = ImageDraw.Draw(img)
        myFont = ImageFont.truetype("src/data/Fonts/Calibri Regular.ttf", 100)

        x_position = 40
        y_position = 10
        count = 0
        for response in response_text:
            d1.text(
                (x_position, y_position),
                response.capitalize(),
                fill=discrete_colours[count],
                font=myFont,
            )
            y_position += 200
            count += 1

        fig = px.imshow(img)
        fig.update_layout(coloraxis_showscale=False)
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)

    return fig


@app.callback(
    Output(component_id="survey_results_bottom", component_property="figure"),
    Input(component_id=question_dropdown, component_property="value"),
)
def update_bottom_graph(selected_metric):
    if selected_metric in monthly_questions["bar_chart_questions"]:
        over_time = df.groupby(["Week ending", "Role"])[
            f"Numeric: {selected_metric}"
        ].mean()
        over_time = over_time.rename("average").reset_index()
        fig = create_time_series_chart(over_time, selected_metric, separate_roles=True)

    elif selected_metric in monthly_questions["pie_chart_questions"]:
        over_time = df.groupby(["Week ending"])[f"Numeric: {selected_metric}"].mean()
        over_time = over_time.rename("average").reset_index()
        fig = create_time_series_chart(over_time, selected_metric)

    else:
        fig = create_empty_image()

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
