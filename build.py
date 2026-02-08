import subprocess
import sys
import os

subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "pyinstaller"])

import PyInstaller.__main__
from PIL import Image

icon_paths_to_check = ['icon.ico', 'icon.png', 'assets/icon.ico', 'icons/icon.ico']
icon_file = None

for icon_path in icon_paths_to_check:
    if os.path.exists(icon_path):
        icon_file = icon_path
        break

if icon_file and icon_file.endswith('.png'):
    try:
        img = Image.open(icon_file)
        ico_path = 'converted_icon.ico'
        img.save(ico_path, format='ICO')
        icon_file = ico_path
    except Exception as e:
        print(f"Error: {e}")
        icon_file = None

if not icon_file:
    try:
        img = Image.new('RGB', (64, 64), color='blue')

        from PIL import ImageDraw

        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 54, 54], outline='white', width=3)

        try:
            from PIL import ImageFont

            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()

        draw.text((32, 32), "G", fill='white', anchor="mm", font=font)

        icon_file = 'default_icon.ico'
        img.save(icon_file, format='ICO')
    except Exception as e:
        print(f"Error: {e}")
        icon_file = None


args = [
    'main.py',
    '--name=GIFF',
    '--onefile',
    '--windowed',
    '--clean',
    '--noconfirm',
]

if icon_file and os.path.exists(icon_file):
    args.append(f'--icon={icon_file}')

if icon_file:
    args.append(f'--add-data={icon_file};.')

PyInstaller.__main__.run(args)

temp_icons = ['converted_icon.ico', 'default_icon.ico']
for temp_icon in temp_icons:
    if os.path.exists(temp_icon):
        try:
            os.remove(temp_icon)
        except:
            pass

print("\nBuild complete!")
