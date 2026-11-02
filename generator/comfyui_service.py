import json
import time
import uuid
import urllib.request
import urllib.parse
from pathlib import Path

from django.conf import settings
from .label_service import add_product_label


COMFYUI_URL = "http://127.0.0.1:8188"


def generate_packaging(product_name, description, theme, packaging_type):

    # 1. Membaca workflow ComfyUI
    workflow_path = Path(settings.BASE_DIR) / "KreatifAI_API.json"

    with open(workflow_path, "r", encoding="utf-8") as file:
        workflow = json.load(file)

    # 2. Menentukan bentuk kemasan
    packaging_options = {
       "standing_pouch": (
    "ONE single upright resealable stand-up pouch (doypack), "
    "with a flat bottom gusset, sealed top edge and zipper closure, "
    "front-facing symmetrical packaging, "
    "one complete pouch only, centered in the image"
),  
    }

    if packaging_type not in packaging_options:
        raise ValueError("Jenis kemasan tidak valid.")

    selected_packaging = packaging_options[packaging_type]

    # 3. Membuat prompt berdasarkan informasi produk
    prompt = (
        f"Professional commercial product packaging design for {product_name}. "
        f"Product description: {description}. "
        f"Packaging design style: {theme}. "
        f"Packaging type: {selected_packaging}. "

        "EXACTLY ONE complete product package. "
        "The package must match the specified packaging type. "
        "Front-facing view, standing upright. "
        "Entire package fully visible from top to bottom. "
        "Centered composition with empty space around the package. "

        "The packaging artwork must clearly represent the actual product. "
        "Use realistic product illustrations matching the description. "
        "Elegant coordinated colors and professional branding. "
        "Clean front panel with space for a product name label. "

        "High-quality realistic commercial packaging mockup. "
        "Professional studio product photography, soft lighting. "
        "Simple neutral background. "
        "Sharp focus and realistic packaging proportions. "

        "No people, no human faces, no unrelated products. "
        "No extra packages, no collage, no split image."
    )

    # 4. Negative prompt
    negative_prompt = (  
    "multiple packages, two bags, three bags, duplicate products, "
    "collage, split screen, multiple panels, "
    "box packaging, bottle, jar, can, "
    "loose products, scattered food, "
    "people, faces, hands, "
    "cropped package, distorted packaging, "
    "blurry, low quality, watermark"
)

    # 5. Mengirim prompt ke workflow
    workflow["3"]["inputs"]["text"] = prompt
    workflow["5"]["inputs"]["text"] = negative_prompt

    # 6. Pengaturan AI
    workflow["4"]["inputs"]["seed"] = uuid.uuid4().int % (2**63)
    workflow["4"]["inputs"]["steps"] = 35
    workflow["4"]["inputs"]["cfg"] = 7
    workflow["4"]["inputs"]["sampler_name"] = "dpmpp_2m"
    workflow["4"]["inputs"]["scheduler"] = "karras"

    # Menghasilkan 4 variasi desain
    workflow["8"]["inputs"]["batch_size"] = 4

    # 7. Mengirim workflow ke ComfyUI
    payload = json.dumps({
        "prompt": workflow,
        "client_id": str(uuid.uuid4())
    }).encode("utf-8")

    request = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))

    prompt_id = result["prompt_id"]

    # 8. Menunggu ComfyUI menyelesaikan proses
    history = None

    for attempt in range(120):
        time.sleep(2)

        with urllib.request.urlopen(
            f"{COMFYUI_URL}/history/{prompt_id}",
            timeout=30
        ) as response:
            data = json.loads(response.read().decode("utf-8"))

        if prompt_id in data:
            history = data[prompt_id]
            break

    if history is None:
        raise TimeoutError("Proses AI terlalu lama.")

    # 9. Mengambil hasil gambar
    outputs = history.get("outputs", {})
    images = outputs.get("9", {}).get("images", [])

    if not images:
        raise RuntimeError(
            "ComfyUI tidak menghasilkan gambar. "
            "Periksa workflow dan log ComfyUI."
        )

    # 10. Menyimpan hasil desain
    generated_images = []

    output_dir = Path(settings.MEDIA_ROOT) / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    for image_info in images:

        query = urllib.parse.urlencode({
            "filename": image_info["filename"],
            "subfolder": image_info.get("subfolder", ""),
            "type": image_info.get("type", "output")
        })

        with urllib.request.urlopen(
            f"{COMFYUI_URL}/view?{query}",
            timeout=30
        ) as response:
            image_data = response.read()

        # Membuat nama file unik
        output_name = f"kemasan_{uuid.uuid4().hex}.png"
        output_path = output_dir / output_name

        # Menyimpan gambar
        with open(output_path, "wb") as file:
            file.write(image_data)

        # Menambahkan nama produk ke gambar
        add_product_label(output_path, product_name)

        # Menambahkan URL hasil desain
        generated_images.append(
            f"{settings.MEDIA_URL}generated/{output_name}"
        )

    # 11. Mengembalikan hasil ke Django
    return {
        "prompt_id": prompt_id,
        "images": generated_images
    }