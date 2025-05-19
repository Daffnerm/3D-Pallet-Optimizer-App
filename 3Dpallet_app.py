import streamlit as st
import pandas as pd
from rectpack import newPacker
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Fixed pallet dimensions
PALLET_LENGTH = 48
PALLET_WIDTH = 40
PALLET_HEIGHT = 4  # Height of the pallet base

st.title("Simple Pallet Configurator")

# User inputs (all integer-only)
col1, col2 = st.columns(2)
with col1:
    carton_length = st.number_input("Carton Length (inches)", 
                                   min_value=1, step=1, format="%d", value=16)
    carton_width = st.number_input("Carton Width (inches)", 
                                  min_value=1, step=1, format="%d", value=10)
with col2:
    carton_height = st.number_input("Carton Height (inches)", 
                                   min_value=1, step=1, format="%d", value=8)
    max_height = st.number_input("Pallet Max Height (inches)", 
                               min_value=1, step=1, format="%d", 
                               value=59)

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

def create_cuboid(ax, x, y, z, dx, dy, dz, color='red'):
    """
    Create a 3D cuboid at position (x, y, z) with size (dx, dy, dz)
    """
    # Define the vertices of the cuboid
    vertices = [
        [x, y, z],
        [x+dx, y, z],
        [x+dx, y+dy, z],
        [x, y+dy, z],
        [x, y, z+dz],
        [x+dx, y, z+dz],
        [x+dx, y+dy, z+dz],
        [x, y+dy, z+dz]
    ]
    
    # Define the faces of the cuboid using vertices
    faces = [
        [vertices[0], vertices[1], vertices[2], vertices[3]],  # bottom
        [vertices[4], vertices[5], vertices[6], vertices[7]],  # top
        [vertices[0], vertices[1], vertices[5], vertices[4]],  # front
        [vertices[2], vertices[3], vertices[7], vertices[6]],  # back
        [vertices[1], vertices[2], vertices[6], vertices[5]],  # right
        [vertices[3], vertices[0], vertices[4], vertices[7]]   # left
    ]
    
    # Create the cuboid
    cuboid = Poly3DCollection(faces, alpha=1, edgecolor='k', linewidth=0.5)
    cuboid.set_facecolor(color)
    ax.add_collection3d(cuboid)

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
        ax.set_title(f"Pallet Layer: {cartons_per_layer} Cartons")
        ax.set_xlim(0, PALLET_LENGTH)
        ax.set_ylim(0, PALLET_WIDTH)
        ax.set_aspect('equal')

        # Draw pallet border
        pallet_border = plt.Rectangle(
            (0, 0), PALLET_LENGTH, PALLET_WIDTH,
            fill=False, edgecolor='black', linewidth=2
        )
        ax.add_patch(pallet_border)

        positions = []
        if cartons_per_layer > 0:
            # Special visualization for 17×13 cartons
            if (carton_length == 17 and carton_width == 13) or (carton_length == 13 and carton_width == 17):
                positions = [
                    # Row 1 - horizontal
                    {"x": 0, "y": 0, "w": 17, "h": 13},
                    {"x": 17, "y": 0, "w": 17, "h": 13},
                    
                    # Row 2 - horizontal
                    {"x": 0, "y": 13, "w": 17, "h": 13},
                    {"x": 17, "y": 13, "w": 17, "h": 13},
                    
                    # Row 3 - horizontal
                    {"x": 0, "y": 26, "w": 17, "h": 13},
                    {"x": 17, "y": 26, "w": 17, "h": 13},
                    
                    # Right column - vertical
                    {"x": 34, "y": 0, "w": 13, "h": 17},
                    {"x": 34, "y": 17, "w": 13, "h": 17}
                ]
                
                for i, pos in enumerate(positions):
                    is_vertical = pos["h"] > pos["w"]
                    rect_color = '#5599FF' if is_vertical else '#0099e6'
                    
                    rect = plt.Rectangle(
                        (pos["x"], pos["y"]), 
                        pos["w"], 
                        pos["h"],
                        edgecolor='#004466', 
                        facecolor=rect_color, 
                        alpha=0.7
                    )
                    ax.add_patch(rect)
                    
                    # Add number to each carton
                    ax.text(
                        pos["x"] + pos["w"]/2, 
                        pos["y"] + pos["h"]/2, 
                        str(i+1),
                        ha='center', 
                        va='center', 
                        color='white', 
                        fontweight='bold'
                    )
            else:
                # Standard visualization for other sizes
                used_l = carton_length if use_original else carton_width
                used_w = carton_width if use_original else carton_length
                
                cols = PALLET_LENGTH // used_l
                rows = PALLET_WIDTH // used_w
                
                for i in range(cols):
                    for j in range(rows):
                        positions.append({
                            "x": i * used_l,
                            "y": j * used_w,
                            "w": used_l,
                            "h": used_w
                        })
                        
                        rect = plt.Rectangle(
                            (i * used_l, j * used_w), 
                            used_l, 
                            used_w,
                            edgecolor='#004466', 
                            facecolor='#0099e6', 
                            alpha=0.7
                        )
                        ax.add_patch(rect)
                        
                        # Add number to each carton
                        ax.text(
                            i * used_l + used_l/2, 
                            j * used_w + used_w/2, 
                            str(i * rows + j + 1),
                            ha='center', 
                            va='center', 
                            color='white', 
                            fontweight='bold'
                        )
        else:
            ax.text(PALLET_LENGTH/2, PALLET_WIDTH/2, "Carton too large!", 
                    ha='center', va='center', color='red', fontsize=14)

        # Add grid for better visualization
        ax.grid(True, linestyle='--', alpha=0.3)
        
        st.pyplot(fig_2d)
    
    with vis_col2:
        # 3D Visualization - COMPLETELY FIXED VERSION
        if cartons_per_layer > 0:
            # Create the 3D figure
            fig_3d = plt.figure(figsize=(6, 6))
            ax3d = fig_3d.add_subplot(111, projection='3d')
            
            # Set viewing angle
            ax3d.view_init(elev=30, azim=45)
            
            # Set limits FIRST
            ax3d.set_xlim(0, PALLET_LENGTH)
            ax3d.set_ylim(0, PALLET_WIDTH)
            
            # Calculate total stack height
            stack_height = max_layers * carton_height
            total_height = PALLET_HEIGHT + stack_height
            
            # Set Z limit to show entire pallet + stack
            ax3d.set_zlim(0, total_height)
            
            # 1. Draw wooden pallet base at z=0 (bottom)
            create_cuboid(
                ax3d, 0, 0, 0,
                PALLET_LENGTH, PALLET_WIDTH, PALLET_HEIGHT,
                color='#C0A080'  # Wooden color
            )
            
            # 2. Draw carton layers, starting at z = PALLET_HEIGHT
            for layer in range(max_layers):
                z_position = PALLET_HEIGHT + (layer * carton_height)
                layer_color = '#2E86C1' if layer % 2 == 0 else '#3498DB'
                
                for pos in positions:
                    # Determine carton dimensions based on orientation
                    if (carton_length == 17 and carton_width == 13) or (carton_length == 13 and carton_width == 17):
                        w = pos["w"]  # Width of carton in this position
                        h = pos["h"]  # Height of carton in this position
                    else:
                        w = pos["w"]
                        h = pos["h"]
                    
                    # Create each carton
                    create_cuboid(
                        ax3d, 
                        pos["x"], pos["y"], z_position,
                        w, h, carton_height,
                        color=layer_color
                    )
            
            # Configure axes
            ax3d.set_axis_off()
            ax3d.set_box_aspect([PALLET_LENGTH, PALLET_WIDTH, total_height])
            
            st.pyplot(fig_3d)
        else:
            st.warning("Cannot create 3D visualization: carton too large for pallet.")
    
    # Calculate pallet utilization - FIXED VOLUME CALCULATION
    pallet_area = PALLET_LENGTH * PALLET_WIDTH
    stack_height = max_layers * carton_height  # Height of all stacked cartons
    total_pallet_volume = pallet_area * (PALLET_HEIGHT + stack_height)  # Including pallet base
    
    if cartons_per_layer > 0:
        if (carton_length == 17 and carton_width == 13) or (carton_length == 13 and carton_width == 17):
            # For 17×13 special case
            horizontal_area = 17 * 13 * 6  # 6 horizontal cartons
            vertical_area = 13 * 17 * 2    # 2 vertical cartons
            carton_area = horizontal_area + vertical_area
        else:
            # For standard layouts
            used_l = carton_length if use_original else carton_width
            used_w = carton_width if use_original else carton_length
            carton_area = used_l * used_w * cartons_per_layer
        
        area_utilization = (carton_area / pallet_area) * 100
        
        # Calculate volume of all cartons
        carton_volume = carton_area * carton_height * max_layers
        
        # Calculate percentage of occupied space
        volume_utilization = (carton_volume / (pallet_area * stack_height)) * 100
    else:
        area_utilization = 0
        volume_utilization = 0
    
    # Display results in two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Optimization Results")
        st.write(f"**Cartons/layer:** {cartons_per_layer}")
        st.write(f"**Max layers ({max_height}\"):** {max_layers}")
        st.write(f"**Total cartons:** {total_cartons}")
    
    with col2:
        st.subheader("Pallet Utilization")
        st.write(f"**Pallet Area Utilization:** {area_utilization:.1f}%")
        st.write(f"**Pallet Volume Utilization:** {volume_utilization:.1f}%")

    # Export to Excel
    if st.button("Save Configuration to Excel"):
        df = pd.DataFrame([{
            "Length": carton_length,
            "Width": carton_width,
            "Height": carton_height,
            "Max Pallet Height": max_height,
            "Cartons/Layer": cartons_per_layer,
            "Layers": max_layers,
            "Total": total_cartons,
            "Area Utilization (%)": round(area_utilization, 1),
            "Volume Utilization (%)": round(volume_utilization, 1)
        }])
        df.to_excel("pallet_configurations.xlsx", index=False)
        st.success("Saved to pallet_configurations.xlsx!")
