#!/usr/bin/env python3
"""
ICT Inventory - Startup Script with ngrok Support
This script starts the Flask app and automatically sets up ngrok for public access.
"""

import os
import sys
import subprocess
import time
import requests
import webbrowser
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    try:
        import flask
        import pymongo
        import pandas
        import openpyxl
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Please install required packages:")
        print("pip install flask pymongo pandas openpyxl requests")
        return False

def install_ngrok():
    """Install ngrok if not present"""
    try:
        # Check if ngrok is already installed
        result = subprocess.run(["ngrok", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ngrok is already installed")
            return True
    except FileNotFoundError:
        pass
    
    print("📥 ngrok not found. Installing...")
    
    # Download ngrok (Windows)
    try:
        import urllib.request
        ngrok_url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
        zip_path = "ngrok.zip"
        
        print("Downloading ngrok...")
        urllib.request.urlretrieve(ngrok_url, zip_path)
        
        # Extract ngrok
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        # Clean up
        os.remove(zip_path)
        
        # Move ngrok to a better location (optional)
        if os.path.exists("ngrok.exe"):
            print("✅ ngrok installed successfully")
            return True
        else:
            print("❌ Failed to install ngrok")
            return False
            
    except Exception as e:
        print(f"❌ Error installing ngrok: {e}")
        print("Please install ngrok manually from: https://ngrok.com/download")
        return False

def setup_ngrok_auth():
    """Setup ngrok authentication if needed"""
    print("🔐 ngrok Authentication Setup")
    print("For public access, you need to sign up for a free ngrok account:")
    print("1. Go to https://ngrok.com/signup")
    print("2. Create a free account")
    print("3. Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken")
    print("4. Run: ngrok config add-authtoken YOUR_TOKEN")
    print()
    
    auth_token = input("Enter your ngrok authtoken (or press Enter to skip): ").strip()
    if auth_token:
        try:
            subprocess.run(["ngrok", "config", "add-authtoken", auth_token], check=True)
            print("✅ ngrok authentication configured")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to configure ngrok authentication")
            return False
    else:
        print("⚠️  Skipping ngrok authentication (limited functionality)")
        return False

def start_application():
    """Start the Flask application"""
    print("🚀 Starting ICT Inventory Application...")
    
    # Check if app.py exists
    if not os.path.exists("app.py"):
        print("❌ app.py not found in current directory")
        return False
    
    # Start the Flask app
    try:
        subprocess.run([sys.executable, "app.py"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting application: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        return True

def main():
    """Main function"""
    print("="*60)
    print("🏢 ICT Inventory - Public Access Setup")
    print("="*60)
    
    # Check requirements
    if not check_requirements():
        return
    
    # Install ngrok if needed
    if not install_ngrok():
        print("⚠️  Continuing without ngrok (local access only)")
    
    # Setup ngrok authentication
    setup_ngrok_auth()
    
    print("\n" + "="*60)
    print("🎯 Ready to start!")
    print("="*60)
    
    # Start the application
    start_application()

if __name__ == "__main__":
    main() 