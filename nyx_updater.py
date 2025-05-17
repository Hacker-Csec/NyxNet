import os
import sys
import json
import hashlib
import requests
import zipfile
import tempfile
import subprocess
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from pathlib import Path
import shutil
import time
from datetime import datetime
import uuid
import random
import string

# Configuration
GITHUB_REPO = "Hacker-Csec/NyxNet"
GITHUB_BRANCH = "main"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}"
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"
GITHUB_DOWNLOAD_URL = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/{GITHUB_BRANCH}.zip"

# Authentication
AUTH_PASSWORD = "xyNNet_XOPP^QZKL"

# Local paths
APP_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = APP_DIR / "loader_config.json"
ACCESS_TOKEN_FILE = APP_DIR / "access_token.tmp"
MAIN_EXE = APP_DIR / "NyxNet.exe"
BACKUP_DIR = APP_DIR / "backups"

# Ensure backup directory exists
BACKUP_DIR.mkdir(exist_ok=True)

class LoaderConfig:
    """Handles loader configuration"""
    
    def __init__(self):
        self.config = {
            "last_update_check": None,
            "last_update": None,
            "current_version": "0.0.0",
            "update_channel": "stable",
            "auto_backup": True,
            "auth_hash": hashlib.sha256(AUTH_PASSWORD.encode()).hexdigest()
        }
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    loaded_config = json.load(f)
                    # Update config while preserving auth hash
                    self.config.update(loaded_config)
                    # Ensure auth hash is always correct
                    self.config["auth_hash"] = hashlib.sha256(AUTH_PASSWORD.encode()).hexdigest()
            except Exception as e:
                print(f"Error loading config: {e}")
        else:
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def update_last_check(self):
        """Update the last check timestamp"""
        self.config["last_update_check"] = datetime.now().isoformat()
        self.save_config()
    
    def update_version(self, version):
        """Update the current version"""
        self.config["current_version"] = version
        self.config["last_update"] = datetime.now().isoformat()
        self.save_config()

class AccessTokenManager:
    """Manages temporary access tokens for main application launch"""
    
    @staticmethod
    def generate_token():
        """Generate a unique token for this session"""
        # Create a random token
        random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        time_part = str(int(time.time()))
        hash_base = f"{random_part}_{time_part}_{uuid.uuid4()}"
        token = hashlib.sha256(hash_base.encode()).hexdigest()
        
        # Save the token to a temporary file
        try:
            with open(ACCESS_TOKEN_FILE, "w") as f:
                f.write(token)
            # Set file to delete on application close
            try:
                # Make the file hidden on Windows
                if os.name == 'nt':
                    import ctypes
                    ctypes.windll.kernel32.SetFileAttributesW(str(ACCESS_TOKEN_FILE), 2)  # 2 = Hidden
            except:
                pass
            return token
        except Exception as e:
            print(f"Error generating token: {e}")
            return None
    
    @staticmethod
    def cleanup_token():
        """Remove the access token file"""
        if ACCESS_TOKEN_FILE.exists():
            try:
                os.remove(ACCESS_TOKEN_FILE)
            except:
                pass

class Updater:
    """Main updater functionality"""
    
    def __init__(self):
        self.config = LoaderConfig()
        self.authenticated = False
    
    def authenticate(self, password):
        """Verify the password against the stored hash"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        stored_hash = self.config.config["auth_hash"]
        return password_hash == stored_hash
    
    def check_for_updates(self):
        """Check for updates from GitHub repository"""
        try:
            # Update last check timestamp
            self.config.update_last_check()
            
            # Get repository information from GitHub API
            response = requests.get(GITHUB_API_URL)
            if response.status_code != 200:
                return False, "Failed to connect to update server", None
            
            repo_info = response.json()
            latest_commit = requests.get(f"{GITHUB_API_URL}/commits/{GITHUB_BRANCH}")
            
            if latest_commit.status_code != 200:
                return False, "Failed to get latest version info", None
            
            commit_info = latest_commit.json()
            latest_version = commit_info["sha"][:7]  # Use first 7 chars of commit SHA as version
            current_version = self.config.config["current_version"]
            
            # Check if update is needed
            if latest_version == current_version:
                return False, "NyxNet is up to date", None
            
            # Get update details
            update_details = {
                "version": latest_version,
                "date": commit_info["commit"]["committer"]["date"],
                "message": commit_info["commit"]["message"],
                "author": commit_info["commit"]["author"]["name"],
                "download_url": GITHUB_DOWNLOAD_URL
            }
            
            return True, "Update available", update_details
            
        except Exception as e:
            return False, f"Error checking for updates: {e}", None
    
    def download_update(self, update_details):
        """Download the update package"""
        try:
            # Ensure we're authenticated
            if not self.authenticated:
                return False, "Authentication required"
            
            # Create a temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                zip_path = temp_path / "update.zip"
                
                # Download the zip file
                response = requests.get(update_details["download_url"], stream=True)
                if response.status_code != 200:
                    return False, "Failed to download update package"
                
                # Save the zip file
                with open(zip_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Extract the zip file
                extract_path = temp_path / "extracted"
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(extract_path)
                
                # Find the extracted folder (usually repo-branch)
                extracted_folders = [f for f in extract_path.iterdir() if f.is_dir()]
                if not extracted_folders:
                    return False, "No folders found in the update package"
                
                src_dir = extracted_folders[0]
                
                # Create a backup of the current files
                if self.config.config["auto_backup"]:
                    backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    backup_path = BACKUP_DIR / backup_name
                    backup_path.mkdir(exist_ok=True)
                    
                    # Copy files to backup (exclude some directories)
                    excluded_dirs = [".git", "__pycache__", "backups", "venv", "env", ".idea"]
                    for item in APP_DIR.iterdir():
                        if item.is_dir() and item.name in excluded_dirs:
                            continue
                        if item.is_file() and item.name.startswith("."):
                            continue
                        
                        # Copy file or directory to backup
                        dest_path = backup_path / item.name
                        if item.is_dir():
                            shutil.copytree(item, dest_path, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, dest_path)
                
                # Update the files
                for item in src_dir.iterdir():
                    # Skip some files and directories
                    if item.name in [".git", ".github", "LICENSE", "README.md"]:
                        continue
                    
                    dest_path = APP_DIR / item.name
                    if item.is_dir():
                        # Handle directory replacement
                        if dest_path.exists():
                            # Don't delete some directories
                            if item.name not in ["backups", "venv", "env"]:
                                # Merge directories instead of replacing
                                for sub_item in item.iterdir():
                                    sub_dest = dest_path / sub_item.name
                                    if sub_item.is_dir():
                                        shutil.copytree(sub_item, sub_dest, dirs_exist_ok=True)
                                    else:
                                        shutil.copy2(sub_item, sub_dest)
                        else:
                            # New directory, just copy it
                            shutil.copytree(item, dest_path)
                    else:
                        # Handle file replacement
                        shutil.copy2(item, dest_path)
                
                # Update the current version
                self.config.update_version(update_details["version"])
                
                return True, "Update installed successfully"
                
        except Exception as e:
            return False, f"Error during update installation: {e}"
    
    def launch_main_application(self):
        """Launch the main NyxNet application with access token"""
        if not self.authenticated:
            return False, "Authentication required"
            
        # Check if the main exe exists
        if not MAIN_EXE.exists():
            return False, "NyxNet.exe not found"
        
        try:
            # Generate access token
            token = AccessTokenManager.generate_token()
            if not token:
                return False, "Failed to generate access token"
            
            # Launch the main application with the token as an argument
            subprocess.Popen([str(MAIN_EXE), f"--access-token={token}"])
            
            return True, "NyxNet launched successfully"
            
        except Exception as e:
            AccessTokenManager.cleanup_token()
            return False, f"Error launching NyxNet: {e}"

class UpdaterApp(ctk.CTk):
    """GUI for the loader application"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize updater
        self.updater = Updater()
        
        # Configure window
        self.title("NyxNet Secure Loader")
        self.geometry("500x600")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Apply dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Create UI elements
        self.create_widgets()
        
        # Show login screen first
        self.show_login_screen()
    
    def create_widgets(self):
        """Create all UI elements"""
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Login frame
        self.login_frame = ctk.CTkFrame(self.main_frame)
        
        # Login elements
        self.login_title = ctk.CTkLabel(
            self.login_frame, 
            text="NyxNet Secure Loader",
            font=("Arial", 20, "bold"),
            text_color="#FF3333"
        )
        self.login_title.pack(pady=(20, 10))
        
        self.login_subtitle = ctk.CTkLabel(
            self.login_frame,
            text="Authentication required",
            font=("Arial", 12),
            text_color="#CCCCCC"
        )
        self.login_subtitle.pack(pady=(0, 20))
        
        self.password_entry = ctk.CTkEntry(
            self.login_frame,
            placeholder_text="Password",
            font=("Arial", 12),
            show="•",
            width=300,
            height=40
        )
        self.password_entry.pack(pady=10)
        self.password_entry.bind("<Return>", lambda event: self.login())
        
        self.login_button = ctk.CTkButton(
            self.login_frame,
            text="AUTHENTICATE",
            command=self.login,
            font=("Arial", 12, "bold"),
            height=40,
            width=300,
            fg_color="#FF3333",
            hover_color="#CC0000"
        )
        self.login_button.pack(pady=10)
        
        self.login_status = ctk.CTkLabel(
            self.login_frame,
            text="",
            font=("Arial", 12),
            text_color="#FF0000"
        )
        self.login_status.pack(pady=10)
        
        # Main launcher frame (hidden initially)
        self.launcher_frame = ctk.CTkFrame(self.main_frame)
        
        # Header
        self.header_frame = ctk.CTkFrame(self.launcher_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 20))
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="NyxNet Control Panel",
            font=("Arial", 24, "bold"),
            text_color="#FF3333"
        )
        self.title_label.pack(side="left", padx=10)
        
        # Status section
        self.status_frame = ctk.CTkFrame(self.launcher_frame)
        self.status_frame.pack(fill="x", pady=10, padx=10)
        
        self.current_version_label = ctk.CTkLabel(
            self.status_frame,
            text=f"Current Version: {self.updater.config.config['current_version']}",
            font=("Arial", 12),
            anchor="w"
        )
        self.current_version_label.pack(fill="x", padx=10, pady=(10, 0), anchor="w")
        
        last_check = self.updater.config.config["last_update_check"]
        last_check_text = "Never" if not last_check else datetime.fromisoformat(last_check).strftime("%Y-%m-%d %H:%M:%S")
        self.last_check_label = ctk.CTkLabel(
            self.status_frame,
            text=f"Last Check: {last_check_text}",
            font=("Arial", 12),
            anchor="w"
        )
        self.last_check_label.pack(fill="x", padx=10, pady=(5, 10), anchor="w")
        
        # Action buttons
        self.buttons_frame = ctk.CTkFrame(self.launcher_frame, fg_color="transparent")
        self.buttons_frame.pack(fill="x", pady=10)
        
        self.launch_button = ctk.CTkButton(
            self.buttons_frame,
            text="LAUNCH NYXNET",
            command=self.launch_nyxnet,
            font=("Arial", 14, "bold"),
            height=50,
            fg_color="#00CC00",
            hover_color="#00AA00"
        )
        self.launch_button.pack(fill="x", padx=10, pady=5)
        
        self.check_button = ctk.CTkButton(
            self.buttons_frame,
            text="Check for Updates",
            command=self.check_updates,
            font=("Arial", 12),
            height=40,
            fg_color="#3366FF",
            hover_color="#2E5CE6"
        )
        self.check_button.pack(fill="x", padx=10, pady=5)
        
        # Update details frame (shown when update is available)
        self.update_details_frame = ctk.CTkFrame(self.launcher_frame)
        
        self.update_title = ctk.CTkLabel(
            self.update_details_frame,
            text="Update Available",
            font=("Arial", 16, "bold"),
            text_color="#00CC00"
        )
        self.update_title.pack(pady=(10, 5))
        
        self.update_info = ctk.CTkTextbox(
            self.update_details_frame,
            font=("Arial", 12),
            height=150,
            width=450,
            wrap="word"
        )
        self.update_info.pack(padx=10, pady=10, fill="both", expand=True)
        self.update_info.configure(state="disabled")
        
        self.update_button = ctk.CTkButton(
            self.update_details_frame,
            text="Install Update",
            command=self.install_update,
            font=("Arial", 12, "bold"),
            height=40,
            fg_color="#00CC00",
            hover_color="#00AA00"
        )
        self.update_button.pack(pady=10, padx=10, fill="x")
        
        # Progress section (shown during update)
        self.progress_frame = ctk.CTkFrame(self.launcher_frame)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Installing Update...",
            font=("Arial", 14)
        )
        self.progress_label.pack(pady=(10, 5))
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=400)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        self.progress_status = ctk.CTkLabel(
            self.progress_frame,
            text="Preparing...",
            font=("Arial", 12)
        )
        self.progress_status.pack(pady=5)
        
        # Status section at bottom
        self.footer_frame = ctk.CTkFrame(self.launcher_frame, fg_color="transparent")
        self.footer_frame.pack(fill="x", side="bottom", pady=10)
        
        self.status_label = ctk.CTkLabel(
            self.footer_frame,
            text="Ready to launch",
            font=("Arial", 12),
            text_color="#CCCCCC"
        )
        self.status_label.pack(side="left", padx=10)
        
        self.quit_button = ctk.CTkButton(
            self.footer_frame,
            text="Quit",
            command=self.on_close,
            font=("Arial", 12),
            height=30,
            width=80,
            fg_color="#666666",
            hover_color="#444444"
        )
        self.quit_button.pack(side="right", padx=10)
    
    def show_login_screen(self):
        """Show the login screen"""
        # Hide other frames
        if hasattr(self, 'launcher_frame'):
            self.launcher_frame.pack_forget()
        
        # Show login frame
        self.login_frame.pack(fill="both", expand=True)
        
        # Focus on password entry
        self.password_entry.focus_set()
    
    def show_launcher_screen(self):
        """Show the main launcher screen"""
        # Hide login frame
        self.login_frame.pack_forget()
        
        # Show launcher frame
        self.launcher_frame.pack(fill="both", expand=True)
        
        # Update version display
        self.current_version_label.configure(text=f"Current Version: {self.updater.config.config['current_version']}")
        
        # Update last check display
        last_check = self.updater.config.config["last_update_check"]
        last_check_text = "Never" if not last_check else datetime.fromisoformat(last_check).strftime("%Y-%m-%d %H:%M:%S")
        self.last_check_label.configure(text=f"Last Check: {last_check_text}")
    
    def login(self):
        """Handle login attempt"""
        password = self.password_entry.get()
        if not password:
            self.login_status.configure(text="Please enter a password")
            return
        
        # Authenticate
        if self.updater.authenticate(password):
            self.updater.authenticated = True
            self.show_launcher_screen()
            
            # Check for main exe
            if not MAIN_EXE.exists():
                self.status_label.configure(text="Warning: NyxNet.exe not found. Please update first.", text_color="#FFAA00")
                self.launch_button.configure(state="disabled")
            
        else:
            self.login_status.configure(text="Invalid password. Please try again.")
            self.password_entry.delete(0, "end")
    
    def check_updates(self):
        """Check for updates"""
        self.status_label.configure(text="Checking for updates...")
        self.update_details_frame.pack_forget()
        
        # Clear previous update info
        self.update_info.configure(state="normal")
        self.update_info.delete("1.0", "end")
        self.update_info.configure(state="disabled")
        
        # Check for updates
        has_update, message, update_details = self.updater.check_for_updates()
        
        # Update last check display
        last_check = self.updater.config.config["last_update_check"]
        last_check_text = datetime.fromisoformat(last_check).strftime("%Y-%m-%d %H:%M:%S")
        self.last_check_label.configure(text=f"Last Check: {last_check_text}")
        
        if has_update:
            # Show update details
            self.update_details_frame.pack(fill="both", expand=True, pady=10, padx=10)
            
            # Format update info
            update_info = f"""
Version: {update_details['version']}
Date: {update_details['date']}
Author: {update_details['author']}

Update Description:
{update_details['message']}
            """
            
            # Update the info display
            self.update_info.configure(state="normal")
            self.update_info.insert("1.0", update_info)
            self.update_info.configure(state="disabled")
            
            # Store update details for later
            self.current_update = update_details
            
            self.status_label.configure(text="Update available. Click 'Install Update' to install.")
        else:
            # No update available
            self.status_label.configure(text=message)
    
    def install_update(self):
        """Install the available update"""
        # Show progress
        self.update_details_frame.pack_forget()
        self.progress_frame.pack(fill="x", pady=10, padx=10)
        self.progress_bar.set(0.1)
        self.progress_status.configure(text="Downloading update...")
        
        # Run the update in a separate thread to keep UI responsive
        def update_thread():
            # Update progress
            self.progress_bar.set(0.3)
            self.progress_status.configure(text="Installing update...")
            
            # Install update
            success, message = self.updater.download_update(self.current_update)
            
            # Update UI
            if success:
                self.progress_bar.set(1.0)
                self.progress_status.configure(text="Update installed successfully!")
                
                # Update version display
                self.current_version_label.configure(text=f"Current Version: {self.updater.config.config['current_version']}")
                
                # Show completion message
                messagebox.showinfo("Update Complete", "The update has been installed successfully.")
                
                # Hide progress
                self.progress_frame.pack_forget()
                self.status_label.configure(text="Update installed successfully.")
                
                # Enable launch button if it was disabled
                if not MAIN_EXE.exists():
                    self.status_label.configure(text="Warning: NyxNet.exe still not found.", text_color="#FFAA00")
                    self.launch_button.configure(state="disabled")
                else:
                    self.launch_button.configure(state="normal")
            else:
                self.progress_bar.set(0)
                self.progress_status.configure(text=f"Error: {message}")
                
                # Show error message
                messagebox.showerror("Update Failed", f"Failed to install the update: {message}")
                
                # Hide progress
                self.progress_frame.pack_forget()
                self.status_label.configure(text=f"Update failed: {message}")
        
        # Start update thread
        import threading
        update_thread = threading.Thread(target=update_thread)
        update_thread.daemon = True
        update_thread.start()
    
    def launch_nyxnet(self):
        """Launch the main NyxNet application"""
        success, message = self.updater.launch_main_application()
        
        if success:
            self.status_label.configure(text="NyxNet launched successfully", text_color="#00CC00")
            # Minimize the loader window
            self.iconify()
        else:
            self.status_label.configure(text=f"Error: {message}", text_color="#FF0000")
            messagebox.showerror("Launch Failed", message)
    
    def on_close(self):
        """Handle window close event"""
        # Clean up the access token file
        AccessTokenManager.cleanup_token()
        self.destroy()

def main():
    app = UpdaterApp()
    app.mainloop()

if __name__ == "__main__":
    main() 