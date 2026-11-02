from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def add_product_label(image_path, product_name):
    image_path = Path(image_path)

    with Image.open(image_path) as original:
        image = original.convert("RGB")

    draw = ImageDraw.Draw(image)
    width, height = image.size

    # Area label di bagian atas gambar
    margin = int(width * 0.06)
    label_height = int(height * 0.12)

    x1 = margin
    y1 = margin
    x2 = width - margin
    y2 = margin + label_height

    # Latar belakang label
    draw.rounded_rectangle(
        (x1, y1, x2, y2),
        radius=12,
        fill="#FFFFFF"
    )

    # Font
    font_path = Path("C:/Windows/Fonts/arialbd.ttf")

    font_size = max(14, int(width * 0.045))

    if font_path.exists():
        font = ImageFont.truetype(str(font_path), font_size)
    else:
        font = ImageFont.load_default()

    # Nama produk
    text = product_name.upper()

    # Sesuaikan ukuran tulisan
    while draw.textbbox((0, 0), text, font=font)[2] > (x2 - x1 - 20):
        font_size -= 1

        if font_size < 10:
            break

        if font_path.exists():
            font = ImageFont.truetype(str(font_path), font_size)

    # Posisi tulisan
    bbox = draw.textbbox((0, 0), text, font=font)

    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    text_x = (width - text_width) / 2
    text_y = y1 + (label_height - text_height) / 2 - bbox[1]

    draw.text(
        (text_x, text_y),
        text,
        font=font,
        fill="#222222"
    )

    image.save(image_path, format="PNG")

    return str(image_path)