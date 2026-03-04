# CHATDC
#### Video Demo:  <URL HERE>
#### Description:
**CHATDC** is a robust group messaging web application built for real-time interaction. It combines modern web technologies to provide a seamless communication experience, focusing on security, moderation, and user personalization.

## 🚀 Overview

This project was developed as part of a learning journey in web development, implementing a hybrid architecture:
* **Real-Time Engine:** Powered by **WebSockets** (Flask-SocketIO) for instantaneous message delivery.
* **Management Layer:** Traditional **HTTP requests** handle user authentication, profile management, and database persistence.

## ✨ Features

### 📨 Communication
* **Real-Time Chat:** Immediate message broadcasting to all connected users in the room.
* **Message Persistence:** All conversations are stored in a PostgreSQL database for historical access.

### 🔐 Security & Profiles
* **Secure Authentication:** Registration and login system with encrypted passwords using industry standards.
* **Custom Profiles:** Users can upload personalized avatars directly to the cloud via **Cloudinary**.
* **Password Management:** Secure functionality to update credentials with previous password validation.

### 🛡️ Moderation & Roles
* **User Level:** Full control over their own content (Edit/Delete).
* **Admin Level:** Elevated privileges to delete any message to maintain community standards, without the ability to modify others' content.

### 📱 Responsive Design
* Dynamic navigation bar that adapts based on the user's session status.
* Fully responsive interface built with Bootstrap 5.

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Backend** | Python, Flask, Flask-SocketIO |
| **Database** | PostgreSQL (with `psycopg_pool`) |
| **Frontend** | HTML5, Jinja2, Bootstrap 5, JavaScript |
| **Cloud Storage** | Cloudinary |

---

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Angelussz/chatdc.git
   cd chatdc
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   * Linux: source venv/bin/activate
   * Windows: venv\Scripts ctivate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables (.env):**
   Create a `.env` file in the root directory and add your credentials:
   ```env
   FLASK_APP=app
   FLASK_DEBUG=1
   DATABASE_URL= POSTGRES URL
   SECRET_KEY= your-secret-key
   CLOUDINARY_CLOUD_NAME= cloudinary-name
   CLOUDINARY_API_KEY= cloudinary-api-key
   CLOUDINARY_API_SECRET= cloudinary-api-secret
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```