"""Draw Orbot's simple geometric application icon for the Windows build."""

from pathlib import Path

from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
image = Image.new("RGBA", (256, 256), (21, 26, 35, 255))
draw = ImageDraw.Draw(image)
draw.ellipse((38, 68, 218, 188), outline=(255, 203, 131), width=12)
draw.ellipse((68, 38, 188, 218), outline=(255, 203, 131), width=12)
draw.ellipse((107, 107, 149, 149), fill=(241, 245, 249))
draw.ellipse((183, 86, 213, 116), fill=(255, 203, 131))
image.save(root / "orbot" / "icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
