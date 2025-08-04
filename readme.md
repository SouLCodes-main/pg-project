# 🏗️ Construction Materials Tracker

Track construction materials, costs, and inventory across multiple sites with data visualization and filtering capabilities.

## ✨ Features

- 📝 Add material records with dates and costs
- 📊 Interactive charts and analytics
- 🔍 Filter and sort by site, date, material type
- 💾 Export data to CSV/Excel
- 📱 Responsive design

## 🛠️ Tech Stack

- **Backend**: Flask, Pandas, Matplotlib
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: SQLite

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/construction-materials-tracker.git
cd construction-materials-tracker
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install and run
pip install -r requirements.txt
python init_db.py
python app.py
```

Visit `http://localhost:5000` 🌐

## 📁 Project Structure

```
├── app.py                 # Main Flask app
├── requirements.txt       # Dependencies
├── static/               # CSS, JS, images
├── templates/            # HTML templates
├── data/                 # Database and exports
└── utils/                # Helper modules
```

## 📦 Dependencies

```
Flask==2.3.3
pandas==2.1.0
matplotlib==3.7.2
plotly==5.15.0
SQLAlchemy==2.0.20
```

## 🎯 Usage

1. **Add Materials** 📝 - Enter material details, costs, and dates
2. **View Records** 📋 - Filter and sort material data
3. **Analytics** 📊 - View cost breakdowns and trends
4. **Export** 💾 - Download filtered data

## 🗄️ Database Schema

**Materials Table:**
- `material_name`, `site_location`, `quantity`, `unit`
- `cost_per_unit`, `total_cost`, `date_used`
- `supplier`, `notes`, `created_at`

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Homepage |
| POST | `/add` | Add material |
| GET | `/records` | View records |
| GET | `/dashboard` | Analytics |
| GET | `/export/<format>` | Export data |

## 🚀 Production Setup

```env
FLASK_ENV=production
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///data/materials.db
```

## 📄 License

MIT License

---

**Made with ❤️ for construction management**
