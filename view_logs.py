#!/usr/bin/env python3
"""
Real-time log viewer for restaurant agent
Shows only agent and customer conversations
"""
import sys
import time
from pathlib import Path

def tail_log(filename='restaurant_agent.log', n_lines=50):
    """Tail the log file and show conversation"""
    log_file = Path(filename)
    
    if not log_file.exists():
        print(f"❌ Log file not found: {filename}")
        print("💡 Start the agent first: python restaurant_main.py dev")
        return
    
    print("="*80)
    print("🎤 RESTAURANT AGENT CONVERSATION LOG")
    print("="*80)
    print("👤 = Customer speaks")
    print("🗣️  = Agent speaks")
    print("="*80)
    print()
    
    # Show last n lines first
    with open(log_file, 'r') as f:
        lines = f.readlines()
        for line in lines[-n_lines:]:
            print_if_relevant(line)
    
    # Follow new lines
    print("\n📡 Watching for new conversations...\n")
    with open(log_file, 'r') as f:
        # Move to end of file
        f.seek(0, 2)
        
        while True:
            line = f.readline()
            if line:
                print_if_relevant(line)
            else:
                time.sleep(0.1)

def print_if_relevant(line):
    """Print only conversation-relevant lines"""
    line = line.strip()
    
    # Agent speaking
    if "🗣️" in line or "AGENT SAID:" in line:
        # Extract just the message part
        if "AGENT SAID:" in line:
            parts = line.split("AGENT SAID:", 1)
            if len(parts) > 1:
                print(f"🗣️  {parts[1].strip()}")
        else:
            print(line)
    
    # Customer speaking
    elif "👤" in line or "Customer said:" in line:
        if "Customer said:" in line:
            parts = line.split("Customer said:", 1)
            if len(parts) > 1:
                print(f"👤 {parts[1].strip()}")
        else:
            print(line)
    
    # Transfers and important events
    elif any(x in line for x in ["Entering", "transferring", "Order confirmed", "Added", "Removed"]):
        print(f"ℹ️  {line}")
    
    # Menu searches
    elif "Searching for item:" in line:
        parts = line.split("Searching for item:", 1)
        if len(parts) > 1:
            print(f"🔍 {parts[1].strip()}")
    
    # Errors
    elif "ERROR" in line or "❌" in line:
        print(f"❌ {line}")

if __name__ == "__main__":
    try:
        tail_log()
    except KeyboardInterrupt:
        print("\n\n👋 Stopped watching logs")
        sys.exit(0)

