
# 🌱 Smiski Focus

A desktop productivity companion that combines distraction blocking,
Pomodoro timers, and interactive study analytics to help students
understand and improve their study habits.

## ✨ Features

- Animated desktop companion with customizable poses and sizes
- Instagram blocking through a Chrome extension
- Customizable Pomodoro focus and break timers
- Real-time distraction counter
- Automatic study session tracking
- Persistent settings using JSON
- SQLite database for historical records
- Interactive analytics dashboard
- Downloadable CSV reports
- Single-click Windows launcher

## 📊 Analytics Dashboard

The dashboard provides:

- Total recorded focus time
- Session completion rates
- Average session duration
- Daily focus trends
- Instagram blocking trends
- Hourly distraction patterns
- Weekly distraction heatmaps
- Automated descriptive insights
- Date range filtering

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Python | Backend and application logic |
| JavaScript | Chrome extension |
| HTML/CSS | User interface |
| PyQt6 | Desktop GUI |
| Flask | Local REST API |
| SQLite | Database management |
| Pandas | Data processing and analysis |
| Plotly | Interactive data visualization |
| Streamlit | Analytics dashboard |
| Pillow | Desktop icon generation |

## 🏗️ System Architecture

Chrome Extension → Flask API → SQLite Database

SQLite Database → Desktop Companion

SQLite Database → Pandas → Streamlit Dashboard

The Chrome extension detects Instagram visits and sends
blocking events to a local Flask API. These events are stored
in SQLite and retrieved by the desktop companion and analytics
dashboard.

## 📁 Project Structure

- smiski.py — Desktop companion and focus timer
- server.py — Flask REST API
- database.py — SQLite database operations
- dashboard.py — Interactive analytics dashboard
- launcher.pyw — Background application launcher
- create_icon.py — Windows icon generator
- requirements.txt — Python dependencies

## 🚀 Installation

### Install the Chrome Extension

1. Open Google Chrome.
2. Navigate to chrome://extensions/.
3. Enable Developer Mode.
4. Click Load unpacked.
5. Select the chrome-extension folder.
6. Enable focus mode through the extension popup.

The extension requires user-provided image assets named
work.png, sleep.png, push.png, and peek.png inside the
chrome-extension folder.

Start the desktop application to enable distraction
logging and real-time analytics.


### Prerequisites

- Python 3.11
- Windows
- Google Chrome

### Install dependencies

    python -m pip install -r requirements.txt

### Initialize the database

    python database.py

### Image assets

Provide your own permitted PNG images named:

- work.png
- sleep.png
- push.png
- peek.png

Image assets are not distributed with this repository.

### Launch the application

    python launcher.pyw

### Open the analytics dashboard

Visit http://127.0.0.1:8501 or select
Open Analytics Dashboard from the desktop companion menu.

## 🔒 Privacy

Study records and distraction history are stored locally.
Personal databases, configuration files, and logs are excluded
from version control.

## 📚 Learning Outcomes

This project explores:

- Database design and SQL queries
- REST API integration
- Data cleaning and transformation
- Feature engineering
- Exploratory data analysis
- Interactive data visualization
- Desktop application development

## 🔮 Future Improvements

- Additional customizable website blockers
- Study goals and progress tracking
- Improved application packaging
- Long-term study pattern analysis
- Cross-platform support

## Development Note

Developed as a personal learning project with AI-assisted
programming, debugging, and documentation.

## Disclaimer

This is an unofficial, non-commercial student project.
It is not affiliated with the Smiski brand.

Focus time measures recorded timer usage rather than
verified productivity.

## Author

Faiza Afreen

Data Science Student | The University of Texas at Dallas
