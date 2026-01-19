# 🎵 TuneX – Music Streaming Web Application

TuneX is a **role-based music streaming web application** built using Flask.  
The project demonstrates real-world full-stack concepts such as authentication, role-based access control, playlist management, creator analytics, and AI-assisted lyrics generation.

The application focuses on practical implementation, seamless music streaming, and a clean user interface, making it suitable for learning and showcasing full-stack web development skills.

## 🌐 Live Demo
🔗 https://tunex-music-streaming-app.onrender.com

⚠️ Note: The application is hosted on a free Render instance.  
The first load may take up to 30–50 seconds due to cold start.

---

## 🚀 Features

### 👤 User
- User registration and login  
- Browse and play songs  
- Create, rename, and delete playlists  
- Add and remove songs from playlists  
- Playlist song reordering  
- Dynamic lyrics display during playback  
- Dark / Light theme toggle  
- View notifications triggered by system actions  

---

### 🎨 Creator
- Upload songs (MP3 / WAV)  
- View and manage uploaded songs  
- Track play count analytics  
- Access creator dashboard and analytics view  
- Receive notifications related to uploaded content  

---

### 🛠 Admin
- View platform-level statistics  
- View registered users and creators  
- Block and unblock users  
- Delete songs with reason-based notifications  
- Monitor overall platform activity  

⚠️ *Admin functionality is limited to platform control and does not include automated moderation.*

---

## 🤖 AI Integration
- Lyrics are generated using the **Google Gemini API**  
- Lyrics are generated based on song metadata or user input  
- Line-by-line lyrics display in the player interface  
- Generated lyrics are cached to avoid repeated API calls  

⚠️ *Lyrics are AI-generated, not speech-to-text transcription.*

---

## 📸 Screenshots

### Home Page
![Home Page](screenshots/home.png)

### Login Page
![Login Page](screenshots/login.png)

### Register Page
![Register Page](screenshots/register.png)

### User Dashboard
![User Dashboard](screenshots/user-dashboard.png)

### Creator Dashboard
![Creator Dashboard](screenshots/creator-dashboard.png)

### Admin Dashboard
![Admin Dashboard](screenshots/admin-dashboard.png)

### AI Lyrics Generation
![AI Lyrics](screenshots/lyrics.png)

---

## 🧱 Tech Stack

| Layer | Technology |
|------|-----------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python (Flask) |
| ORM | SQLAlchemy |
| Database | SQLite |
| Authentication | Werkzeug Security (Password Hashing) |
| AI Integration | Google Gemini API |
| UI | Dark / Light Mode, CSS-based Styling |

---
## 📂 Project Structure

```text
PROJECT/
│
├── main.py
├── .env
├── requirements.txt
├── README.md
│
├── controller/
│   ├── config.py
│   ├── database.py
│   └── models.py
│
├── instance/
│   └── msa.sqlite3
│
├── static/
│   ├── uploads/
│   └── tunex.png
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── user_dashboard.html
│   ├── creator_dashboard.html
│   ├── creator_analytics.html
│   ├── admin_dashboard.html
│   ├── profile.html
│   ├── edit_profile.html
│   └── change_password.html
│
└── .gitignore

```

## 🔐 Security Considerations
- Passwords are securely hashed using Werkzeug (no plaintext storage)
- Role-based access control enforced at route level
- Admin routes protected from unauthorized access


## ⚙️ Installation & Setup

### 1️⃣ Clone the repository
```bash
git clone https://github.com/arun-mahendran/tunex-music-streaming-app.git
cd tunex
```

### 2️⃣ Create and activate a virtual environment

**Windows**
```bash
python -m venv venv
venv\Scripts\activate    
```

**macOS / Linux**
```bash
python -m venv venv
source venv/bin/activate   
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Environment configuration
Create a `.env` file:
```env
GEMINI_API_KEY = your_api_key_here
SECRET_KEY = your_secret_key
```

### 5️⃣ Run the application
```bash
python main.py
```

Access the app at:
http://127.0.0.1:5000


## 🔐 Admin Access
Admin access is restricted for security reasons.

For evaluation or demonstration purposes, admin credentials can be provided upon request.


## 🎯 Learning Outcomes
- Role-based access control implementation
- Flask application structuring  
- SQLAlchemy ORM usage  
- Playlist and media management
- Creator analytics handling
- Admin-level platform control  
- AI API integration  
- Frontend–backend coordination  
  
---

## ⚠️ Deployment Limitation (Free Tier)

This application is deployed on a free Render hosting plan.

Due to the use of an ephemeral container on the free tier:
- Application data stored using SQLite is **not persistent**
- Registered users, uploaded songs, and playlists may reset after periods of inactivity or service restarts
- Uploaded media files may not be retained across restarts

This behavior is expected and does not reflect an issue with the application logic.

🔧 **Production Consideration:**  
For persistent data storage in a production environment, the application can be migrated to a managed PostgreSQL database and cloud-based storage for media files.

---

## 📌 Future Enhancements
- Global modal music player  
- Time-synced lyrics display  
- Music recommendation system
- Song likes and favorites  
- Cloud-based media storage  

---

## 🧑‍💻 Author
**Arun Mahendran B**  
Pre-final Year Engineering Student  
Aspiring Full-Stack Developer 
