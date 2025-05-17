"""
This script adds security token verification to chatbox.py
Run this once to modify the original chatbox.py file
"""

import os
import sys
from pathlib import Path

def add_security_to_chatbox():
    """Add security token verification to chatbox.py"""
    
    # Path to the chatbox.py file
    chatbox_path = Path(os.path.dirname(os.path.abspath(__file__))) / "chatbox.py"
    
    if not chatbox_path.exists():
        print(f"Error: {chatbox_path} not found")
        return False
    
    # Read the original file
    with open(chatbox_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if security is already added
    if "verify_access_token" in content:
        print("Security verification already added to chatbox.py")
        return True
    
    # Security code to add at the beginning
    security_code = """
import argparse
import sys
from pathlib import Path

# Security check - verify access token
def verify_access_token():
    \"\"\"Verify that the application was launched with a valid access token\"\"\"
    # Check command line arguments
    parser = argparse.ArgumentParser(description="NyxNet Secure Application")
    parser.add_argument("--access-token", help="Access token for authentication")
    args, unknown = parser.parse_known_args()
    
    # Check for access token
    if not args.access_token:
        print("Error: No access token provided. Please use the official NyxNet Loader.")
        sys.exit(1)
    
    # Verify token against temporary file
    token_file = Path(os.path.dirname(os.path.abspath(__file__))) / "access_token.tmp"
    if not token_file.exists():
        print("Error: Invalid launch method. Please use the official NyxNet Loader.")
        sys.exit(1)
    
    try:
        with open(token_file, "r") as f:
            stored_token = f.read().strip()
        
        if args.access_token != stored_token:
            print("Error: Invalid access token. Please use the official NyxNet Loader.")
            sys.exit(1)
    except:
        print("Error: Could not verify access token. Please use the official NyxNet Loader.")
        sys.exit(1)
    
    # Token is valid, continue with application
    print("Access granted. Welcome to NyxNet.")

"""
    
    # Find where to insert the security code
    import_section_end = content.find("# Import login system")
    if import_section_end == -1:
        import_section_end = content.find("from io import BytesIO")
        if import_section_end == -1:
            # Just add after the first few imports
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if i > 10 and not line.startswith("import") and not line.startswith("from"):
                    import_section_end = content.find(line)
                    break
    
    if import_section_end == -1:
        print("Could not find a suitable place to insert security code")
        return False
    
    # Find the main code after if __name__ == "__main__":
    main_section = content.find('if __name__ == "__main__":')
    if main_section == -1:
        print("Could not find main section in chatbox.py")
        return False
    
    # Find the first code line after if __name__ == "__main__":
    main_code_start = content.find("\n", main_section) + 1
    while content[main_code_start:main_code_start+1].isspace():
        main_code_start = content.find("\n", main_code_start) + 1
    
    # Insert the security check into the main section
    security_check = "    # Verify access token before starting\n    verify_access_token()\n    \n"
    
    # Create the modified content
    modified_content = (
        content[:import_section_end] + 
        security_code + 
        content[import_section_end:main_code_start] + 
        security_check + 
        content[main_code_start:]
    )
    
    # Backup the original file
    backup_path = chatbox_path.with_suffix(".py.bak")
    if not backup_path.exists():
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created backup: {backup_path}")
    
    # Write the modified file
    with open(chatbox_path, "w", encoding="utf-8") as f:
        f.write(modified_content)
    
    print(f"Successfully added security to {chatbox_path}")
    return True

if __name__ == "__main__":
    add_security_to_chatbox() 