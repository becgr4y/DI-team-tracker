import glob
import os
import smtplib

import numpy as np
import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html
from skimage import io

from config import *
from utils import *

# Read in most recent file
list_of_files = [
    file
    for file in glob.glob("src/data/Results/*")
    if "~" not in file and "xlsx" in file
]
latest_file = max(list_of_files, key=os.path.getctime)
df = pd.read_excel(latest_file)

# Create numeric-only versions of data columns
for column in bar_chart_data_columns + pie_chart_data_columns:

    df[f"Numeric: {column}"] = df[column].apply(lambda x: handling_bad_numbers(x))

# Group dates to weeks
df["Week ending"] = (
    df["Completion time"].apply(lambda x: round_to_end_of_week(x)).dt.floor("D")
)
most_recent_week = df["Week ending"].max()

# Match with whether or not they're are a developer
df_roles = pd.read_csv("src/data/Reference/Roles.csv")
df = pd.merge(df, df_roles, on="Name")
df = df.fillna({"Role": "Developer"})

# Send email for people who wish to discuss their workload
discuss_workload = df.loc[
    (df["Week ending"] == most_recent_week)
    & (
        df["Would you like to discuss your current workload with Will or Hansa?"]
        == "Yes"
    ),
    "Name",
].to_list()
if len(discuss_workload) > 0:
    sent_from = gmail_user
    to = send_workload_flags_to
    subject = "TEST - DI Weekly Survey: People flagging workload"
    body = """\
    Hi Hansa and Will,

    The following people would like to discuss their workload with you:
    - %s

    Have a nice week!
    """ % (
        "\n - ".join(discuss_workload)
    )

    email_text = """\
    From: %s
    To: %s
    Subject: %s

    %s
    """ % (
        sent_from,
        ", ".join(to),
        subject,
        body,
    )

    try:
        smtp_server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        smtp_server.ehlo()
        smtp_server.login(gmail_user, gmail_password)
        smtp_server.sendmail(sent_from, to, email_text)
        smtp_server.close()
        print("Email sent successfully!")
    except Exception as ex:
        print("Something went wrong….", ex)

# Setting up the dash app
app = Dash()

question_dropdown = dcc.Dropdown(
    options=bar_chart_data_columns + pie_chart_data_columns + picture_data_columns,
    value=bar_chart_data_columns[0],
)

app.layout = html.Div(
    children=[
        html.H1(children="DI Team Dashboard"),
        question_dropdown,
        html.Div(
            [
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
    if selected_metric in bar_chart_data_columns:
        last_week = (
            df.loc[df["Week ending"] == most_recent_week]
            .groupby([f"Numeric: {selected_metric}", "Role"])[
                f"Numeric: {selected_metric}"
            ]
            .count()
        )
        last_week = last_week.rename("number_of_people").reset_index()

        fig = px.bar(
            last_week,
            x=f"Numeric: {selected_metric}",
            y="number_of_people",
            color="Role",
            color_discrete_sequence=discrete_colours,
            title="This week:",
            labels={
                f"Numeric: {selected_metric}": axis_labels[selected_metric],
                "number_of_people": "Number of people",
            },
        )
        fig.update_layout(yaxis=dict(tickmode="linear", tick0=0, dtick=1))

    elif selected_metric in pie_chart_data_columns:
        last_week = (
            df.loc[
                df["Week ending"] == most_recent_week,
                [selected_metric, f"Numeric: {selected_metric}"],
            ]
            .value_counts()
            .rename("counts")
        )
        last_week = pd.DataFrame(last_week).reset_index()
        last_week = last_week.sort_values(by=f"Numeric: {selected_metric}")

        fig = px.pie(
            last_week,
            values="counts",
            names=selected_metric,
            color_discrete_sequence=[
                "#19D3F3",
                "#FF6692",
                "#00CC96",
                "#AB63FA",
                "#636EFA",
                "#B6E880",
                "#FF97FF",
                "#FECB52",
            ],
            title="This week:",
        )
        fig.update_traces(sort=False)

    elif selected_metric in picture_data_columns:
        last_week = (
            df.loc[
                df["Week ending"] == most_recent_week,
                ["Fun question"],
            ]
            .value_counts()
            .rename("counts")
        )
        results = {key[0]: value for key, value in last_week.to_dict().items()}
        if len(results) > 0:
            if results["Dogs"] > results["Cats"]:
                get_dog()
            elif results["Dogs"] < results["Cats"]:
                get_cat()
            else:
                choose_randomly()
        else:
            choose_randomly()

        img = io.imread(animal_file_path)
        fig = px.imshow(img)
        fig.update_layout(coloraxis_showscale=False)
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)

    else:
        img = np.zeros([100, 100, 3], dtype=np.uint8)
        img.fill(255)
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
    if selected_metric in bar_chart_data_columns:
        over_time = df.groupby(["Week ending", "Role"])[
            f"Numeric: {selected_metric}"
        ].mean()
        over_time = over_time.rename("average").reset_index()

        fig = px.line(
            over_time,
            x="Week ending",
            y="average",
            color="Role",
            color_discrete_sequence=discrete_colours,
            title="Over time:",
            labels={
                "Week ending": "Week ending",
                "average": f"Average {axis_labels[selected_metric].lower()}",
            },
        )
        fig.update_xaxes(tick0="2022-07-08", dtick=604800000, tickformat="%-d %B")

    elif selected_metric in pie_chart_data_columns:
        over_time = df.groupby(["Week ending"])[f"Numeric: {selected_metric}"].mean()
        over_time = over_time.rename("average").reset_index()

        fig = px.line(
            over_time,
            x="Week ending",
            y="average",
            color_discrete_sequence=discrete_colours,
            title="Over time:",
            labels={
                "Week ending": "Week ending",
                "average": f"Average {axis_labels[selected_metric].lower()}",
            },
        )
        fig.update_xaxes(tick0="2022-07-08", dtick=604800000, tickformat="%-d %B")

    else:
        img = np.zeros([100, 100, 3], dtype=np.uint8)
        img.fill(255)
        fig = px.imshow(img)
        fig.update_layout(coloraxis_showscale=False)
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
