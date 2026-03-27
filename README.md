# 📊 PolitiScope — Social Media Analysis Dashboard

A web-based tool for analyzing politician social media posts during election periods. Upload CSV datasets and get instant **Exploratory Data Analysis (EDA)**, **actionable insights**, **interactive visualizations**, and a **comprehensive printable report**.

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Interactive_Charts-3F4F75?logo=plotly&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🚀 Features

- **CSV Upload** — Drag-and-drop or browse to upload your dataset
- **Dataset Overview** — Total posts, engagement stats, platform & post type breakdowns, top channels
- **Key Insights** — Auto-generated findings on misinformation, hate speech, tone, campaign narratives, target groups, electoral integrity, and gender dynamics
- **10+ Interactive Charts** — Platform distribution, engagement timelines, tag distributions, heatmaps, radar charts, sunbursts, box plots, and more
- **Full Report** — Printable report with summary, findings, tag breakdowns, charts, and recommendations

---

## 🗂️ Project Structure

```
socialMedia/
├── app.py                  # Flask backend (CSV parsing, EDA, chart generation)
├── README.md
├── requirements.txt
└── static/
    ├── index.html          # Main HTML page
    ├── styles.css          # Dark-themed CSS design system
    └── app.js              # Frontend logic (upload, rendering, navigation)
```

---

## 📋 Prerequisites

- **Python 3.8+** — [Download Python](https://www.python.org/downloads/)
- **pip** — Comes bundled with Python
- **Git** — [Download Git](https://git-scm.com/downloads)

---

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/aad4rsh/SocialMedia.git
cd SocialMedia
```

### 2. (Optional) Create a Virtual Environment

It's recommended to use a virtual environment to avoid dependency conflicts.

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install flask pandas plotly seaborn scipy
```

Or if a `requirements.txt` is available:
```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

You should see output like:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### 5. Open in Browser

Open your browser and navigate to:

```
http://127.0.0.1:5000
```

---

## 📖 How to Use

1. **Upload CSV** — Drag and drop your CSV file onto the upload zone, or click to browse
2. **Click "Analyze Data"** — The app will parse your data and generate all analyses
3. **Navigate Tabs** — Use the top navigation to switch between:
   - **Overview** — Dataset stats, platform distribution, top channels
   - **Insights** — Auto-generated key findings with severity indicators
   - **Charts** — All interactive Plotly visualizations
   - **Report** — Complete analysis report with recommendations
4. **Print Report** — Click the "Print Report" button to save/print the full report

---

## 📊 Expected CSV Format

The CSV should be **tab-separated** (TSV) or **comma-separated** (CSV) with the following columns:

### Core Columns

| Column | Description |
|--------|-------------|
| `PostId` | Unique identifier for each post |
| `Platform` | Social media platform (Facebook, YouTube, TikTok, etc.) |
| `ChannelName` | Name of the politician/channel |
| `PublishedAt` | Post publish date (UTC) |
| `LikesCount` | Number of likes |
| `SharesCount` | Number of shares |
| `CommentsCount` | Number of comments |
| `ViewsCount` | Number of views |
| `PostType` | Type of post (status, video, photo, etc.) |
| `Description` | Post text content |

### Tag Columns (Binary: 0 or 1)

The dataset includes binary tag columns across these categories:

| Category | Tags |
|----------|------|
| **Misinformation** | False Claim, Altered Content, Coordinated Content |
| **Hate Speech** | Targeted Attack, Hate Incitement |
| **Electoral Integrity** | Fraud, Early Results, Attack Election Commission, Discredit Process |
| **Gender & Inclusion** | Attacks on Women, Representation, Digital Barriers, Inclusion Policy |
| **Target Group** | Women, Dalits, Janajati, Madheshi, Religious Minorities, Journalists, etc. |
| **Content Type** | Text Post, Image, Video, AI/Deepfake, Edited/Repurposed |
| **Tone** | Positive, Neutral, Negative, Aggressive, Fear-based, Emotional, Informational |
| **Campaign Narrative** | Policy-based, Issue-based, Attack on Opponent, Nationalism, Religious Appeal, etc. |
| **Political Party** | RSP, UML, Congress, NCP, Others |
| **Issue Area** | Health, Education, Employment, Security, Environment, etc. |

---

## 🧰 Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Python, Flask |
| **Data Analysis** | Pandas, NumPy |
| **Charts** | Plotly (server-side generation + client-side rendering) |
| **Frontend** | HTML5, CSS3 (vanilla), JavaScript (vanilla) |
| **Fonts** | Inter, JetBrains Mono (Google Fonts) |

---

## 🛑 Troubleshooting

| Issue | Solution |
|-------|----------|
| **CSS/JS not loading** | Make sure `styles.css` and `app.js` are inside the `static/` folder |
| **Port 5000 in use** | Change the port in `app.py`: `app.run(port=5001)` |
| **CSV parsing error** | Ensure your CSV is tab-separated or comma-separated with proper headers |
| **Module not found** | Run `pip install flask pandas plotly seaborn scipy` |
| **Large file timeout** | The app supports files up to 50MB; ensure your dataset is within limits |

---

## 📄 License

This project is for research and educational purposes.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request
