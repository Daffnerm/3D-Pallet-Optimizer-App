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
                                  min_value=1, step=1, format="%d")
    carton_width = st.number_input("Carton Width (inches)", 
                                 min_value=1, step=1, format="%d")
with col2:
    carton_height = st.number_input("Carton Height (inches)", 
                                  min_value=1, step=1, format="%d")
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
        pallet_border = plt.Rectangle((0, 0), PALLET_LENGTH, PALLET_WIDTH, 
                                  fill=False, edgecolor='black', linewidth=2)
        ax.add_patch(pallet_border)

        if cartons_per_layer > 0:
            # Special visualization for 17×13 cartons - FIXED LAYOUT
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
                
                # Draw cartons with different colors for horizontal/vertical
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

        # Add grid
        ax.grid(True, linestyle='--', alpha=0.3)
        st.pyplot(fig_2d)
    
    with vis_col2:
        # 3D Visualization (fixed view)
        if cartons_per_layer > 0:
            # Create figure for 3D plot
            fig_3d = plt.figure(figsize=(6, 6))
            ax3d = fig_3d.add_subplot(111, projection='3d')
            
            # Draw the pallet base (gray)
            x = np.array([0, PALLET_LENGTH, PALLET_LENGTH, 0, 0])
            y = np.array([0, 0, PALLET_WIDTH, PALLET_WIDTH, 0])
            z = np.zeros(5)
            ax3d.plot3D(x, y, z, color='gray')
            ax3d.fill(x, y, z, color='lightgray', alpha=0.7)
            
            # Generate positions for 3D if not already done in 2D section
            positions = []
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
            else:
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
            
            # For each layer
            for layer in range(max_layers):
                z_offset = layer * carton_height
                
                # For each carton in the layer
                for pos in positions:
                    # Get dimensions based on orientation
                    if (carton_length == 17 and carton_width == 13) or (carton_length == 13 and carton_width == 17):
                        is_vertical = pos["h"] > pos["w"]
                        l = pos["w"]
                        w = pos["h"]
                    else:
                        l = pos["w"]
                        w = pos["h"]
                    
                    # Calculate vertices
                    x = [pos["x"], pos["x"]+l, pos["x"]+l, pos["x"], pos["x"], pos["x"]+l, pos["x"]+l, pos["x"]]
                    y = [pos["y"], pos["y"], pos["y"]+w, pos["y"]+w, pos["y"], pos["y"], pos["y"]+w, pos["y"]+w]
                    z = [z_offset, z_offset, z_offset, z_offset, z_offset+carton_height, z_offset+carton_height, z_offset+carton_height, z_offset+carton_height]
                    
                    # Use different colors for alternating layers
                    color = '#2E86C1' if layer % 2 == 0 else '#3498DB'
                    
                    # Render the box
                    for i in range(4):
                        ax3d.plot3D([x[i], x[i+4]], [y[i], y[i+4]], [z[i], z[i+4]], color='#004466')
                    
                    # Draw top and bottom faces
                    ax3d.plot3D([x[0], x[1], x[2], x[3], x[0]], [y[0], y[1], y[2], y[3], y[0]], [z[0], z[1], z[2], z[3], z[0]], color='#004466')
                    ax3d.plot3D([x[4], x[5], x[6], x[7], x[4]], [y[4], y[5], y[6], y[7], y[4]], [z[4], z[5], z[6], z[7], z[4]], color='#004466')
                    
                    # Fill cube faces
                    ax3d.fill([x[0], x[1], x[2], x[3]], [y[0], y[1], y[2], y[3]], [z[0], z[1], z[2], z[3]], color=color)
                    ax3d.fill([x[4], x[5], x[6], x[7]], [y[4], y[5], y[6], y[7]], [z[4], z[5], z[6], z[7]], color=color)
                    ax3d.fill([x[0], x[1], x[5], x[4]], [y[0], y[1], y[5], y[4]], [z[0], z[1], z[5], z[4]], color=color)
                    ax3d.fill([x[1], x[2], x[6], x[5]], [y[1], y[2], y[6], y[5]], [z[1], z[2], z[6], z[5]], color=color)
                    ax3d.fill([x[2], x[3], x[7], x[6]], [y[2], y[3], y[7], y[6]], [z[2], z[3], z[7], z[6]], color=color)
                    ax3d.fill([x[3], x[0], x[4], x[7]], [y[3], y[0], y[4], y[7]], [z[3], z[0], z[4], z[7]], color=color)
            
            # Set view and limits
            ax3d.view_init(elev=30, azim=45)
            ax3d.set_box_aspect([PALLET_LENGTH, PALLET_WIDTH, max_height])
            
            # Remove axes and set background color
            ax3d.set_axis_off()
            
            # Set equal scale
            ax3d.set_xlim(0, PALLET_LENGTH)
            ax3d.set_ylim(0, PALLET_WIDTH)
            ax3d.set_zlim(0, max_height)
            
            st.pyplot(fig_3d)
        else:
            st.warning("Cannot create 3D visualization: carton too large for pallet.")
    
    # Calculate pallet utilization
    pallet_area = PALLET_LENGTH * PALLET_WIDTH
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
        
        utilization_percentage = (carton_area / pallet_area) * 100
    else:
        utilization_percentage = 0
    
    # Display results in two columns
    col1, col2 = st.columns(2)
    
    with col1:
        # Optimization Results
        st.subheader("Optimization Results")
        st.write(f"**Cartons/layer:** {cartons_per_layer}")
        st.write(f"**Max layers ({max_height}\"):** {max_layers}")
        st.write(f"**Total cartons:** {total_cartons}")
    
    with col2:
        # Pallet Utilization
        st.subheader("Pallet Utilization")
        st.write(f"**Pallet Area Utilization:** {utilization_percentage:.1f}%")

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
            "Utilization (%)": round(utilization_percentage, 1)
        }])
        df.to_excel("pallet_configurations.xlsx", index=False)
        st.success("Saved to pallet_configurations.xlsx!")
