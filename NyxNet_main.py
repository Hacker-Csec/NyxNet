import os
import sys
import argparse
import hashlib
import time
from pathlib import Path

# Access token file (temporary file created by the loader)
APP_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
ACCESS_TOKEN_FILE = APP_DIR / "access_token.tmp"

def verify_access_token(provided_token):
    """Verify that the provided token matches the one in the temporary file"""
    if not ACCESS_TOKEN_FILE.exists():
        return False
    
    try:
        # Read the token from the file
        with open(ACCESS_TOKEN_FILE, "r") as f:
            stored_token = f.read().strip()
        
        # Verify the token
        return provided_token == stored_token
    except:
        return False

def main():
    """Main application entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="NyxNet Secure Application")
    parser.add_argument("--access-token", help="Access token for authentication")
    args = parser.parse_args()
    
    # Check for access token
    if not args.access_token or not verify_access_token(args.access_token):
        print("Error: Invalid access token. Please use the official NyxNet Loader to start this application.")
        print("This application cannot be started directly.")
        time.sleep(3)  # Give user time to read the message
        sys.exit(1)
    
    # If token is valid, launch the main application
    print("Access token verified. Starting NyxNet...")
    
    # -------------------------------------------------------------------------
    # Here, import and start the actual application code
    # This is where the original chatbox.py code should be imported and executed
    # -------------------------------------------------------------------------
    
    # For this example, we'll just simulate the application
    try:
        from chatbox import Chatbox
        app = Chatbox()
        app.mainloop()
    except ImportError:
        # If chatbox.py is not available, show a placeholder UI
        import tkinter as tk
        from tkinter import messagebox
        import customtkinter as ctk
        
        # Create a placeholder UI
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        app = ctk.CTk()
        app.title("NyxNet")
        app.geometry("800x600")
        
        # Main frame
        main_frame = ctk.CTkFrame(app)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="NyxNet Terminal",
            font=("Arial", 24, "bold"),
            text_color="#00FF00"
        )
        title.pack(pady=20)
        
        # Status message
        status = ctk.CTkLabel(
            main_frame,
            text="Access granted through secure loader. System operational.",
            font=("Arial", 14),
            text_color="#FFFFFF"
        )
        status.pack(pady=10)
        
        # Terminal output simulation
        terminal = ctk.CTkTextbox(
            main_frame,
            font=("Consolas", 12),
            fg_color="#000000",
            text_color="#00FF00",
            height=300
        )
        terminal.pack(fill="both", expand=True, pady=10)
        terminal.insert("1.0", "> System initialized\n> Secure connection established\n> Ready for input\n")
        
        # Input field
        input_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        input_frame.pack(fill="x", pady=10)
        
        input_field = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter command...",
            font=("Consolas", 12),
            height=35,
            width=600
        )
        input_field.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Process command
        def process_command():
            cmd = input_field.get()
            if cmd:
                terminal.insert("end", f"> {cmd}\n")
                terminal.insert("end", f"Processing: {cmd}...\nCommand executed.\n\n")
                terminal.see("end")
                input_field.delete(0, "end")
        
        # Send button
        send_button = ctk.CTkButton(
            input_frame,
            text="Send",
            command=process_command,
            width=100
        )
        send_button.pack(side="right")
        
        # Bind Enter key
        input_field.bind("<Return>", lambda event: process_command())
        
        # Show the application
        app.mainloop()

if __name__ == "__main__":
    main() 