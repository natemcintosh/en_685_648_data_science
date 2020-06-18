from typing import *
import os
import itertools as it
import unicodedata
import sqlite3

import bs4
import pandas as pd
import numpy as np


def main(html_file: str, sql_file: str, sql_table_name: str) -> None:
    # Check files exist
    assert os.path.isfile(html_file), f"Could not find HTML file '{html_file}''"
    assert os.path.isfile(sql_file), f"Could not find SQL database '{sql_file}'"

    # Read in all the tables that can be found in the html file
    all_tables = pd.read_html(html_file)

    # Filter down to just those that are 'hurricane tables'
    tables = [t for t in all_tables if is_hurricane_table(t)]

    # Combine tables
    hurricane_table_bad_cols = combine_hurricane_tables(tables)

    # Fix columns
    hurricane_table = fix_columns(hurricane_table_bad_cols)

    # Populate database
    conn = sqlite3.connect(sql_file)
    hurricane_table.to_sql(
        name=sql_table_name, con=conn, if_exists="replace", index=False
    )
    conn.close()


def is_hurricane_table(table: pd.DataFrame) -> bool:
    """
    is_hurricane_table() looks for the following headers in a table, and return true if
    it finds them
    - year
    - number of tropical storms
    - number of hurricanes
    - number of major hurricanes
    - deaths
    Having investigated all 18 hurricane tables, these column headers appear in all 18
    """
    # Get the column headers, remove all whitespace and lowercase everything. Also put
    # it in a set for faster lookup
    normalized_headers = {str(h).replace(" ", "").lower() for h in table.columns}

    # Create the required cases and normalize them
    required_headers = [
        "Year",
        "Map",
        "Number ofhurricanes",
        "Number ofmajor hurricanes",
        "Deaths",
    ]
    required_headers = [h.replace(" ", "").lower() for h in required_headers]

    # Check if all the required cases are in the normalized_headers
    return all(h in normalized_headers for h in required_headers)


def combine_hurricane_tables(tables: List[pd.DataFrame]) -> pd.DataFrame:
    """
    combine_hurricane_tables() strives to find common column headers, name them the
    same thing, and then merge those columns together
    """
    # Format all the headers the same way
    for t in tables:
        t.columns = [str(h).replace(" ", "").lower() for h in t.columns]

    # Create a dictionary of what to replace common headers with
    replacements = {
        "year": "year",
        "numberoftropicalstorms": "tropical_storms",
        "numberofhurricanes": "hurricanes",
        "numberofmajorhurricanes": "major_hurricanes",
        "deaths": "deaths",
        "damageusd": "damage",
        "notes": "notes",
    }

    # Replace all the names that can be
    for t in tables:
        t.rename(columns=replacements, inplace=True)

    # downselect the columns to just those of interest
    cols_of_interest = set(replacements.values())
    tables_subset = [t[set(t.columns).intersection(cols_of_interest)] for t in tables]

    # Concatenate it all together
    T = pd.concat(tables_subset).reset_index(drop=True)

    # Sort columns into nicer order
    T = T[list(replacements.values())]

    return T


def fix_columns(hurricane_table_bad_cols: pd.DataFrame) -> pd.DataFrame:
    """
    fix_columns() will attempt to coerce all of 7 the columns into proper form for the
    database
    """
    fixed_year = fix_year_col(hurricane_table_bad_cols)

    fixed_deaths = fix_deaths_col(fixed_year)

    fixed_damage = fix_damage_col(fixed_deaths)

    return fixed_damage


def fix_year_col(df: pd.DataFrame) -> pd.DataFrame:
    """Get year into an integer form. May have to remove rows of totals"""
    # To start, make sure everything is a string
    df.year = df.year.astype("str")

    # Downselect to only numerical columns
    df2 = df.drop(np.where(df.year.str.isalpha())[0])

    # Set year type to int
    df2.year = df2.year.astype("int")

    return df2.sort_values("year")


def fix_deaths_col(df: pd.DataFrame) -> pd.DataFrame:
    """Make the deaths column an integer"""
    # To start, make sure everything is a string, then remove ',' '~' '+'
    deaths = (
        df.deaths.astype("str")  # make everything a string
        .str.strip("~+, ")  # remove the following characters
        .str.replace("None", "0")  # replace 'none' with 0
    )

    # Replace anything that is not numeric with 'NaN'
    deaths.loc[deaths.str.isalpha()] = "NaN"

    # Make it numeric, and convert "NaN" to actual NaN
    deaths = pd.to_numeric(deaths, errors="coerce")

    df.deaths = deaths

    return df


def fix_damage_col(df: pd.DataFrame) -> pd.DataFrame:
    """Try to coerce this into a column of real numbers"""
    damage = (
        df.damage.astype("str")  # Make sure everything is a string
        .str.replace("million", "e6")  # Replace names with scientific notation
        .str.replace("billion", "e9")
        .apply(drop_up_to_dollar_inclusive)  # remove everything before and including $
        .apply(lambda x: unicodedata.normalize("NFKD", x))  # normalize to unicode
        .str.replace(" ", "")
        .str.replace("+", "")  # Remove +
    )

    damage = pd.to_numeric(damage, errors="coerce")

    df.damage = damage

    return df


def drop_up_to_dollar_inclusive(s: str) -> str:
    # Drop everything before the $
    including_dollar_sign = list(it.dropwhile(lambda char: char != "$", s))

    # if there is nothing left, return the original
    if len(including_dollar_sign) == 0:
        return s

    # If a $ is the first thing, drop it
    if including_dollar_sign[0] == "$":
        everything_else = including_dollar_sign[1:]

    return "".join(everything_else)
