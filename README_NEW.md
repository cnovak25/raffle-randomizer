# 🎯 MVN Great Save Raffle

A modern, celebratory raffle application with authenticated photo access for KPA systems.

## ✨ Features

- 🎊 **Celebratory Effects**: Balloons, snow, and confetti when selecting winners
- 📸 **Authenticated Photo Access**: FastAPI proxy server for KPA photo integration
- 🎯 **Smart Winner Cards**: Auto-generated cards with rotated photos
- 📱 **Mobile Responsive**: Clean, modern interface that works on all devices
- 📋 **CSV Integration**: Direct support for standard column names

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Photo Proxy Server
```bash
python kpa_photo_proxy.py
```

### 3. Run the Raffle App
```bash
streamlit run app.py
```

## 📋 CSV Format

Your CSV file should contain these columns:
- `First Name` - Participant's first name
- `Last Name` - Participant's last name  
- `Location` - Participant's location/office
- `Ticket Level` - Raffle ticket level/type
- `Photo` - KPA photo URL (optional)

## 🔧 Photo Proxy Setup

For KPA photo access:

1. **Extract Session Cookie**: Use browser developer tools to get your KPA session cookie
2. **Update Proxy**: Edit `kpa_photo_proxy.py` with your session cookie
3. **Start Proxy**: Run the proxy server before using the raffle app

## 🎉 Usage

1. Upload your CSV file
2. Check "Use KPA Proxy Server" for photo access
3. Click "Random Selection" 
4. Enjoy the celebration! 🎊
5. Save and share the winner card

## 🛠️ Technical Stack

- **Frontend**: Streamlit with celebratory UI components
- **Backend**: FastAPI proxy server for authentication
- **Image Processing**: PIL with automatic photo rotation
- **Data**: Pandas for CSV processing

## 📁 Project Structure

```
├── app.py                 # Main Streamlit raffle application
├── kpa_photo_proxy.py     # FastAPI proxy for authenticated photos
├── requirements.txt       # Python dependencies
├── Moon Valley Logo.png   # Company logo
└── README.md             # This file
```

## 🎯 Key Components

### Raffle App (`app.py`)
- CSV upload and validation
- Winner selection with celebrations
- Photo-enabled winner card generation
- Mobile-responsive design

### Photo Proxy (`kpa_photo_proxy.py`)  
- Authenticated KPA photo access
- In-memory caching for performance
- Session cookie authentication
- RESTful API endpoint

---

🎊 **Ready to celebrate your next raffle winner!** 🎊
