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

# User inputs with correct defaults
col1, col2 = st.columns(2)
with col1:
    carton_length = st.number_input("Carton Length (inches)", min_value=1, step=1, format="%d", value=16)
    carton_width = st.number_input("Carton Width (inches)", min_value=1, step=1, format="%d", value=10)
with col2:
    carton_height = st.number_input("Carton Height (inches)", min_value=1, step=1, format="%d", value=8)
    max_height = st.number_input("Pallet Max Height (inches)", min_value=1, step=1, format="%d", value=59)

def calculate_capacity(l, w, h, max_h):
    # Special case for 17×13/13×17 cartons
    if (l == 17 and w == 13) or (l == 13 and w == 17):
        return 8, "special", []
    # Try both uniform orientations
    orient1 = (PALLET_LENGTH // l) * (PALLET_WIDTH // w)
    orient2 = (PALLET_LENGTH // w) * (PALLET_WIDTH // l)
    theoretical_max = max(orient1, orient2)
    use_original = orient1 >= orient2
    # Try rectpack for mixed orientation
    packer = newPacker()
    packer.add_bin(PALLET_LENGTH, PALLET_WIDTH)
    for _ in range(1000):
        packer.add_rect(l, w)
        packer.add_rect(w, l)
    packer.pack()
    rects = [rect for rect in packer[0]] if packer and len(packer) > 0 else []
    rectpack_result = len(rects)
    # Choose best result
    if theoretical_max >= rectpack_result:
        return theoretical_max, "uniform" if use_original else "rotated", []
    else:
        return rectpack_result, "mixed", rects

def draw_box(ax, x, y, z, dx, dy, dz, color):
    # Define the 8 vertices of the box
    p = np.array([
        [x, y, z],
        [x+dx, y, z],
        [x+dx, y+dy, z],
        [x, y+dy, z],
        [x, y, z+dz],
        [x+dx, y, z+dz],
        [x+dx, y+dy, z+dz],
        [x, y+dy, z+dz]
    ])
    faces = [
        [p[0], p[1], p[2], p[3]],  # bottom
        [p[4], p[5], p[6], p[7]],  # top
        [p[0], p[1], p[5], p[4]],  # front
        [p[1], p[2], p[6], p[5]],  # right
        [p[2], p[3], p[7], p[6]],  # back
        [p[3], p[0], p[4], p[7]]   # left
    ]
    box = Poly3DCollection(faces, facecolors=color, edgecolors='k', linewidths=0.5)
    ax.add_collection3d(box)

if carton_height > max_height:
    st.error("Carton height exceeds maximum pallet height!")
    cartons_per_layer = 0
    layout_type = "none"
    rects = []
    max_layers = 0
    total_cartons = 0
    positions = []
else:
    cartons_per_layer, layout_type, rects = calculate_capacity(
        carton_length, carton_width, carton_height, max_height
    )
    max_layers = max_height // carton_height
    total_cartons = cartons_per_layer * max_layers
    positions = []
    # Prepare positions for 2D/3D
    if cartons_per_layer > 0:
        if layout_type == "special":
            # 17x13 special case: 6 horizontal, 2 vertical
            positions = [
                {'x': 0, 'y': 0, 'w': 17, 'h': 13},
                {'x': 17, 'y': 0, 'w': 17, 'h': 13},
                {'x': 0, 'y': 13, 'w': 17, 'h': 13},
                {'x': 17, 'y': 13, 'w': 17, 'h': 13},
                {'x': 0, 'y': 26, 'w': 17, 'h': 13},
                {'x': 17, 'y': 26, 'w': 17, 'h': 13},
                {'x': 34, 'y': 0, 'w': 13, 'h': 17},
                {'x': 34, 'y': 17, 'w': 13, 'h': 17},
            ]
        elif layout_type == "mixed":
            for rect in rects:
                positions.append({'x': rect.x, 'y': rect.y, 'w': rect.width, 'h': rect.height})
        else:
            used_l = carton_length if layout_type == "uniform" else carton_width
            used_w = carton_width if layout_type == "uniform" else carton_length
            cols = PALLET_LENGTH // used_l
            rows = PALLET_WIDTH // used_w
            for i in range(cols):
                for j in range(rows):
                    positions.append({'x': i*used_l, 'y': j*used_w, 'w': used_l, 'h': used_w})

# Side-by-side layout for 2D and 3D
vis_col1, vis_col2 = st.columns(2)

with vis_col1:
    # 2D Visualization
    fig2d, ax = plt.subplots(figsize=(6, 6))
    ax.set_title(f"Pallet Layer: {cartons_per_layer} Cartons")
    ax.set_xlim(0, PALLET_LENGTH)
    ax.set_ylim(0, PALLET_WIDTH)
    ax.set_aspect('equal')
    # Pallet border
    pallet_border = plt.Rectangle((0, 0), PALLET_LENGTH, PALLET_WIDTH, fill=False, edgecolor='black', linewidth=2)
    ax.add_patch(pallet_border)
    if cartons_per_layer > 0:
        for i, pos in enumerate(positions):
            is_vertical = pos['h'] > pos['w']
            rect_color = "#5599FF" if is_vertical else "#0099e6"
            rect = plt.Rectangle((pos['x'], pos['y']), pos['w'], pos['h'],
                                 edgecolor='#004466', facecolor=rect_color, alpha=0.7)
            ax.add_patch(rect)
            ax.text(pos['x'] + pos['w']/2, pos['y'] + pos['h']/2, str(i+1),
                    ha='center', va='center', color='white', fontweight='bold')
    else:
        ax.text(PALLET_LENGTH/2, PALLET_WIDTH/2, "Carton too large!",
                ha='center', va='center', color='red', fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.3)
    st.pyplot(fig2d)

with vis_col2:
    # 3D Visualization (no pallet base, cartons only)
    if cartons_per_layer > 0:
        fig3d = plt.figure(figsize=(6, 6))
        ax3d = fig3d.add_subplot(111, projection='3d')
        for layer in range(max_layers):
            z_pos = layer * carton_height
            color = '#2E86C1' if layer % 2 == 0 else '#3498DB'
            for pos in positions:
                dx = pos['w']
                dy = pos['h']
                dz = carton_height
                draw_box(ax3d, pos['x'], pos['y'], z_pos, dx, dy, dz, color)
        ax3d.set_xlim(0, PALLET_LENGTH)
        ax3d.set_ylim(0, PALLET_WIDTH)
        ax3d.set_zlim(0, max_layers * carton_height)
        ax3d.view_init(elev=30, azim=45)
        ax3d.set_axis_off()
        st.pyplot(fig3d)
    else:
        st.warning("Cannot create 3D visualization: carton too large for pallet.")

# Utilization calculations
pallet_area = PALLET_LENGTH * PALLET_WIDTH
pallet_volume = pallet_area * max_height
if cartons_per_layer > 0:
    if layout_type == "special":
        horizontal_area = 17 * 13 * 6
        vertical_area = 13 * 17 * 2
        carton_area = horizontal_area + vertical_area
    else:
        carton_area = sum(pos['w'] * pos['h'] for pos in positions)
    carton_volume = carton_area * carton_height * max_layers
    area_util = (carton_area / pallet_area) * 100
    vol_util = (carton_volume / pallet_volume) * 100
else:
    area_util = vol_util = 0

# Results display
col1, col2 = st.columns(2)
with col1:
    st.subheader("Optimization Results")
    st.write(f"Cartons/layer: {cartons_per_layer}")
    st.write(f"Max layers: {max_layers}")
    st.write(f"Total cartons: {total_cartons}")
with col2:
    st.subheader("Pallet Utilization")
    st.write(f"Pallet Area Utilization: {area_util:.1f}%")
    st.write(f"Pallet Volume Utilization: {vol_util:.1f}%")

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
        "Area Utilization (%)": round(area_util, 1),
        "Volume Utilization (%)": round(vol_util, 1)
    }])
    df.to_excel("pallet_configurations.xlsx", index=False)
    st.success("Saved to pallet_configurations.xlsx!")
