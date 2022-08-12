import re
from datetime import timedelta, datetime
import pandas as pd
import plotly.express as px

import dog
import numpy as np
import requests
import random
import smtplib
import glob
import os
from skimage import io

from config import (
    cat_url,
    animal_file_path,
    animal_directory,
    animal_file_name,
    gmail_user,
    send_workload_flags_to,
    gmail_password,
    discrete_colours,
    axis_labels,
)


def read_most_recent_file(folder: str) -> pd.DataFrame:
    """
    Takes folder and reads the most recent file in the folder

    Args:
        folder (str): path to folder

    Returns:
        pd.DataFrame: most recent file as pandas DataFrame
    """
    list_of_files = [
        file for file in glob.glob(folder) if "~" not in file and "xlsx" in file
    ]
    latest_file = max(list_of_files, key=os.path.getctime)
    df = pd.read_excel(latest_file)
    return df


def create_numeric_columns(
    df: pd.DataFrame, list_of_columns: list[str]
) -> pd.DataFrame:
    """
    Creates additional columns with numeric contents only

    Args:
        df (pd.DataFrame): raw data
        list_of_columns (list[str]): list of columns to create numeric columns for

    Returns:
        pd.DataFrame: original DataFrame with additional numeric columns
    """
    for column in list_of_columns:
        df[f"Numeric: {column}"] = df[column].apply(lambda x: handling_bad_numbers(x))

    return df


def round_to_end_of_week(input_date: datetime) -> datetime:
    """
    Rounds survey completion date to the closest end of week date.
    Days up to Tuesday are rounded back to past Friday, days from
    Wednesday on are rounded forward to next Friday.

    Args:
        input_date (datetime): date and time the survey was completed

    Returns
        datetime: end of week date
    """
    day_of_week = input_date.weekday()
    if day_of_week < 2:
        return input_date - timedelta(days=(3 + day_of_week))
    else:
        return input_date - timedelta(days=(day_of_week - 4))


def handling_bad_numbers(data_entry: str) -> int:
    """
    Attempts to convert non-integer entries to integers

    Args:
        data_entry (string): Entry in survey form, hopefully an integer

    Returns:
        int: integer value
    """

    try:
        return int(data_entry)
    except ValueError:
        all_numbers = [x for x in re.split("\W+", str(data_entry)) if x]
        return int(all_numbers[0])


def get_cat():
    """
    Retrieves cat image from Cat as a service and saves to file.
    """
    response = requests.get(cat_url)

    with open(animal_file_path, "wb") as f:
        f.write(response.content)


def get_dog():
    """
    Retrieves dog image from the random dog API and saves to file.
    """
    dog.getDog(directory=animal_directory, filename=animal_file_name)


def choose_randomly():
    """
    Randomly chooses dogs or cats
    """
    if random.random() <= 0.5:
        get_dog()
    else:
        get_cat()


def send_email(discuss_workload):
    """
    Uses smtp to send an email to Will and Hansa if anyone has flagged
    wanting to discuss their workload.

    Args:
        discuss_workload (List(str)): List of people who answered yes
    """
    if len(discuss_workload) > 0:
        body = """\
        Hi Hansa and Will,

        The following people would like to discuss their workload with you:
        - %s

        Have a nice week!
        """ % (
            "\n - ".join(discuss_workload)
        )
    else:
        body = """\
        Hi Hansa and Will,

        No one wants to discuss their workload this week :)

        Have a nice week!
        """

    sent_from = gmail_user
    to = send_workload_flags_to
    subject = "TEST - DI Weekly Survey: People flagging workload"

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
        smtp_server.quit()
        print("Email sent successfully!")
    except Exception as ex:
        print("Something went wrong….", ex)


def create_bar_chart(df: pd.DataFrame, metric: str, most_recent_week: datetime):
    """
    Takes Dataframe and creates bar chart of selected column for the most recent week

    Args:
        df (pd.DataFrame): DataFrame with data
        metric (str): name of column for metric
        most_recent_week (datetime): date of most recent week

    Returns:
        plotly figure
    """

    last_week = (
        df.loc[df["Week ending"] == most_recent_week]
        .groupby([f"Numeric: {metric}", "Role"])[f"Numeric: {metric}"]
        .count()
    )
    last_week = last_week.rename("number_of_people").reset_index()

    fig = px.bar(
        last_week,
        x=f"Numeric: {metric}",
        y="number_of_people",
        color="Role",
        color_discrete_sequence=discrete_colours,
        title="This week:",
        labels={
            f"Numeric: {metric}": axis_labels[metric],
            "number_of_people": "Number of people",
        },
    )
    return fig


def create_pie_chart(df: pd.DataFrame, metric: str, most_recent_week: str):
    """
    Takes Dataframe and creates bar chart of selected column for most recent week

    Args:
        df (pd.DataFrame): DataFrame with data
        metric (str): name of column for metric
        most_recent_week (datetime): date of most recent week

    Returns:
        plotly figure
    """
    last_week = (
        df.loc[
            df["Week ending"] == most_recent_week,
            [metric, f"Numeric: {metric}"],
        ]
        .value_counts()
        .rename("counts")
    )
    last_week = pd.DataFrame(last_week).reset_index()
    last_week = last_week.sort_values(by=f"Numeric: {metric}")

    fig = px.pie(
        last_week,
        values="counts",
        names=metric,
        color_discrete_sequence=discrete_colours,
        title="This week:",
    )
    fig.update_traces(sort=False)

    return fig


def get_animal_picture(df: pd.DataFrame, most_recent_week: datetime):
    """
    Returns animal picture based on voting for most recent week.
    Chooses randomly in case of tie.

    Args:
        df (pd.DataFrame): DataFrame of survey results
        most_recent_week (datetime): date of most recent week

    Returns:
        plotly figure
    """
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
        if "Dogs" not in results:
            get_cat()
        elif "Cats" not in results:
            get_dog()
        elif results["Dogs"] > results["Cats"]:
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

    return fig


def create_time_series_chart(
    time_series_data: pd.DataFrame, metric: str, separate_roles: bool = False
):
    """
    Takes Dataframe and creates time series chart of metric.

    Args:
        df (pd.DataFrame): DataFrame with data
        metric (str): name of column for metric
        separate_roles (bool, optional): if True separate lines are
            plotted for each role type. Defaults to False.

    Returns:
        plotly figure
    """
    if separate_roles:
        fig = px.line(
            time_series_data,
            x="Week ending",
            y="average",
            color="Role",
            color_discrete_sequence=discrete_colours,
            title="Over time:",
            labels={
                "Week ending": "Week ending",
                "average": f"Average {axis_labels[metric].lower()}",
            },
        )
    else:
        fig = px.line(
            time_series_data,
            x="Week ending",
            y="average",
            color_discrete_sequence=discrete_colours,
            title="Over time:",
            labels={
                "Week ending": "Week ending",
                "average": f"Average {axis_labels[metric].lower()}",
            },
        )
    fig.update_xaxes(tick0="2022-07-08", dtick=604800000, tickformat="%-d %B")
    return fig


def create_empty_image():
    """
    Creates a blank image

    Returns:
        plotly figure
    """
    img = np.zeros([100, 100, 3], dtype=np.uint8)
    img.fill(255)
    fig = px.imshow(img)
    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    return fig
