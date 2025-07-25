# 📊 Excel Interview Agent - Streamlit Frontend

A modern, interactive web interface for the AI-powered Excel proficiency assessment system.

## 🚀 Features

### 🎯 **Interactive Assessment**
- **Conversational Interface**: Chat-based Excel interview experience
- **Step-by-Step Guidance**: AI guides users through 5 Excel tasks one by one
- **Real-time Progress Tracking**: Visual progress bar and question counter
- **File Download/Upload**: Seamless sample file download and completed work upload

### 💻 **Modern Web UI**
- **Clean Design**: Professional, responsive Streamlit interface
- **Sidebar Navigation**: Progress tracking, file management, and status updates
- **Chat Interface**: Natural conversation flow with the AI interviewer
- **Error Handling**: Comprehensive error messages and user guidance

### 📈 **Assessment Flow**
1. **Introduction**: AI greets candidate and explains assessment structure
2. **Download Step**: Candidate downloads sample Excel file
3. **5 Excel Tasks**:
   - Basic pivot table creation
   - Chart visualization
   - Advanced pivot analysis
   - Calculated fields & formatting
   - Final file upload
4. **Evaluation**: AI evaluates completed work and provides detailed feedback
5. **PDF Report**: Downloadable assessment summary (if configured)

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- OpenAI API key

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set OpenAI API Key
```bash
# Option 1: Environment variable
export OPENAI_SERVICE_ACCOUNT_KEY="your_openai_api_key_here"

# Option 2: Create .env file
echo "OPENAI_SERVICE_ACCOUNT_KEY=your_openai_api_key_here" > .env
```

### 3. Ensure Sample File Exists
Make sure `dummy_excel_assessment_data.xlsx` is in the project directory.

## 🚀 Running the Application

### Option 1: Quick Start (Recommended)
```bash
python run_streamlit.py
```

### Option 2: Direct Streamlit
```bash
streamlit run streamlit_app.py
```

### Option 3: Custom Port
```bash
streamlit run streamlit_app.py --server.port 8502
```

The application will open in your browser at `http://localhost:8501`

## 📱 User Interface Guide

### Main Interface
- **Chat Area**: Main conversation interface with the AI interviewer
- **Input Box**: Type responses to the AI's questions
- **Progress Bar**: Shows current assessment progress (Question X of 6)

### Sidebar Features
- **Session Info**: Displays unique session ID
- **Progress Tracking**: Visual progress indicator
- **Sample File Download**: One-click download of assessment data
- **File Upload**: Drag-and-drop Excel file upload
- **Status Indicator**: Shows current assessment state

## 🎯 How to Use

### For Candidates:
1. **Open the app** in your browser
2. **Start conversation** by typing your name or greeting
3. **Follow AI guidance** step by step:
   - Download the sample Excel file when prompted
   - Complete each Excel task as requested
   - Upload your completed file at the end
4. **Receive evaluation** and feedback from the AI

### For Administrators:
- **Monitor sessions** through session IDs
- **Review chat logs** for assessment quality
- **Access PDF reports** (if configured)
- **Track user progress** through the interface

## 🔧 Configuration

### Theme Customization
Edit `.streamlit/config.toml` to customize colors and appearance:
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

### Server Settings
```toml
[server]
headless = true
port = 8501
maxUploadSize = 200
```

## 📁 File Structure
```
├── streamlit_app.py          # Main Streamlit application
├── run_streamlit.py          # Launch script with dependency checks
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── config.toml          # Streamlit configuration
├── tool_handlers.py         # Backend tool functions
├── evaluation.py            # Evaluation logic
├── models.py               # Pydantic data models
├── tools.py                # OpenAI tool definitions
├── main.py                 # Command-line interface (optional)
└── dummy_excel_assessment_data.xlsx  # Sample Excel file
```

## 🐛 Troubleshooting

### Common Issues:

**1. "OpenAI API key not found"**
```bash
export OPENAI_SERVICE_ACCOUNT_KEY="your_key_here"
```

**2. "Module not found" errors**
```bash
pip install -r requirements.txt
```

**3. "Sample file not found"**
- Ensure `dummy_excel_assessment_data.xlsx` is in the project directory
- File will still work but users won't be able to download sample data

**4. Upload not working**
- Check file size limits in Streamlit config
- Ensure file is a valid Excel format (.xlsx, .xls, .xlsm)

### Debug Mode:
```bash
streamlit run streamlit_app.py --logger.level debug
```

## 🤝 Integration

### With Existing Systems:
- **API Integration**: Can be embedded in larger assessment platforms
- **Database Storage**: Session data can be logged to databases
- **Authentication**: Can be integrated with SSO/auth systems
- **Reporting**: PDF generation can be customized for branding

### Extending Functionality:
- Add more Excel assessment questions
- Integrate with HR management systems
- Add candidate scoring databases
- Implement advanced analytics

## 📊 Performance

### Optimization Tips:
- Use `@st.cache_data` for large data processing
- Implement session state management for better UX
- Consider WebSocket connections for real-time features

### Resource Usage:
- **Memory**: ~50-100MB per active session
- **CPU**: Low, mainly during AI API calls
- **Network**: Depends on OpenAI API usage

## 🔒 Security

### Best Practices:
- Keep OpenAI API keys secure and never commit to version control
- Implement rate limiting for production use
- Validate all uploaded files for security
- Use HTTPS in production environments

## 📈 Monitoring

### Metrics to Track:
- Session completion rates
- Average assessment time
- File upload success rates
- AI response quality scores

---

## 🎉 Ready to Start!

Run the application and start conducting professional Excel assessments with AI assistance!

```bash
python run_streamlit.py
```

For questions or support, check the logs or review the backend modules for troubleshooting. 