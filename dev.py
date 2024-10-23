import os
from app import create_app

if __name__ == '__main__':
    os.environ['FLASK_ENV'] = 'development'
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=8080)
