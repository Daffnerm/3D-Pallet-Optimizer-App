import streamlit as st
import pandas as pd
from rectpack import newPacker
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm

# Fixed pallet dimensions
PALLET_LENGTH = 48
PALLET_WIDTH = 40

st.title("Advanced Pallet Optimizer")

# User inputs (all integer-only)
col1, col2 = st.columns(2)
with col1:
    carton_length = st.number_input("Carton Length (inches)", 
                                  min_value=1, step=1, format="%d", value=17)
    carton_width = st.number_input("Carton Width (inches)", 
                                 min_value=1, step=1, format="%d", value=13)
with col2:
    carton_height = st.number_input("Carton Height (inches)", 
                                  min_value=1, step=1, format="%d", value=10)
    max_height = st.number_input("Pallet Max Height (inches)", 
                               min_value=1, step=1, format="%d", 
                               value=72)

def calculate_capacity(l, w, h, max_h):
    # Special case for 17×13/13×17 cartons
    if (l == 17 and w == 13) or (l == 13 and w == 17):
        return 8, False
    
    # Theoretical maximum for uniform orientations
    orient1 = (PALLET_LENGTH // l) * (PALLET_WIDTH // w)
    orient2 = (PALLET_LENGTH // w) * (PALLET_WIDTH // l)
    theoretical_max = max(orient1, orient2)
    
    # Mixed-orientation attempt with rectpack
    packer = newPacker()
    packer.add_bin(PALLET_LENGTH, PALLET_WIDTH)
    
    for _ in range(1000):
        packer.add_rect(l, w)
        packer.add_rect(w, l)
    
    packer.pack()
    rectpack_result = len(packer[0]) if packer else 0
    
    # Choose best result
    cartons_per_layer = max(theoretical_max, rectpack_result)
    use_original = orient1 >= orient2 if cartons_per_layer == theoretical_max else False
    
    return cartons_per_layer, use_original

if carton_height > max_height:
    st.error("Carton height exceeds maximum pallet height!")
else:
    cartons_per_layer, use_original = calculate_capacity(
        carton_length, carton_width, carton_height, max_height
    )
    max_layers = max_height // carton_height
    total_cartons = cartons_per_layer * max_layers

    # Create side by side layout for visualizations
    vis_col1, vis_col2 = st.columns(2)
    
    with vis_col1:
        # 2D Visualization
        fig_2d, ax = plt.subplots(figsize=(6, 6))
        ax.set_title(f"Pallet Layer: {cartons_per_layer} Cartons (Max Height: {max_height}\")")
        ax.set_xlim(0, PALLET_LENGTH)
        ax.set_ylim(0, PALLET_WIDTH)
        ax.set_aspect('equal')

        # Draw pallet border
        pallet_border = plt.Rectangle((0, 0), PALLET_LENGTH, PALLET_WIDTH, 
                                  fill=False, edgecolor='black', linewidth=2)
        ax.add_patch(pallet_border)

        # Generate positions for the cartons (for both 2D and 3D)
        positions = []
        
        if cartons_per_layer > 0:
            # Special visualization for 17×13 cartons
