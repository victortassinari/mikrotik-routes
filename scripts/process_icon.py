from PIL import Image
import os

# Paths
source_png = r"c:\Users\victo\source\repos\mikrotik-routes\app\assets\icon.png"
assets_dir = r"c:\Users\victo\source\repos\mikrotik-routes\app\assets"

target_ico = os.path.join(assets_dir, "icon.ico")

if not os.path.exists(assets_dir):
    os.makedirs(assets_dir)

# Open and save as PNG in assets
img = Image.open(source_png)

# Convert to ICO
# Icon sizes usually include 16x16, 32x32, 48x48, 64x64, 128x128, 256x256
icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
img.save(target_ico, format='ICO', sizes=icon_sizes)
print(f"Saved ICO to {target_ico}")
