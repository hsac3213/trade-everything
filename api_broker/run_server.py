import sys
import os

# Get the parent directory of api_broker
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from api_broker.Server.server import main

if __name__ == "__main__":
    main()