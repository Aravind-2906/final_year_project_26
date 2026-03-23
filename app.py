from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask import send_file
import sqlite3
import os
from werkzeug.utils import secure_filename
from src.predict import predict_for_web
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")
print("Running from:", os.getcwd())

app = Flask(__name__)
app.secret_key = "glaucoma_secret"

# ================= UPLOAD CONFIG ================= #
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================= DATABASE ================= #
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            phone TEXT,
            address TEXT,
            password TEXT
        )
    """)
    c.execute("""
CREATE TABLE IF NOT EXISTS predictions(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_email TEXT,
eye TEXT,
result TEXT,
confidence REAL,
cdr REAL,
date TEXT
)
""")
    conn.commit()
    conn.close()

init_db()

# ================= HELPER ================= #
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ================= LOGIN ================= #
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = email
            return redirect(url_for("home"))
        return "Invalid credentials ❌"

    return render_template("login.html")


# ================= REGISTER ================= #
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        address = request.form["address"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute(
        "INSERT INTO users(name,email,phone,address,password) VALUES(?,?,?,?,?)",
        (name,email,phone,address,password)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")

# ================= HOME ================= #
@app.route("/home")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("home.html")


# ================= DETECT PAGE ================= #
@app.route("/detect")
def detect():

    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT name,email,phone,address FROM users WHERE email=?",
    (session["user"],))

    user = c.fetchone()
    conn.close()

    return render_template(
        "detect.html",
        name=user[0],
        email=user[1],
        phone=user[2],
        address=user[3]
    )

# ================= AI PREDICT ================= #
@app.route("/predict", methods=["POST"])
def predict():
    try:

        if "image" not in request.files:
            return jsonify({"status": "error", "message": "No image uploaded"})

        file = request.files["image"]

        if file.filename == "":
            return jsonify({"status": "error", "message": "No file selected"})

        if not allowed_file(file.filename):
            return jsonify({"status": "error", "message": "Invalid file type"})
        import time
        filename = str(int(time.time())) + "_" + secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # 🔹 AI Prediction
        result = predict_for_web(filepath)

        # 🔹 Save prediction to database ONLY if success
        if result["status"] == "success":

            from datetime import datetime

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            c.execute(
                """
                INSERT INTO predictions(user_email, eye, result, confidence, cdr, date)
                VALUES (?,?,?,?,?,?)
                """,
                (
                    session.get("user"),
                    request.form.get("eyeType", "Unknown"),
                    result["result"],
                    result["confidence"],
                    result["cdr"],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )

            conn.commit()
            conn.close()

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })
    
@app.route("/validate", methods=["POST"])
def validate_image():
    try:

        if "image" not in request.files:
            return jsonify({"status": "error", "message": "No image uploaded"})

        file = request.files["image"]

        import time

        filename = str(int(time.time())) + "_" + secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        from src.predict import is_retina_image
        import cv2

        img = cv2.imread(filepath)

        if not is_retina_image(img):
            return jsonify({"status": "invalid"})

        return jsonify({"status": "valid"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/generate_report", methods=["POST"])
def generate_report():
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from datetime import datetime

    result = request.form["result"]
    confidence = request.form["confidence"]
    cdr = request.form["cdr"]
    risk_score = int(request.form["riskScore"])
    eye = request.form.get("eyeType","Unknown")

    test_datetime = datetime.now().strftime("%d %B %Y  %I:%M %p")
    report_id = datetime.now().strftime("OG-%Y%m%d-%H%M")

    # Get patient details from database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name,phone,address FROM users WHERE email=?", (session["user"],))
    user = c.fetchone()
    conn.close()

    name = user[0]
    phone = user[1]
    address = user[2]

    # Unique report filename
    name_clean = name.replace(" ","_")
    eye_clean = eye.replace(" ","")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    filename = f"{name_clean}_{eye_clean}_Glaucoma_Report_{timestamp}.pdf"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(filepath)

    elements = []

    # HEADER
    elements.append(Paragraph("<b>OptiGuard</b>", styles["Title"]))
    elements.append(Paragraph("Glaucoma Screening Report", styles["Heading2"]))
    elements.append(Spacer(1,20))

    # PATIENT INFO TABLE
    elements.append(Paragraph("<b>Patient Information</b>", styles["Heading3"]))

    patient_data = [
    ["Report ID", report_id],
    ["Patient Name", name],
    ["Phone Number", phone],
    ["Address", address],
    ["Eye Tested", eye],
    ["Date & Time of Test", test_datetime]
    ]

    table1 = Table(patient_data, colWidths=[200,250])
    table1.setStyle([
    ("GRID",(0,0),(-1,-1),1,colors.grey)
    ])

    elements.append(table1)
    elements.append(Spacer(1,20))

    # CLINICAL RESULTS
    elements.append(Paragraph("<b>Clinical Test Results</b>", styles["Heading3"]))

    result_data = [
    ["Diagnosis", result],
    ["Confidence Level", confidence + "%"],
    ["Cup-to-Disc Ratio (CDR)", cdr],
    ["Risk Assessment Score", str(risk_score)]
    ]

    table2 = Table(result_data, colWidths=[200,250])
    table2.setStyle([
    ("GRID",(0,0),(-1,-1),1,colors.grey)
    ])

    elements.append(table2)
    elements.append(Spacer(1,20))

    # RECOMMENDATION
    elements.append(Paragraph("<b>Clinical Recommendation</b>", styles["Heading3"]))

    if result == "Glaucoma":
        advice = "Screening results indicate possible glaucomatous changes. A comprehensive ophthalmologic examination is recommended."
    else:
        advice = "No significant glaucomatous indicators detected. Routine ophthalmic screening is advised."

    elements.append(Paragraph(advice, styles["BodyText"]))

    elements.append(Spacer(1,30))

    elements.append(Paragraph(
    "This report is intended for screening purposes only and does not replace clinical diagnosis by a licensed ophthalmologist.",
    styles["Italic"]
    ))

    doc.build(elements)
    return send_file(filepath, as_attachment=True)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================= RUN ================= #
if __name__ == "__main__":
    app.run(debug=True)
    app.run(host="0.0.0.0", port=5000)
