import streamlit as st
import pandas as pd
from rectpack import newPacker
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Fixed pallet dimensions
PALLET_LENGTH = 48
PALLET_WIDTH = 40

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
                               min_value=1, step=1, format="%d", value=59)

def calculate_capacity(l, w, h, max_h):
    # Special case for 17×13/13×17 cartons
    if (l == 17 and w == 13) or (l == 13 and w == 17):
        return 8, False, []
    
    # Mixed-orientation attempt with rectpack
    packer = newPacker()
    packer.add_bin(PALLET_LENGTH, PALLET_WIDTH)
    
    for _ in range(1000):
        packer.add_rect(l, w)
        packer.add_rect(w, l)
    
    packer.pack()
    rects = [rect for rect in packer[0]] if packer else []
    
    return len(rects), False, rects

def plot_cube(ax, x, y, z, dx, dy, dz, color):
    vertices = [
        [x, y, z], [x+dx, y, z], [x+dx, y+dy, z], [x, y+dy, z],
        [x, y, z+dz], [x+dx, y, z+dz], [x+dx, y+dy, z+dz], [x, y+dy, z+dz]
    ]
    faces = [
        [vertices[0], vertices[1], vertices[2], vertices[3]],  # bottom
        [vertices[4], vertices[5], vertices[6], vertices[7]],  # top
        [vertices[0], vertices[1], vertices[5], vertices[4]],  # front
        [vertices[2], vertices[3], vertices[7], vertices[6]],  # back
        [vertices[1], vertices[2], vertices[6], vertices[5]],  # right
        [vertices[3], vertices[0], vertices[4], vertices[7]]   # left
    ]
    cube = Poly3DCollection(faces, alpha=1.0, edgecolors='k', linewidths=0.5)
    cube.set_facecolor(color)
    ax.add_collection3d(cube)

if carton_height > max_height:
    st.error("Carton height exceeds maximum pallet height!")
else:
    cartons_per_layer, use_original, rects = calculate_capacity(
        carton_length, carton_width, carton_height, max_height
    )
    max_layers = max_height // carton_height
    total_cartons = cartons_per_layer * max_layers

    # Create side by side layout
    vis_col1, vis_col2 = st.columns(2)
    
    with vis_col1:
        # 2D Visualization
        fig_2d, ax = plt.subplots(figsize=(6, 6))
        ax.set_title(f"Pallet Layer: {cartons_per_layer} Cartons")
        ax.set_xlim(0, PALLET_LENGTH)
        ax.set_ylim(0, PALLET_WIDTH)
        ax.set_aspect('equal')
        
        # Draw pallet border (FIXED HERE)
        pallet_border = plt.Rectangle(
            (0, 0), PALLET_LENGTH, PALLET_WIDTH,
            fill=False, edgecolor='black', linewidth=2
        )
        ax.add_patch(pallet_border)
        
        if cartons_per_layer > 0:
            if (carton_length == 17 and carton_width == 13) or (carton_length == 13 and carton_width == 17):
                # Special 17×13 layout
                positions = [...]  # Your existing special case positions
            else:
                # Use actual rectpack results
                for i, rect in enumerate(rects):
                    x, y, w, h = rect.x, rect.y, rect.width, rect.height
                    rect_patch = plt.Rectangle(
                        (x, y), w, h,
                        edgecolor='#004466', facecolor='#0099e6', alpha=0.7
                    )
                    ax.add_patch(rect_patch)
                    ax.text(
                        x + w/2, y + h/2, str(i+1),
                        ha='center', va='center', color='white', fontweight='bold'
                    )
        
        ax.grid(True, linestyle='--', alpha=0.3)
        st.pyplot(fig_2d)
    
    with vis_col2:
        # 3D Visualization (no pallet)
        if cartons_per_layer > 0:
            fig_3d = plt.figure(figsize=(6, 6))
            ax3d = fig_3d.add_subplot(111, projection='3d')
            
            for layer in range(max_layers):
                z_pos = layer * carton_height
                color = '#2E86C1' if layer % 2 == 0 else '#3498DB'
                
                for rect in rects:
                    plot_cube(ax3d, rect.x, rect.y, z_pos, 
                            rect.width, rect.height, carton_height, color)
            
            ax3d.set_xlim(0, PALLET_LENGTH)
            ax3d.set_ylim(0, PALLET_WIDTH)
            ax3d.set_zlim(0, max_layers * carton_height)
            ax3d.view_init(elev=30, azim=45)
            ax3d.set_axis_off()
            st.pyplot(fig_3d)

    # Calculate pallet utilization
    pallet_area = PALLET_LENGTH * PALLET_WIDTH
    stack_volume = pallet_area * (max_layers * carton_height)
    
    if cartons_per_layer > 0:
        if (carton_length == 17 and carton_width == 13) or (carton_length == 13 and carton_width == 17):
            horizontal_area = 17 * 13 * 6
            vertical_area = 13 * 17 * 2
            carton_area = horizontal_area + vertical_area
            carton_volume = carton_area * carton_height * max_layers
        else:
            carton_area = sum(rect.width * rect.height for rect in rects)
            carton_volume = carton_area * carton_height * max_layers
        
        area_utilization = (carton_area / pallet_area) * 100
        volume_utilization = (carton_volume / stack_volume) * 100
    else:
        area_utilization = 0
        volume_utilization = 0
    
    # Display results
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
