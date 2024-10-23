import os
from app import app  # Import the existing app instance instead of create_app

if __name__ == '__main__':
    os.environ['FLASK_ENV'] = 'development'
    app.run(debug=True, host='0.0.0.0', port=8080)
