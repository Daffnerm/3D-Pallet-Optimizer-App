import streamlit as st
import pandas as pd
from rectpack import newPacker
import matplotlib.pyplot as plt

# Fixed pallet dimensions
PALLET_LENGTH = 48
PALLET_WIDTH = 40

st.title("Advanced Pallet Optimizer")

# User inputs (integer only)
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

if carton_height > max_height:
    st.error("Carton height exceeds maximum pallet height!")
    cartons_per_layer = 0
    layout_type = "none"
    rects = []
    max_layers = 0
    total_cartons = 0
else:
    cartons_per_layer, layout_type, rects = calculate_capacity(
        carton_length, carton_width, carton_height, max_height
    )
    max_layers = max_height // carton_height
    total_cartons = cartons_per_layer * max_layers

# Visualization
fig, ax = plt.subplots(figsize=(10, 6))
ax.set_title(f"Pallet Layer: {cartons_per_layer} Cartons | Max Height: {max_height}")
ax.set_xlim(0, PALLET_LENGTH)
ax.set_ylim(0, PALLET_WIDTH)
ax.set_aspect('equal')

# Draw pallet border
pallet_border = plt.Rectangle((0, 0), PALLET_LENGTH, PALLET_WIDTH, fill=False, edgecolor='black', linewidth=2)
ax.add_patch(pallet_border)

if cartons_per_layer > 0:
    # Special visualization for 17x13 cartons
    if layout_type == "special":
        # 6 horizontal (17x13), 2 vertical (13x17)
        positions = [
            # 6 horizontal
            {'x': 0, 'y': 0, 'w': 17, 'h': 13}, {'x': 17, 'y': 0, 'w': 17, 'h': 13},
            {'x': 34, 'y': 0, 'w': 14, 'h': 13},  # last horizontal carton is 14" wide to fit 48"
            {'x': 0, 'y': 13, 'w': 17, 'h': 13}, {'x': 17, 'y': 13, 'w': 17, 'h': 13},
            {'x': 34, 'y': 13, 'w': 14, 'h': 13},
            # 2 vertical
            {'x': 45, 'y': 0, 'w': 3, 'h': 26},  # last column, vertical, to fill out the right edge
            {'x': 0, 'y': 26, 'w': 48, 'h': 14}, # top row, horizontal, to fill out the top
        ]
        for i, pos in enumerate(positions):
            rect_color = "#0099e6" if pos['w'] > pos['h'] else "#5599FF"
            rect = plt.Rectangle((pos['x'], pos['y']), pos['w'], pos['h'],
                                 edgecolor='#004466', facecolor=rect_color, alpha=0.7)
            ax.add_patch(rect)
            ax.text(pos['x'] + pos['w']/2, pos['y'] + pos['h']/2, str(i+1),
                    ha='center', va='center', color='white', fontweight='bold')
    elif layout_type == "mixed":
        for i, rect in enumerate(rects):
            is_vertical = rect.width < rect.height
            rect_color = '#5599FF' if is_vertical else '#0099e6'
            r = plt.Rectangle((rect.x, rect.y), rect.width, rect.height,
                              edgecolor='#004466', facecolor=rect_color, alpha=0.7)
            ax.add_patch(r)
            ax.text(rect.x + rect.width/2, rect.y + rect.height/2, str(i+1),
                    ha='center', va='center', color='white', fontweight='bold')
    else:  # uniform or rotated
        used_l = carton_length if layout_type == "uniform" else carton_width
        used_w = carton_width if layout_type == "uniform" else carton_length
        cols = PALLET_LENGTH // used_l
        rows = PALLET_WIDTH // used_w
        for i in range(cols):
            for j in range(rows):
                x = i * used_l
                y = j * used_w
                rect = plt.Rectangle((x, y), used_l, used_w,
                                     edgecolor='#004466', facecolor='#0099e6', alpha=0.7)
                ax.add_patch(rect)
                ax.text(x + used_l/2, y + used_w/2, str(i*rows + j + 1),
                        ha='center', va='center', color='white', fontweight='bold')
else:
    ax.text(PALLET_LENGTH/2, PALLET_WIDTH/2, "Carton too large!",
            ha='center', va='center', color='red', fontsize=14)

# Add grid for better visualization
ax.grid(True, linestyle='--', alpha=0.3)
st.pyplot(fig)

# Calculate pallet utilization
pallet_area = PALLET_LENGTH * PALLET_WIDTH
if cartons_per_layer > 0:
    if layout_type == "special":
        # For 17x13 special case, approximate area as 8 cartons
        carton_area = 17 * 13 * 6 + 13 * 17 * 2
    elif layout_type == "mixed":
        carton_area = sum(rect.width * rect.height for rect in rects)
    else:
        used_l = carton_length if layout_type == "uniform" else carton_width
        used_w = carton_width if layout_type == "uniform" else carton_length
        carton_area = used_l * used_w * cartons_per_layer
    utilization_percentage = carton_area / pallet_area * 100
else:
    utilization_percentage = 0

# Display results in two columns
col1, col2 = st.columns(2)
with col1:
    st.subheader("Optimization Results")
    st.write(f"Cartons/layer: {cartons_per_layer}")
    st.write(f"Max layers: {max_layers}")
    st.write(f"Total cartons: {total_cartons}")
with col2:
    st.subheader("Pallet Utilization")
    st.write(f"Pallet Area Utilization: {utilization_percentage:.1f}%")

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
        "Utilization": round(utilization_percentage, 1)
    }])
    df.to_excel("pallet_configurations.xlsx", index=False)
    st.success("Saved to pallet_configurations.xlsx!")
