# 👁️ AI-Based Glaucoma Detection System

## 📌 Project Overview
This project is a web-based application that detects glaucoma from retinal fundus images using Deep Learning. The system uses a trained Convolutional Neural Network (CNN) model to classify images as **Glaucoma** or **Normal**.

---

## 🚀 Features
- Upload retinal fundus image
- Image preview before prediction
- AI-based glaucoma detection
- Instant result display
- Web interface using Flask
- User-friendly UI

---

## 🧠 Technologies Used
- Python
- Flask
- TensorFlow / Keras
- OpenCV
- NumPy
- HTML, CSS, JavaScript

---

## 🏗️ Project Structure

glaucoma_web_app/
│
├── app.py
├── requirements.txt
├── Procfile
│
├── model/
│ └── glaucoma_model.h5
│
├── static/
│ ├── style.css
│ ├── script.js
│ └── images/
│
├── templates/
│ ├── index.html
│ ├── login.html
│ └── register.html


---

## ⚙️ Installation & Setup

### 1. Clone Repository

git clone https://github.com/yourusername/glaucoma-detection-app.git

cd glaucoma-detection-app


### 2. Create Virtual Environment

python -m venv venv
venv\Scripts\activate # Windows


### 3. Install Dependencies

pip install -r requirements.txt


### 4. Run Application

python app.py


### 5. Open in Browser

http://127.0.0.1:5000


---

## 🌐 Deployment
This project can be deployed using **Render Cloud Platform**.

---

## 🧪 Model Details
- Model Type: CNN (Convolutional Neural Network)
- Input Size: 224x224
- Output: Binary Classification (Glaucoma / Normal)

---

## 📊 Future Improvements
- Add Grad-CAM visualization
- Improve model accuracy
- Add user authentication system
- Deploy using custom domain

---

## 👨‍💻 Author
**Dinesh kumar T.S**
**Aravind S.A**
**Hari sankar A.S**
**kavikkumar**

---

## 📄 License
This project is for educational purposes.
