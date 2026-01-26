import os
import sys

def install_and_import_pil():
    try:
        from PIL import Image
        return Image
    except ImportError:
        print("PIL not found. Installing Pillow...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        from PIL import Image
        return Image

Image = install_and_import_pil()
from collections import Counter

def get_dominant_colors(image_path, num_colors=3):
    try:
        img = Image.open(image_path)
        img = img.resize((150, 150))  # Resize for faster processing
        img = img.convert("RGBA")
        
        # Get pixels and remove transparent ones
        pixels = [p[:3] for p in list(img.getdata()) if p[3] > 128]
        
        if not pixels:
            return []

        counts = Counter(pixels)
        most_common = counts.most_common(num_colors)
        
        hex_colors = []
        for color, count in most_common:
            hex_colors.append('#{:02x}{:02x}{:02x}'.format(*color))
            
        return hex_colors
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    logo_path = r"F:\New folder (24)\favicon_io\full logo.png"
    if os.path.exists(logo_path):
        colors = get_dominant_colors(logo_path, num_colors=4)
        with open("colors.txt", "w") as f:
            f.write(str(colors))
    else:
        with open("colors.txt", "w") as f:
            f.write("Logo file not found.")
