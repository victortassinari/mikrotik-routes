from PIL import Image, ImageDraw

def create_warning_icon(path):
    size = (32, 32)
    image = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Yellow triangle
    padding = 4
    points = [
        (size[0] // 2, padding), # Top
        (padding, size[1] - padding), # Bottom left
        (size[0] - padding, size[1] - padding) # Bottom right
    ]
    draw.polygon(points, fill="#f1c40f")
    
    # Exclamation mark
    draw.rectangle([size[0]//2 - 1, size[1]//2 - 6, size[0]//2 + 1, size[1]//2 + 2], fill="black")
    draw.rectangle([size[0]//2 - 1, size[1]//2 + 4, size[0]//2 + 1, size[1]//2 + 6], fill="black")
    
    image.save(path)
    print(f"Created warning icon at {path}")

if __name__ == "__main__":
    import os
    assets_dir = r"c:\Users\victo\source\repos\mikrotik-routes\app\assets"
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    create_warning_icon(os.path.join(assets_dir, "warning.png"))
