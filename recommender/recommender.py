import pandas as pd
from scipy.spatial.distance import cosine
import numpy as np

data = pd.read_csv('data/track2users1.csv', index_col='track')
data = data.transpose()

def signup(username):
    pass

def like(username, track):
    pass

def recommend(username):
    pass

