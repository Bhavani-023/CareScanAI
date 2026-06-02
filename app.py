from flask import Flask, render_template, request
import os
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import base64
import uuid

# Set Tesseract path (Check this path carefully)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)

# Use absolute upload path (safer)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads folder if not exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    image_path = None

    # -------- CASE 1: File Upload --------
    if "image" in request.files and request.files["image"].filename != "":
        image = request.files["image"]

        # Generate unique filename
        filename = str(uuid.uuid4()) + "_" + image.filename
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

    # -------- CASE 2: Camera Capture --------
    elif request.form.get("image_data"):
        image_data = request.form.get("image_data")

        image_data = image_data.split(",")[1]
        image_bytes = base64.b64decode(image_data)

        filename = str(uuid.uuid4()) + "_captured.png"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        with open(image_path, "wb") as f:
            f.write(image_bytes)

    else:
        return "No image received"

    # -------- OCR PROCESSING --------
    try:
        img = Image.open(image_path)
        img = img.convert("L")
        img = ImageEnhance.Contrast(img).enhance(2)
        img = img.filter(ImageFilter.SHARPEN)

        text = pytesseract.image_to_string(img, config="--oem 3 --psm 6")

    except Exception as e:
        return f"OCR Error: {str(e)}"

    # -------- Extract Medicines --------
    medicines = extract_medicines(text)

    output = []
    for med in medicines:
        times = assign_time(med)
        output.append({"medicine": med, "times": times})

    return render_template(
        "index.html",
        output=output,
        success="Image processed successfully!"
    )


# --------- MEDICINE FILTER ----------
def extract_medicines(text):
    medicine_list = [
        "Paracetamol", "Amoxicillin", "Ciprofloxacin",
        "Azithromycin", "Ceftriaxone", "Amikacin",
        "Meropenem", "Imipenem", "Nitrofurantoin",
        "Metformin", "Ibuprofen"
    ]

    found = []
    for med in medicine_list:
        if med.lower() in text.lower():
            found.append(med)

    return found


# --------- REMINDER TIME LOGIC ----------
def assign_time(medicine):
    critical = ["Ciprofloxacin", "Amikacin", "Ceftriaxone", "Meropenem"]

    if medicine in critical:
        return ["08:00 AM", "02:00 PM", "08:00 PM"]
    else:
        return ["09:00 AM", "09:00 PM"]


if __name__ == "__main__":
    app.run(debug=True)