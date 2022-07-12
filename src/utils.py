import re
from datetime import timedelta

import dog
import numpy as np
import requests
import random

from config import *


def round_to_end_of_week(input_date):
    """
    Rounds survey completion date to the closest end of week date.
    Days up to Tuesday are rounded back to past Friday, days from
    Wednesday on are rounded forward to next Friday.

    Args:
        input_date (Datetime): Date and time the survey was completed
    """
    day_of_week = input_date.weekday()
    if day_of_week < 2:
        return input_date - timedelta(days=(3 + day_of_week))
    else:
        return input_date - timedelta(days=(day_of_week - 4))


def handling_bad_numbers(data_entry):
    """
    Attempts to convert non-integer entries to integers

    Args:
        data_entry (string): Entry in survey form, hopefully an integer
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
    Retrieves dog image from the random dog API.
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
