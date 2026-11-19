from PIL import Image
from pathlib import Path

BASE_DIR = Path(__file__).parent

image = Image.open(
    BASE_DIR / "work.png"
).convert("RGBA")

image.thumbnail(
    (256, 256),
    Image.Resampling.LANCZOS
)

icon = Image.new("RGBA", (256, 256))

icon.paste(
    image,
    (
        (256 - image.width) // 2,
        (256 - image.height) // 2
    )
)

icon.save(
    BASE_DIR / "smiski.ico",
    sizes=[
        (16, 16),
        (32, 32),
        (48, 48),
        (64, 64),
        (128, 128),
        (256, 256)
    ]
)

print("Smiski icon created!")