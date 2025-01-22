from flask import Flask, send_file, render_template_string
import markdown
import json
from markdown.extensions import fenced_code, tables, toc, codehilite
from markdown.extensions.attr_list import AttrListExtension
from markdown.extensions.md_in_html import MarkdownInHtmlExtension
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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/json.min.js"></script>
    <style>
        /* Custom markdown styling */
        .markdown-body {
            color: #24292e;
            line-height: 1.6;
        }
        .markdown-body h1 {
            font-size: 2em;
            border-bottom: 1px solid #eaecef;
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            padding-bottom: .3em;
        }
        .markdown-body h2 {
            font-size: 1.5em;
            border-bottom: 1px solid #eaecef;
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            padding-bottom: .3em;
        }
        .markdown-body h3 {
            font-size: 1.25em;
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
        }
        .markdown-body p {
            margin-top: 0;
            margin-bottom: 16px;
        }
        .markdown-body code {
            padding: .2em .4em;
            margin: 0;
            font-size: 85%;
            background-color: rgba(27,31,35,.05);
            border-radius: 6px;
            font-family: ui-monospace,SFMono-Regular,SF Mono,Menlo,Consolas,Liberation Mono,monospace;
        }
        .markdown-body pre {
            padding: 16px;
            overflow: auto;
            font-size: 85%;
            line-height: 1.45;
            background-color: #f6f8fa;
            border-radius: 6px;
            margin-bottom: 16px;
        }
        .markdown-body pre code {
            padding: 0;
            margin: 0;
            font-size: 100%;
            background-color: transparent;
            border: 0;
        }
        .markdown-body ul {
            padding-left: 2em;
            margin-top: 0;
            margin-bottom: 16px;
            list-style-type: disc;
        }
        .markdown-body ol {
            padding-left: 2em;
            margin-top: 0;
            margin-bottom: 16px;
        }
        .markdown-body li {
            margin-top: 0.25em;
        }
        .markdown-body blockquote {
            padding: 0 1em;
            color: #6a737d;
            border-left: .25em solid #dfe2e5;
            margin: 0 0 16px;
        }
        .markdown-body table {
            border-spacing: 0;
            border-collapse: collapse;
            margin-top: 0;
            margin-bottom: 16px;
            width: 100%;
        }
        .markdown-body table th {
            font-weight: 600;
            padding: 6px 13px;
            border: 1px solid #dfe2e5;
            background-color: #f6f8fa;
        }
        .markdown-body table td {
            padding: 6px 13px;
            border: 1px solid #dfe2e5;
        }
        .markdown-body img {
            max-width: 100%;
            box-sizing: initial;
            border-style: none;
            margin: 16px 0;
        }
        .markdown-body hr {
            height: .25em;
            padding: 0;
            margin: 24px 0;
            background-color: #e1e4e8;
            border: 0;
        }
    </style>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto px-4 py-8 max-w-4xl">
        <nav class="mb-8 flex space-x-4 bg-white p-4 rounded-lg shadow">
            <a href="/" class="text-blue-600 hover:text-blue-800 font-medium">Analysis Results</a>
            <span class="text-gray-300">|</span>
            <a href="/readme" class="text-blue-600 hover:text-blue-800 font-medium">Documentation</a>
            <span class="text-gray-300">|</span>
            <a href="/jsonresults" class="text-blue-600 hover:text-blue-800 font-medium">JSON Results</a>
        </nav>
        <div class="markdown-body bg-white p-8 rounded-lg shadow">
            {{ content|safe }}
        </div>
    </div>
    <script>hljs.highlightAll();</script>
</body>
</html>
"""

@app.route('/')
def serve_report():
    """Serve the analysis results HTML file."""
    return send_file('analysis_results.html')

@app.route('/readme')
def serve_readme():
    """Serve the README.md file as HTML with improved rendering."""
    try:
        with open('README.md', 'r') as f:
            md_content = f.read()
            
            # Configure Markdown with extensions
            md = markdown.Markdown(extensions=[
                'fenced_code',
                'codehilite',
                'tables',
                'toc',
                AttrListExtension(),
                MarkdownInHtmlExtension(),
                'pymdownx.superfences',
                'pymdownx.highlight',
                'pymdownx.inlinehilite',
                'pymdownx.snippets',
                'pymdownx.tasklist',
            ])
            
            # Convert markdown to HTML
            html_content = md.convert(md_content)
            
            # Render with template
            return render_template_string(
                HTML_TEMPLATE,
                content=html_content
            )
    except FileNotFoundError:
        return "README.md not found", 404

@app.route('/jsonresults')
def serve_json_results():
    """Serve the analysis results JSON file with syntax highlighting."""
    try:
        with open('analysis_results.json', 'r') as f:
            json_content = json.loads(f.read())
            # Pretty print JSON with 2-space indentation
            formatted_json = json.dumps(json_content, indent=2)
            
            html_content = f'''
            <div class="markdown-body">
                <h1>Analysis Results (JSON)</h1>
                <p class="text-gray-600 mb-4">
                    This is the raw JSON data that powers the analysis results. 
                    The data is formatted for readability with syntax highlighting.
                </p>
                <pre><code class="language-json">{formatted_json}</code></pre>
            </div>
            '''
            
            return render_template_string(
                HTML_TEMPLATE,
                content=html_content
            )
    except FileNotFoundError:
        return "analysis_results.json not found", 404
    except json.JSONDecodeError:
        return "Invalid JSON file", 500

@app.route('/health')
def health_check():
    """Health check endpoint for Cloud Run."""
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    # Use PORT environment variable if available (Cloud Run sets this)
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
