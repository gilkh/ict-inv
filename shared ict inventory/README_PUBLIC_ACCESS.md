# ICT Inventory - Public Access Setup

This guide will help you set up your ICT Inventory application to be accessible from anywhere using ngrok.

## 🚀 Quick Start (Windows)

### Option 1: One-Click Start (Recommended)
1. Double-click `start_public.bat`
2. Follow the prompts to set up ngrok
3. The app will start automatically with public access

### Option 2: Manual Setup
1. Run `python start_with_ngrok.py`
2. Follow the setup instructions
3. The app will start with ngrok tunnel

## 📋 Prerequisites

### Required Software
- **Python 3.7+** - [Download here](https://python.org/downloads/)
- **MongoDB** - Running locally or cloud instance
- **ngrok** - Will be installed automatically (or [manual install](https://ngrok.com/download))

### Python Packages
All required packages will be installed automatically, but you can also install them manually:
```bash
pip install -r requirements.txt
```

## 🔧 Setup Instructions

### 1. Install Dependencies
```bash
# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install requirements
pip install -r requirements.txt
```

### 2. Configure MongoDB
Make sure MongoDB is running and accessible. The app will connect to:
- **Local MongoDB**: `mongodb://localhost:27017`
- **Database**: `afrahkoum`
- **Collection**: `ict_inventory`

### 3. Set up ngrok (Free Account)
1. Go to [ngrok.com/signup](https://ngrok.com/signup)
2. Create a free account
3. Get your authtoken from [dashboard.ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken)
4. The setup script will prompt you for this token

## 🎯 Running the Application

### Method 1: Using the Batch File (Windows)
```bash
start_public.bat
```

### Method 2: Using the Python Script
```bash
python start_with_ngrok.py
```

### Method 3: Direct Python Execution
```bash
python app.py
```

## 🌐 Access URLs

When the app starts, you'll see output like this:

```
============================================================
🚀 ICT Inventory Application Started!
============================================================
📱 Local Access:
   • http://localhost:5000
   • http://192.168.1.100:5000

🌐 Public Access (via ngrok):
   • https://abc123.ngrok.io

💡 You can now access the app from anywhere!
   • Share the ngrok URL with others
   • The URL will work on any device with internet

🔐 Login Credentials:
   • Admin: admin / admin123
   • User: user / user123
============================================================
```

## 🔐 Login Credentials

- **Admin Access**: `admin` / `admin123`
  - Full access to all features
  - Can edit, delete, add records
  - User management capabilities
  
- **User Access**: `user` / `user123`
  - Read-only access
  - Can view and filter data
  - No editing capabilities

## 📱 Access from Anywhere

### Local Network Access
- **Same computer**: `http://localhost:5000`
- **Same network**: `http://YOUR_LOCAL_IP:5000`

### Public Internet Access
- **ngrok URL**: `https://abc123.ngrok.io` (changes each time)
- **Share with others**: Anyone with the ngrok URL can access your app
- **Mobile devices**: Works on phones, tablets, etc.

## 🔧 Configuration Options

### Environment Variables
You can set these environment variables to customize the app:

```bash
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=afrahkoum
MONGO_COLLECTION_NAME=ict_inventory

# Flask Configuration
SECRET_KEY=your-secret-key-change-this-in-production
```

### Port Configuration
To change the port, edit the `PORT` variable in `app.py`:
```python
PORT = 8080  # Change to your preferred port
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. ngrok Not Found
```
❌ ngrok not found. Installing...
```
- The script will automatically download and install ngrok
- If it fails, manually install from [ngrok.com/download](https://ngrok.com/download)

#### 2. MongoDB Connection Error
```
Error connecting to MongoDB: [Errno 61] Connection refused
```
- Make sure MongoDB is running
- Check if the connection string is correct
- Verify firewall settings

#### 3. Port Already in Use
```
Error: [Errno 48] Address already in use
```
- Change the port in `app.py`
- Or kill the process using the port:
  ```bash
  # Windows
  netstat -ano | findstr :5000
  taskkill /PID <PID> /F
  
  # Mac/Linux
  lsof -ti:5000 | xargs kill -9
  ```

#### 4. ngrok Authentication Required
```
Error: Your account is limited to 1 simultaneous ngrok client session
```
- Sign up for a free ngrok account
- Add your authtoken: `ngrok config add-authtoken YOUR_TOKEN`

### Getting Help

1. **Check the console output** for error messages
2. **Verify MongoDB is running** and accessible
3. **Ensure all dependencies are installed**
4. **Check firewall settings** if accessing from other devices

## 🔒 Security Considerations

### For Production Use
1. **Change default passwords** in the `USERS` dictionary
2. **Use environment variables** for sensitive data
3. **Enable HTTPS** for secure connections
4. **Implement proper authentication** (OAuth, LDAP, etc.)
5. **Set up proper MongoDB authentication**
6. **Use a production WSGI server** (Gunicorn, uWSGI)

### Current Security Features
- Session-based authentication
- Role-based access control (Admin/User)
- Location-based data filtering
- Column-level permissions
- CSRF protection (Flask built-in)

## 📞 Support

If you encounter issues:
1. Check the console output for error messages
2. Verify all prerequisites are met
3. Ensure MongoDB is running and accessible
4. Check network connectivity and firewall settings

## 🎉 Success!

Once everything is set up, you'll have:
- ✅ Local access to your ICT Inventory
- ✅ Public access via ngrok URL
- ✅ Ability to share with others
- ✅ Mobile device compatibility
- ✅ Secure login system

Your ICT Inventory is now accessible from anywhere in the world! 🌍 