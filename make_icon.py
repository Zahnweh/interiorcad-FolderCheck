"""make_icon.py – erstellt icon.ico aus icon.png"""
from PIL import Image
import sys, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
img = Image.open("icon.png").convert("RGBA")
img.save("icon.ico", format="ICO",
         sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
print("  -> icon.ico erstellt")
