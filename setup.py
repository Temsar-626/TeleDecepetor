#!/usr/bin/env python3

import os
import subprocess
import sys

def execute_setup():
    """Execute main.py to set up and run the TeleDeceptor project."""
    try:
        # Run main.py
        subprocess.run([sys.executable, "main.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during setup: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nSetup interrupted by user.")
        sys.exit(1)

if __name__ == "__main__":
    print("Starting TeleDeceptor setup...")
    execute_setup()
