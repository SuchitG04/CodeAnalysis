from flask import Flask, send_file
import os

app = Flask(__name__)

@app.route('/')
def serve_report():
    """Serve the analysis results HTML file."""
    return send_file('analysis_results.html')

@app.route('/health')
def health_check():
    """Health check endpoint for Cloud Run."""
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    # Use PORT environment variable if available (Cloud Run sets this)
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
