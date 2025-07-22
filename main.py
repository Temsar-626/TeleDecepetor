import os
import subprocess
import sys
import time

def run_command(command, error_message=None):
    """Run a shell command and handle errors."""
    try:
        process = subprocess.run(command, check=True, text=True, capture_output=True)
        print(process.stdout)
        return True
    except subprocess.CalledProcessError as e:
        if error_message:
            print(f"Error: {error_message}")
        print(f"Command failed: {' '.join(command)}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def clone_repository():
    """Clone the TeleDeceptor repository."""
    repo_url = "https://github.com/Temsar-626/TeleDecepetor"
    clone_dir = "TeleDecepetor"
    
    # Check if directory already exists
    if os.path.exists(clone_dir):
        print(f"Repository already cloned at {clone_dir}")
        return True
    
    print(f"Cloning repository from {repo_url}...")
    return run_command(
        ["git", "clone", repo_url], 
        "Failed to clone repository"
    )

def install_dependencies():
    """Install dependencies using pip."""
    repo_dir = "TeleDecepetor"
    
    if not os.path.exists(repo_dir):
        print("Repository directory not found. Clone the repository first.")
        return False
    
    print("Installing dependencies...")
    os.chdir(repo_dir)
    
    # Check for requirements.txt
    requirements_file = "requirements.txt"
    if os.path.exists(requirements_file):
        return run_command(
            [sys.executable, "-m", "pip", "install", "-r", requirements_file],
            "Failed to install dependencies from requirements.txt"
        )
    else:
        print("No requirements.txt found. Installing common Telegram bot dependencies...")
        # Install common Telegram bot libraries
        return run_command(
            [sys.executable, "-m", "pip", "install", "python-telegram-bot", "requests"],
            "Failed to install common dependencies"
        )

def run_application():
    """Run the app.py file."""
    app_file = "app.py"
    
    if not os.path.exists(app_file):
        print(f"Application file {app_file} not found.")
        return False
    
    print(f"Running {app_file}...")
    
    # Use subprocess.Popen to keep the app running
    try:
        process = subprocess.Popen([sys.executable, app_file])
        return True
    except Exception as e:
        print(f"Error running application: {str(e)}")
        return False

def make_replit_adjustments():
    """Make any necessary adjustments for Replit compatibility."""
    print("Checking for necessary Replit adjustments...")
    
    # Create .replit file if it doesn't exist
    replit_file = "../.replit"
    if not os.path.exists(replit_file):
        with open(replit_file, "w") as f:
            f.write("""run = "cd TeleDecepetor && python app.py"
language = "python3"
""")
        print("Created .replit configuration file.")
    
    # Check if we have a TOKEN or API_KEY variable that needs to be set
    if not os.path.exists("app.py"):
        print("Warning: app.py not found, cannot check for token requirements.")
        return
    
    with open("app.py", "r") as f:
        content = f.read()
        
    # Check if the app might be looking for a token
    token_checks = ["TOKEN", "API_KEY", "BOT_TOKEN", "TELEGRAM_TOKEN"]
    for token_var in token_checks:
        if token_var in content and not os.environ.get(token_var):
            print(f"Warning: The application may require a {token_var} environment variable.")
            print(f"Please set this in the Replit Secrets tab if the application fails to run.")

def main():
    print("Setting up TeleDeceptor Python project from GitHub on Replit")
    
    # Step 1: Clone the repository
    if not clone_repository():
        print("Failed to clone repository. Exiting.")
        return
    
    # Step 2: Install dependencies
    if not install_dependencies():
        print("Failed to install dependencies. Exiting.")
        return
        
    # Step 3: Make Replit adjustments
    make_replit_adjustments()
    
    # Step 4: Run the application
    if not run_application():
        print("Failed to run the application.")
        return
    
    print("\nSetup completed successfully! The application should be running now.")
    print("If the application requires a Telegram bot token or other credentials,")
    print("please set them in the Replit Secrets tab.")
    
    # Keep the script running so the subprocess keeps running
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
