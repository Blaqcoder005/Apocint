➡️Apostolic Chapel International – Habitation of Grace 🌍⛪

This is the official website for Apostolic Chapel International {Habitation of Grace}, built to represent the Church's vision, history, ministries, sermons, and events online.

➡️ 🔧 Tech Stack

- Frontend: HTML, CSS (Custom & Responsive), JavaScript
- Backend: Python (Flask)
- Database: MariaDB (MySQL)
- Hosting/Deployment: Termux (Localhost), GitHub, Render

➡️ 📁 Project Structure

Apocimt/
├── static/                  
│   ├── style.css
│   ├── frontend.css
│   ├── optimized-background.jpg
│   ├── pastor.jpg
│   └── ...
├── templates/              
│   ├── home.html
│   ├── about.html
│   ├── events.html
│   ├── contact.html
│   ├── sermon.html
│   └── admin/             
│       ├── admin.html
│       ├── admin_uploads.html
│       ├── admin_events.html
│       └── admin_sermons.html
├── apocint.py              
├── requirements.txt
└── render.yaml             

💡 Features

🔥 Home page with parallax design and welcome banner

📖 About page with church history, doctrine, and pastor profile

🎧 Sermons section with latest uploads and audio player

📅 Events section showing upcoming church programs

📨 Contact form with server-side form validation and database integration

🔐 Admin Panel for managing messages, sermons, and events


📥 Installation & Running

Local Setup (via Termux or Linux)

1. Clone the repository:

git clone https://github.com/Blaqcoder005/Apocimt.git
cd Apocimt


2. Install dependencies:

pip install -r requirements.txt


3. Start the development server:

python apocint.py


4. Access it:

Visit http://localhost:2000 or your mobile IP if accessing from another device.



Deployment (Render)

This project includes a render.yaml file for automated deployment using Render.com.


📌 Notes

The database must be set up with sermons, events, and messages tables.

Admin uploads are handled via custom dashboard routes.


🙏 Special Thanks

To everyone contributing or helping behind the scenes to make the vision of Apostolic Chapel Int'l digital a reality.


