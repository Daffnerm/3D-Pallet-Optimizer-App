import streamlit as st
import pandas as pd
from rectpack import newPacker
import matplotlib.pyplot as plt

# Fixed pallet dimensions
PALLET_LENGTH = 48
PALLET_WIDTH = 40

st.title("Advanced Pallet Optimizer")

# User inputs (all integer-only)
col1, col2 = st.columns(2)
with col1:
    carton_length = st.number_input("Carton Length (inches)", 
                                   min_value=1, step=1, format="%d")
    carton_width = st.number_input("Carton Width (inches)", 
                                  min_value=1, step=1, format="%d")
with col2:
    carton_height = st.number_input("Carton Height (inches)", 
                                   min_value=1, step=1, format="%d")
    max_height = st.number_input("Pallet Max Height (inches)", 
                               min_value=1, step=1, format="%d", 
                               value=59)  # Default to 59"

def calculate_capacity(l, w, h, max_h):
    # Special case for 17×13/13×17 cartons
    if (l == 17 and w == 13) or (l == 13 and w == 17):
        return 8, False
    
    # Theoretical maximum for uniform orientations
    orient1 =
