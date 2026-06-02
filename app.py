from flask import Flask, render_template, request
import os
import base64
import uuid
import requests

app = Flask(__name__)

# Upload folder setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# OCR.Space API Key
API_KEY = "K87552243988957"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    image_path = None

    # -------- File Upload --------
    if "image" in request.files and request.files["image"].filename != "":
        image = request.files["image"]

        filename = str(uuid.uuid4()) + "_" + image.filename
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        image.save(image_path)

    # -------- Camera Capture --------
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

    # -------- OCR Processing --------
    try:

        with open(image_path, "rb") as f:

            response = requests.post(
                "https://api.ocr.space/parse/image",
                files={"filename": f},
                data={
                    "apikey": API_KEY,
                    "language": "eng"
                }
            )

        result = response.json()

        if result.get("IsErroredOnProcessing"):
            return "OCR failed. Please try another image."

        text = result["ParsedResults"][0]["ParsedText"]

    except Exception as e:
        print("OCR ERROR:", e)
        return f"OCR Error: {e}"

    # -------- Medicine Extraction --------
    medicines = extract_medicines(text)

    output = []

    for med in medicines:
        output.append({
            "medicine": med,
            "times": assign_time(med)
        })

    return render_template(
        "index.html",
        output=output,
        success="Prescription scanned successfully!"
    )


# -------- Medicine Filter --------
def extract_medicines(text):

    medicine_list = [
        "Paracetamol",
        "Amoxicillin",
        "Ciprofloxacin",
        "Azithromycin",
        "Ceftriaxone",
        "Amikacin",
        "Meropenem",
        "Imipenem",
        "Nitrofurantoin",
        "Metformin",
        "Ibuprofen"
    ]

    found = []

    for med in medicine_list:
        if med.lower() in text.lower():
            found.append(med)

    return found


# -------- Reminder Logic --------
def assign_time(medicine):

    critical = [
        "Ciprofloxacin",
        "Amikacin",
        "Ceftriaxone",
        "Meropenem"
    ]

    if medicine in critical:
        return ["08:00 AM", "02:00 PM", "08:00 PM"]

    return ["09:00 AM", "09:00 PM"]


if __name__ == "__main__":
    app.run(debug=True)