from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from accounts.models import Profile
from products.models import Category, Product
import re
import time


# Indicative sample prices in INR for demo/testing only, not live market rates.
# Images are fetched from LoremFlickr at seed time; an internet connection is needed.
PRODUCTS = [
    # category, name, price, stock, unit, location, description, image keywords, farmer username
    ("Vegetables", "Tomato", 35, 40, "kg", "Dindigul", "Fresh ripe tomatoes from a local farm.", "fresh,tomatoes,vegetable", "farmer_dindigul"),
    ("Vegetables", "Onion", 40, 60, "kg", "Perambalur", "Everyday cooking onions.", "red,onions,vegetable", "farmer_perambalur"),
    ("Vegetables", "Potato", 35, 45, "kg", "Nilgiris", "Clean, firm potatoes.", "potatoes,vegetable", "farmer_nilgiris"),
    ("Vegetables", "Brinjal", 40, 25, "kg", "Madurai", "Fresh purple brinjal.", "eggplant,brinjal,vegetable", "farmer_madurai"),
    ("Vegetables", "Drumstick", 70, 20, "kg", "Theni", "Tender drumsticks for sambar and poriyal.", "moringa,drumstick,vegetable", "farmer_theni"),
    ("Vegetables", "Ladies Finger", 45, 25, "kg", "Salem", "Fresh green ladies finger.", "okra,green,vegetable", "farmer_salem"),
    ("Vegetables", "Carrot", 60, 30, "kg", "Nilgiris", "Crunchy carrots.", "carrots,vegetable", "farmer_nilgiris"),
    ("Vegetables", "Cabbage", 35, 25, "kg", "Nilgiris", "Fresh cabbage heads.", "cabbage,vegetable", "farmer_nilgiris"),
    ("Vegetables", "Cauliflower", 45, 20, "piece", "Coimbatore", "Fresh cauliflower.", "cauliflower,vegetable", "farmer_coimbatore"),
    ("Vegetables", "Green Chilli", 60, 15, "kg", "Erode", "Spicy green chillies.", "green,chilli,pepper,vegetable", "farmer_erode"),
    ("Vegetables", "Cucumber", 35, 30, "kg", "Krishnagiri", "Cool, fresh cucumber.", "cucumber,vegetable", "farmer_krishnagiri"),
    ("Vegetables", "Pumpkin", 30, 30, "kg", "Thanjavur", "Locally grown pumpkin.", "pumpkin,vegetable", "farmer_thanjavur"),
    ("Leafy Greens", "Spinach", 20, 35, "bunch", "Chengalpattu", "Fresh spinach bunch.", "spinach,leafy,greens", "farmer_chengalpattu"),
    ("Leafy Greens", "Coriander Leaves", 15, 30, "bunch", "Coimbatore", "Aromatic coriander leaves.", "cilantro,coriander,herbs", "farmer_coimbatore"),
    ("Leafy Greens", "Mint Leaves", 15, 25, "bunch", "Madurai", "Fresh mint leaves.", "mint,herbs,leaves", "farmer_madurai"),
    ("Fruits", "Banana", 55, 40, "dozen", "Trichy", "Naturally ripened bananas.", "banana,bunch,fruit", "farmer_trichy"),
    ("Fruits", "Mango", 100, 25, "kg", "Krishnagiri", "Seasonal mangoes; availability may vary.", "mango,fruit", "farmer_krishnagiri"),
    ("Fruits", "Papaya", 45, 25, "kg", "Salem", "Fresh ripe papaya.", "papaya,fruit", "farmer_salem"),
    ("Fruits", "Guava", 60, 25, "kg", "Theni", "Fresh green guava.", "guava,fruit", "farmer_theni"),
    ("Fruits", "Watermelon", 30, 20, "kg", "Tiruvallur", "Juicy seasonal watermelon.", "watermelon,fruit", "farmer_tiruvallur"),
    ("Fruits", "Pomegranate", 180, 15, "kg", "Coimbatore", "Fresh pomegranates.", "pomegranate,fruit", "farmer_coimbatore"),
    ("Fruits", "Sweet Lime", 70, 20, "kg", "Tirunelveli", "Fresh sweet lime mosambi.", "sweetlime,citrus,fruit", "farmer_tirunelveli"),
    ("Fruits", "Jackfruit", 50, 15, "kg", "Panruti", "Seasonal jackfruit; price shown per kg.", "jackfruit,fruit", "farmer_panruti"),
    ("Fruits", "Coconut", 35, 30, "piece", "Pollachi", "Fresh coconut from Pollachi region.", "coconut,fruit", "farmer_pollachi"),
]

FARMERS = {
    "farmer_dindigul": ("Kumar", "Dindigul", "farmer.dindigul@example.com"),
    "farmer_perambalur": ("Selvi", "Perambalur", "farmer.perambalur@example.com"),
    "farmer_nilgiris": ("Ravi", "Nilgiris", "farmer.nilgiris@example.com"),
    "farmer_madurai": ("Meena", "Madurai", "farmer.madurai@example.com"),
    "farmer_theni": ("Murugan", "Theni", "farmer.theni@example.com"),
    "farmer_salem": ("Lakshmi", "Salem", "farmer.salem@example.com"),
    "farmer_coimbatore": ("Arun", "Coimbatore", "farmer.coimbatore@example.com"),
    "farmer_erode": ("Karthik", "Erode", "farmer.erode@example.com"),
    "farmer_krishnagiri": ("Priya", "Krishnagiri", "farmer.krishnagiri@example.com"),
    "farmer_thanjavur": ("Bala", "Thanjavur", "farmer.thanjavur@example.com"),
    "farmer_chengalpattu": ("Revathi", "Chengalpattu", "farmer.chengalpattu@example.com"),
    "farmer_trichy": ("Suresh", "Tiruchirappalli", "farmer.trichy@example.com"),
    "farmer_tiruvallur": ("Anitha", "Tiruvallur", "farmer.tiruvallur@example.com"),
    "farmer_tirunelveli": ("Joseph", "Tirunelveli", "farmer.tirunelveli@example.com"),
    "farmer_panruti": ("Gopal", "Panruti", "farmer.panruti@example.com"),
    "farmer_pollachi": ("Dhanalakshmi", "Pollachi", "farmer.pollachi@example.com"),
}


def download_image(keywords):
    url = "https://loremflickr.com/800/600/" + keywords.replace(" ", "%20")
    request = Request(url, headers={"User-Agent": "GreenHarvestDemo/1.0"})
    with urlopen(request, timeout=20) as response:
        content_type = response.headers.get("Content-Type", "")
        data = response.read()
    if not content_type.startswith("image/") or not data:
        raise ValueError("Image endpoint did not return an image")
    return data


class Command(BaseCommand):
    help = "Create demo Tamil Nadu farmers, categories and sample products with illustrative prices/images."

    def add_arguments(self, parser):
        parser.add_argument("--skip-images", action="store_true", help="Create products without downloading images.")

    def handle(self, *args, **options):
        categories = {}
        for category_name in ["Fruits", "Vegetables", "Leafy Greens"]:
            categories[category_name], _ = Category.objects.get_or_create(name=category_name)

        farmers = {}
        for username, (first_name, city, email) in FARMERS.items():
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first_name, "last_name": "Farmer", "email": email},
            )
            # Do not reset an existing user's password.
            if created:
                user.set_unusable_password()
                user.save()
            Profile.objects.get_or_create(user=user, defaults={"role": "farmer"})
            farmers[username] = user

        created_count = 0
        image_count = 0
        for category_name, name, price, stock, unit, city, description, keywords, farmer_username in PRODUCTS:
            product, created = Product.objects.get_or_create(
                farmer=farmers[farmer_username],
                name=name,
                defaults={
                    "category": categories[category_name],
                    "description": description,
                    "price": price,
                    "stock": stock,
                    "unit": unit,
                    "location": city,
                },
            )
            if created:
                created_count += 1
            if not options["skip_images"] and not product.image:
                try:
                    data = download_image(keywords)
                    safe_name = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
                    product.image.save(f"{safe_name}.jpg", ContentFile(data), save=True)
                    image_count += 1
                    time.sleep(0.2)
                except (URLError, HTTPError, TimeoutError, ValueError, OSError) as exc:
                    self.stdout.write(self.style.WARNING(f"Image skipped for {name}: {exc}"))

        self.stdout.write(self.style.SUCCESS(
            f"Done. New products: {created_count}; images downloaded: {image_count}; farmers checked/created: {len(farmers)}."
        ))
        self.stdout.write("Sample farmer usernames are demo accounts only; they have no usable password by default.")
        self.stdout.write("Prices are illustrative INR sample prices, not live mandi/retail rates.")
