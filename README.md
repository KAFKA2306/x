# 🚀 Twitter Data Analysis Tool

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![HTMX](https://img.shields.io/badge/HTMX-339933?style=for-the-badge&logo=htmx)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

Analyze your Twitter/X archive with style. Insights into your audience, content performance, and engagement patterns—all offline, private, and fast.

---

## ✨ Features

- **📊 Comprehensive Analytics**:
    - **Activity Heatmaps**: Visualizes daily and hourly tweet patterns.
    - **Content Analysis**: Word clouds and top keyword extraction (TF-IDF).
    - **Type Distribution**: Breakdown of original tweets vs. replies vs. retweets.

- **👥 Audience Insights**:
    - **Top Interactions**: See who you reply to and retweet the most.
    - **Private & Safe**: Works on your local archive (`tweets.js`), no API keys required.

- **💻 Modern Dashboard**:
    - **Web Interface**: Interactive dashboard built with **FastAPI** & **HTMX**.
    - **Instant Reports**: CLI mode for generating static PNG reports in seconds.

---

## 🛠️ Installation

This project handles dependencies with `uv`.

```bash
# Install dependencies
uv sync
```

### 🌐 Web Dashboard

Launch the analytics dashboard:

```bash
task start
# OR
uv run python -m src.main
```

Visit **[http://localhost:8000](http://localhost:8000)** to explore your data.

---

## 📂 Project Structure

```
.
├── src/                # 🧠 Core Logic (Clean Architecture)
│   ├── analytics/      # Interaction & Audience analysis
│   ├── web/            # FastAPI + HTMX Frontend
│   ├── features.py     # Statistical processing
│   └── visualization.py # Chart generation
├── data/               # 📦 Input Data
│   └── tweets.js       # Your Twitter Archive file
├── output/             # 📈 Generated Reports
├── config.yaml         # ⚙️ Configuration
└── Taskfile.yaml       # 📋 Task Runner
```

## 🔧 Configuration

Edit `config.yaml` to point to your Twitter Archive file:

```yaml
# config.yaml
input_file: "path/to/your/tweets.js"
model_name: "gemini-2.5-flash"
```

---

<p align="center">
  <sub>Built with ❤️ by Antigravity. Minimalist, fast, and local-first.</sub>
</p>
