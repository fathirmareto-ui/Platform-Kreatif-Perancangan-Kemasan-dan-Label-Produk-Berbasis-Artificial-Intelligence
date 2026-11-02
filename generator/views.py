from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from .forms import RegisterForm

from urllib.error import HTTPError, URLError
from .comfyui_service import generate_packaging


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        error = "Username atau password salah."

    return render(request, "generator/login.html", {
        "error": error
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("login")

    return render(request, "generator/register.html", {
        "form": form
    })


def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("login")

    return render(request, "generator/logout.html")


@login_required(login_url="login")
def dashboard(request):
    return render(request, "generator/dashboard.html")


@login_required(login_url="login")
def home(request):
    context = {}

    if request.method == "POST":
        product_name = request.POST.get("product_name", "").strip()
        description = request.POST.get("description", "").strip()
        theme = request.POST.get("theme", "").strip()
        packaging_type = request.POST.get("packaging_type", "").strip()
        product_image = request.FILES.get("product_image")

        errors = []

        valid_packaging_types = [
            "standing_pouch",
            "box",
            "bottle",
            "sachet",
            "jar",
            "can",
        ]

        if not product_name:
            errors.append("Nama produk wajib diisi.")

        if not description:
            errors.append("Deskripsi produk wajib diisi.")

        if theme not in ["Minimalis", "Premium", "Modern", "Natural"]:
            errors.append("Silakan pilih tema desain.")

        if packaging_type not in valid_packaging_types:
            errors.append("Silakan pilih jenis kemasan.")

        if not product_image:
            errors.append("Silakan unggah foto produk.")

        elif product_image.size > 5 * 1024 * 1024:
            errors.append("Ukuran foto maksimal 5 MB.")

        elif product_image.content_type not in [
            "image/jpeg",
            "image/png",
            "image/webp"
        ]:
            errors.append("Format foto harus JPG, PNG, atau WebP.")

        if errors:
            context.update({
                "errors": errors,
                "product_name": product_name,
                "description": description,
                "theme": theme,
                "packaging_type": packaging_type,
            })

        else:
            file_path = default_storage.save(
                f"uploads/{product_image.name}",
                product_image
            )

            context.update({
                "product_name": product_name,
                "description": description,
                "theme": theme,
                "packaging_type": packaging_type,
                "image_url": default_storage.url(file_path),
                "submitted": True,
            })

            try:
                result = generate_packaging(
                    product_name,
                    description,
                    theme,
                    packaging_type
                )

                context["ai_submitted"] = True
                context["prompt_id"] = result.get("prompt_id")
                context["generated_images"] = result.get("images", [])

            except (HTTPError, URLError, TimeoutError) as error:
                context["errors"] = [
                    f"Gagal menghubungi ComfyUI: {error}"
                ]

            except Exception as error:
                context["errors"] = [
                    f"Terjadi kesalahan saat memproses AI: {error}"
                ]

    return render(request, "generator/index.html", context)