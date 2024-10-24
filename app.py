import os
import sys
from base_app import create_base_app
from blueprints.analyzer import analyzer


app = create_base_app()
app.register_blueprint(analyzer)


if __name__ == '__main__':
    # Only use this for development
    if os.environ.get('FLASK_ENV') == 'development':
        app.run(debug=True, host='0.0.0.0', port=8080)
    else:
        print("Please use Gunicorn to run this application in production")
        sys.exit(1)
