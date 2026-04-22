"""
Standalone web service runner for Kantech Events Database
Run this to start the web service on port 5000
"""

import sys
from webservice import app
from config import WEBSERVICE_HOST, WEBSERVICE_PORT, WEBSERVICE_DEBUG


if __name__ == "__main__":
    print(f"Starting Kantech WebService on {WEBSERVICE_HOST}:{WEBSERVICE_PORT}")
    print("API Documentation: http://localhost:5000/api/docs")
    print("Press Ctrl+C to stop")
    
    try:
        app.run(
            host=WEBSERVICE_HOST,
            port=WEBSERVICE_PORT,
            debug=WEBSERVICE_DEBUG,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\nWebService stopped.")
        sys.exit(0)
