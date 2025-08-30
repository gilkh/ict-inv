#!/usr/bin/env python3
"""
Script to fix ngrok detection in app.py
"""

import re
import subprocess
import os
import time

def fix_ngrok_detection():
    """Fix the ngrok detection functions in app.py"""
    
    # Read the current app.py file
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the check_ngrok_installed function
    old_check_function = '''def check_ngrok_installed():
        """Check if ngrok is installed"""
        try:
            subprocess.run(["ngrok", "version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False'''
    
    new_check_function = '''def check_ngrok_installed():
        """Check if ngrok is installed"""
        # First check if ngrok is in the current directory
        current_dir_ngrok = os.path.join(os.getcwd(), "ngrok.exe")
        if os.path.exists(current_dir_ngrok):
            print(f"✅ Found ngrok in current directory: {current_dir_ngrok}")
            return True
        
        # Then check if ngrok is in PATH
        try:
            subprocess.run(["ngrok", "version"], capture_output=True, check=True)
            print("✅ Found ngrok in system PATH")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ ngrok not found in PATH")
            return False'''
    
    # Replace the start_ngrok function
    old_start_function = '''def start_ngrok(port):
        """Start ngrok tunnel"""
        try:
            # Kill any existing ngrok processes
            subprocess.run(["taskkill", "/f", "/im", "ngrok.exe"], capture_output=True)
            time.sleep(1)
            
            # Start ngrok
            ngrok_process = subprocess.Popen(
                ["ngrok", "http", str(port), "--log=stdout"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for ngrok to start and get the public URL
            time.sleep(3)
            
            # Try to get the ngrok URL from the API
            try:
                import requests
                response = requests.get("http://localhost:4040/api/tunnels")
                if response.status_code == 200:
                    tunnels = response.json()["tunnels"]
                    if tunnels:
                        public_url = tunnels[0]["public_url"]
                        return public_url, ngrok_process
            except:
                pass
            
            return None, ngrok_process
            
        except Exception as e:
            print(f"Error starting ngrok: {e}")
            return None, None'''
    
    new_start_function = '''def start_ngrok(port):
        """Start ngrok tunnel"""
        try:
            # Kill any existing ngrok processes
            subprocess.run(["taskkill", "/f", "/im", "ngrok.exe"], capture_output=True)
            time.sleep(1)
            
            # Determine ngrok executable path
            current_dir_ngrok = os.path.join(os.getcwd(), "ngrok.exe")
            if os.path.exists(current_dir_ngrok):
                ngrok_cmd = current_dir_ngrok
                print(f"Using ngrok from current directory: {ngrok_cmd}")
            else:
                ngrok_cmd = "ngrok"
                print("Using ngrok from system PATH")
            
            # Start ngrok
            ngrok_process = subprocess.Popen(
                [ngrok_cmd, "http", str(port), "--log=stdout"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for ngrok to start and get the public URL
            time.sleep(3)
            
            # Try to get the ngrok URL from the API
            try:
                import requests
                response = requests.get("http://localhost:4040/api/tunnels")
                if response.status_code == 200:
                    tunnels = response.json()["tunnels"]
                    if tunnels:
                        public_url = tunnels[0]["public_url"]
                        print(f"✅ ngrok tunnel established: {public_url}")
                        return public_url, ngrok_process
            except Exception as e:
                print(f"⚠️  Could not get ngrok URL from API: {e}")
            
            print("⚠️  ngrok started but URL not available yet")
            return None, ngrok_process
            
        except Exception as e:
            print(f"❌ Error starting ngrok: {e}")
            return None, None'''
    
    # Replace the ngrok check line
    old_check_line = "    # Check if ngrok is available\n    ngrok_available = check_ngrok_installed()"
    new_check_line = '''    # Check if ngrok is available
    print("🔍 Checking for ngrok...")
    ngrok_available = check_ngrok_installed()'''
    
    # Update the print_access_info function to include better messaging
    old_print_info = '''        else:
            print(f"\\n⚠️  ngrok not available - only local access")
            print(f"   • Install ngrok for public access: https://ngrok.com/download")'''
    
    new_print_info = '''        else:
            print(f"\\n⚠️  ngrok not available - only local access")
            print(f"   • Install ngrok for public access: https://ngrok.com/download")
            print(f"   • Or place ngrok.exe in the same folder as app.py")'''
    
    # Apply all replacements
    content = content.replace(old_check_function, new_check_function)
    content = content.replace(old_start_function, new_start_function)
    content = content.replace(old_check_line, new_check_line)
    content = content.replace(old_print_info, new_print_info)
    
    # Write the updated content back to app.py
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Successfully updated app.py with fixed ngrok detection!")
    print("🔍 The app will now:")
    print("   • Check for ngrok.exe in the current directory first")
    print("   • Fall back to system PATH if not found locally")
    print("   • Provide better error messages and debugging info")

if __name__ == "__main__":
    fix_ngrok_detection() 