from flask import Flask, send_file, render_template_string
import markdown2
import os

app = Flask(__name__)

# HTML template for rendering markdown
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Code Analysis Documentation</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-50">
    <div class="container mx-auto px-4 py-8 max-w-4xl">
        <nav class="mb-8 flex space-x-4">
            <a href="/" class="text-blue-600 hover:text-blue-800">Analysis Results</a>
            <a href="/readme" class="text-blue-600 hover:text-blue-800">Documentation</a>
        </nav>
        <div class="prose prose-blue max-w-none bg-white p-8 rounded-lg shadow">
            {{ content|safe }}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def serve_report():
    """Serve the analysis results HTML file."""
    return send_file('analysis_results.html')

@app.route('/readme')
def serve_readme():
    """Serve the README.md file as HTML."""
    try:
        with open('README.md', 'r') as f:
            # Convert markdown to HTML
            md_content = f.read()
            html_content = markdown2.markdown(
                md_content,
                extras=['fenced-code-blocks', 'tables', 'break-on-newline']
            )
            
            # Render with template
            return render_template_string(
                HTML_TEMPLATE,
                content=html_content
            )
    except FileNotFoundError:
        return "README.md not found", 404

@app.route('/health')
def health_check():
    """Health check endpoint for Cloud Run."""
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    # Use PORT environment variable if available (Cloud Run sets this)
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
