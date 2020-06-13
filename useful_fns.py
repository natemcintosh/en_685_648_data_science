import pandas as pd
import numpy as np


def cond_prob(df: pd.DataFrame, A: str, B: str) -> pd.DataFrame:
    N = len(df)

    # Calculate the joint probabilities, P(age, agi)
    joint_probs = (
        df.groupby(A)[B]  # for each A group, do the following: grab the B column
        .value_counts()  # count the number of values of each unique age in that AGI bin
        .unstack(A)  # move AGI from the index to be the columns
        .fillna(0.0)  # fill NaN with 0.0
        .div(N)  # divide by population size
    )

    p_B = np.sum(joint_probs.values, axis=1).reshape((-1, 1))
    return joint_probs / p_B


def plot_cond_prob(p_A_given_B: pd.DataFrame):
    # Get the name of the index column
    B = p_A_given_B.index.name

    # If the B column is numeric
    if p_A_given_B.index.is_numeric():
        return p_A_given_B.reset_index().plot.area(x=B, figsize=(15, 10))
    # If categorical or string
    elif p_A_given_B.index.is_object() | p_A_given_B.index.is_categorical():
        # What is the name of the A column?
        temp = p_A_given_B.stack().rename("prob").reset_index()
        A_name = np.setdiff1d(temp.columns, [B, "prob"])[0]

        # Create the plot
        return (
            p_A_given_B.stack()
            .rename("prob")
            .unstack(A_name)
            .plot.barh(figsize=(15, 10), stacked=True)
        )
