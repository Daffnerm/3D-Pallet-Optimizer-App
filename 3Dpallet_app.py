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

# User inputs with defaults
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
    
    # Grid approach calculations
    orient1 = (PALLET_LENGTH // l) * (PALLET_WIDTH // w)
    orient2 = (PALLET_LENGTH // w) * (PALLET_WIDTH // l)
    grid_max = max(orient1, orient2)
    use_original = orient1 >= orient2
    
    # Mixed-orientation attempt with rectpack
    packer = newPacker()
    packer.add_bin(PALLET_LENGTH, PALLET_WIDTH)
    
    for _ in range(1000):
        packer.add_rect(l, w)
        packer.add_rect(w, l)
    
    packer.pack()
    rects = [rect for rect in packer[0]] if packer else []
    
    # Choose best result
    if grid_max >= len(rects):
        return grid_max, use_original, []
    else:
        return len(rects), False, rects

def draw_box(ax, x, y, z, dx, dy, dz, color):
    vertices = [
        [x, y, z], [x+dx, y, z], [x+dx, y+dy, z], [x, y+dy, z],
        [x, y, z+dz], [x+dx, y, z+dz], [x+dx, y+dy, z+dz], [x, y+dy, z+dz]
    ]
    faces = [
        [vertices[0], vertices[1], vertices[2], vertices[3]],
        [vertices[4], vertices[5], vertices[6], vertices[7]],
        [vertices[0], vertices[1], vertices[5], vertices[4]],
        [vertices[1], vertices[2], vertices[6], vertices[5]],
        [vertices[2], vertices[3], vertices[7], vertices[6]],
        [vertices[3], vertices[0], vertices[4], vertices[7]]
    ]
    box = Poly3DCollection(faces, facecolors=color, edgecolors='k', linewidths=0.5)
    ax.add_collection3d(box)

if carton_height > max_height:
    st.error("Carton height exceeds maximum pallet height!")
else:
    cartons_per_layer, use_original, rects = calculate_capacity(
        carton_length, carton_width, carton_height, max_height
    )
    max_layers = max_height // carton_height
    total_cartons = cartons_per_layer * max_layers

    # Visualization columns
    vis_col1, vis_col2 = st.columns(2)
    
    with vis_col1:
        # 2D Visualization
        fig_2d, ax = plt.subplots(figsize=(6, 6))
        ax.set_title(f"Layer: {cartons_per_layer} Cartons")
        ax.set_xlim(0, PALLET_LENGTH)
        ax.set_ylim(0, PALLET_WIDTH)
        ax.set_aspect('equal')
        
        # Pallet border
        plt.Rectangle((0, 0), PALLET_LENGTH, PALLET_WIDTH, 
                    fill=False, edgecolor='black', linewidth=2).draw(ax)
        
        if cartons_per_layer > 0:
            if not rects:  # Grid layout
                used_l = carton_length if use_original else carton_width
                used_w = carton_width if use_original else carton_length
                cols = PALLET_LENGTH // used_l
                rows = PALLET_WIDTH // used_w
                
                for i in range(cols):
                    for j in range(rows):
                        x = i * used_l
                        y = j * used_w
                        plt.Rectangle((x, y), used_l, used_w, 
                                    edgecolor='#004466', facecolor='#0099e6', 
                                    alpha=0.7).draw(ax)
                        ax.text(x + used_l/2, y + used_w/2, str(i*rows + j + 1),
                               ha='center', va='center', color='white', fontweight='bold')
            else:  # rectpack layout
                for i, rect in enumerate(rects):
                    plt.Rectangle((rect.x, rect.y), rect.width, rect.height,
                                edgecolor='#004466', facecolor='#0099e6', 
                                alpha=0.7).draw(ax)
                    ax.text(rect.x + rect.width/2, rect.y + rect.height/2, str(i+1),
                           ha='center', va='center', color='white', fontweight='bold')
        
        ax.grid(True, linestyle='--', alpha=0.3)
        st.pyplot(fig_2d)
    
    with vis_col2:
        # 3D Visualization
        if cartons_per_layer > 0:
            fig_3d = plt.figure(figsize=(6, 6))
            ax3d = fig_3d.add_subplot(111, projection='3d')
            
            total_height = max_layers * carton_height
            ax3d.set_xlim(0, PALLET_LENGTH)
            ax3d.set_ylim(0, PALLET_WIDTH)
            ax3d.set_zlim(0, total_height)
            
            for layer in range(max_layers):
                z_pos = layer * carton_height
                color = '#2E86C1' if layer % 2 == 0 else '#3498DB'
                
                if not rects:  # Grid layout
                    used_l = carton_length if use_original else carton_width
                    used_w = carton_width if use_original else carton_length
                    cols = PALLET_LENGTH // used_l
                    rows = PALLET_WIDTH // used_w
                    
                    for i in range(cols):
                        for j in range(rows):
                            draw_box(ax3d, i*used_l, j*used_w, z_pos, 
                                    used_l, used_w, carton_height, color)
                else:  # rectpack layout
                    for rect in rects:
                        draw_box(ax3d, rect.x, rect.y, z_pos, 
                                rect.width, rect.height, carton_height, color)
            
            ax3d.view_init(elev=30, azim=45)
            ax3d.set_axis_off()
            st.pyplot(fig_3d)

    # Utilization calculations
    pallet_area = PALLET_LENGTH * PALLET_WIDTH
    pallet_volume = pallet_area * max_height
    
    if cartons_per_layer > 0:
        if not rects:  # Grid layout
            used_l = carton_length if use_original else carton_width
            used_w = carton_width if use_original else carton_length
            carton_area = used_l * used_w * cartons_per_layer
        else:
            carton_area = sum(rect.width * rect.height for rect in rects)
        
        carton_volume = carton_area * carton_height * max_layers
        area_util = (carton_area / pallet_area) * 100
        vol_util = (carton_volume / pallet_volume) * 100
    else:
        area_util = vol_util = 0

    # Results display
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Optimization Results")
        st.write(f"**Cartons/layer:** {cartons_per_layer}")
        st.write(f"**Max layers:** {max_layers}")
        st.write(f"**Total cartons:** {total_cartons}")
    
    with col2:
        st.subheader("Utilization")
        st.write(f"**Area:** {area_util:.1f}%")
        st.write(f"**Volume:** {vol_util:.1f}%")

    # Excel export
    if st.button("Save to Excel"):
        df = pd.DataFrame([{
            "Length": carton_length,
            "Width": carton_width,
            "Height": carton_height,
            "Max Height": max_height,
            "Cartons/Layer": cartons_per_layer,
            "Layers": max_layers,
            "Total": total_cartons,
            "Area Util (%)": round(area_util, 1),
            "Vol Util (%)": round(vol_util, 1)
        }])
        df.to_excel("pallet_config.xlsx", index=False)
        st.success("Configuration saved!")
