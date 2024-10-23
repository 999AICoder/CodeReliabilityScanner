import argparse
from base_app import create_base_app
from blueprints.analyzer import analyzer
from blueprints.suggestions import suggestions

app = create_base_app()
app.register_blueprint(analyzer)
app.register_blueprint(suggestions)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run the Aider Suggestions web interface")
    parser.add_argument("--highlight", action="store_true", help="Enable syntax highlighting")
    args = parser.parse_args()

    app.config['HIGHLIGHT'] = args.highlight
    app.run(debug=True, port=5000)
