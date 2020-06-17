from typing import *
import os

import bs4
import pandas as pd


def main(html_file: str, sql_file: str, sql_table_name: str) -> None:
    # Check files exist
    assert os.path.isfile(html_file), f"Could not find {html_file}"
    assert os.path.isfile(sql_file), f"Could not find {sql_file}"

    # Read in all the tables that can be found in the html file
    all_tables = pd.read_html(html_file)

    # Filter down to just those that are 'hurricane tables'
    tables = [t for t in all_tables if is_hurricane_table(t)]

    # Combine tables
    hurricane_table = combine_hurricane_tables(tables)

    # Populate database


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
    cols_of_interest = list(replacements.values())
    tables_subset = [t[cols_of_interest] for t in tables] #THE COLS OF INTEREST AREN'T ALWAYS IN THE TABLE, HAVE TO CREATE DEFAULTS FOR THEM

    # Concatenate it all together
    T = pd.concat(tables_subset)

    return T


# def main(html_file: str) -> None:
#     # Read in the html file
#     with open("hurricanes.html") as f:
#         content = f.read()

#     # Parse with bs4
#     soup = bs4.BeautifulSoup(content)

#     # Get the hurricane tables out (still in HTML form)
#     html_tables = get_html_hurricane_tables(soup)

#     # Convert from html tables to a pandas dataframes

#     # Populate the table in the database


# def get_html_hurricane_tables(soup: bs4.BeautifulSoup) -> List[bs4.element.Tag]:
#     """
#     get_html_hurricane_tables() will search for all HTML tables, and return them only
#     if they pass the is_hurricane_table() predicate test
#     """
#     return [t for t in soup.find_all("table") if is_hurricane_table(t)]


# def is_hurricane_table(table: bs4.element.Tag) -> bool:
#     """
#     is_hurricane_table() looks for the following headers in a table, and return true if
#     it finds them
#     - year
#     - number of tropical storms
#     - number of hurricanes
#     - number of major hurricanes
#     - deaths
#     Having investigated all 18 hurricane tables, these column headers appear in all 18
#     """
#     # Get the headers
#     headers = get_table_headers(table)

#     # Remove all whitespace and lowercase everything. Also put it in a set for faster
#     # lookup
#     normalized_headers = {h.replace(" ", "").lower() for h in headers}

#     # Create the required cases and normalize them
#     required_headers = [
#         "Year",
#         "Map",
#         "Number ofhurricanes",
#         "Number ofmajor hurricanes",
#         "Deaths",
#     ]
#     required_headers = [h.replace(" ", "").lower() for h in required_headers]

#     # Check if all the required cases are in the normalized_headers
#     return all(h in normalized_headers for h in required_headers)


# def get_table_headers(table: bs4.element.Tag) -> List[str]:
#     """
#     get_table_headers() for a given HTML table, this will search for the headers, and
#     return them as stripped text
#     """
#     # Get the headers from the table
#     headers_tags = table.find_all("th")

#     # Get the text and strip it
#     return [h.text.strip() for h in headers_tags]
