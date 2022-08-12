import glob
import os

import pandas as pd

from utils import send_email, round_to_end_of_week

# Read in most recent file
list_of_files = [
    file
    for file in glob.glob("src/data/Results/*")
    if "~" not in file and "xlsx" in file
]
latest_file = max(list_of_files, key=os.path.getctime)
df = pd.read_excel(latest_file)

# Group dates to weeks
df["Week ending"] = (
    df["Completion time"].apply(lambda x: round_to_end_of_week(x)).dt.floor("D")
)
most_recent_week = df["Week ending"].max()

# Send email for people who wish to discuss their workload
discuss_workload = df.loc[
    (df["Week ending"] == most_recent_week)
    & (
        df["Would you like to discuss your current workload with Will or Hansa?"]
        == "Yes"
    ),
    "Name",
].to_list()
send_email(discuss_workload)
