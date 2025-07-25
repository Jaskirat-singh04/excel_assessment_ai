#!/usr/bin/env python3
"""
Launch script for Excel Interview Agent Streamlit App
"""

import os
import subprocess
import sys
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit', 'openai', 'pydantic', 'pandas', 'reportlab'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install missing packages with:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def check_api_key():
    """Check if OpenAI API key is configured"""
    api_key = os.getenv('OPENAI_SERVICE_ACCOUNT_KEY')
    if not api_key:
        print("❌ OpenAI API key not found!")
        print("💡 Set your API key as an environment variable:")
        print("   export OPENAI_SERVICE_ACCOUNT_KEY='your_api_key_here'")
        print("   # or add it to a .env file")
        return False
    
    print("✅ OpenAI API key configured")
    return True

def check_sample_file():
    """Check if sample Excel file exists"""
    sample_file = Path("dummy_excel_assessment_data.xlsx")
    if not sample_file.exists():
        print("⚠️  Sample Excel file 'dummy_excel_assessment_data.xlsx' not found")
        print("💡 Make sure the sample file is in the current directory")
        return False
    
    print("✅ Sample Excel file found")
    return True

def main():
    """Main launcher function"""
    print("🚀 Starting Excel Interview Agent...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check API key
    if not check_api_key():
        sys.exit(1)
    
    # Check sample file
    check_sample_file()  # Warning only, not blocking
    
    print("\n✅ All checks passed!")
    print("🌐 Starting Streamlit app...")
    print("📊 Excel Interview Agent will open in your browser")
    print("=" * 50)
    
    # Launch Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_app.py", 
            "--server.headless", "false"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Excel Interview Agent stopped by user")

if __name__ == "__main__":
    main()