#!/usr/bin/env python3

import json
import os
from typing import Dict, List, Any

def generate_html_report(analysis_results: List[Dict[str, Any]], python_files: Dict[str, str]) -> str:
    """Generate an HTML report with TailwindCSS styling."""
    
    # Generate table rows and modals first
    table_rows = []
    modal_templates = []
    total_models = 0
    total_fields = 0
    total_security_findings = 0
    total_arch_patterns = 0
    total_error_handlers = 0
    
    for result in analysis_results:
        file_name = result['file_name']
        models = result.get('data_models', [])
        total_models += len(models)
        
        # Count total fields
        fields_count = sum(len(model.get('fields', [])) for model in models)
        total_fields += fields_count
        
        # Format model names
        model_names = [model['class_name'] for model in models]
        
        # Format sources and sinks
        sources = result.get('data_sources', [])
        sinks = result.get('data_sinks', [])
        
        # Get security info
        security_info = result.get('security_info', {})
        auth_methods = security_info.get('auth_methods', [])
        compliance_refs = security_info.get('compliance_refs', [])
        encryption_usage = security_info.get('encryption_usage', [])
        audit_logs = security_info.get('audit_logs', [])
        access_controls = security_info.get('access_controls', [])
        
        # Count security findings
        security_count = len(auth_methods) + len(compliance_refs) + len(encryption_usage) + len(audit_logs) + len(access_controls)
        total_security_findings += security_count
        
        # Get architecture info
        arch_info = result.get('architecture_info', {})
        patterns = arch_info.get('patterns', [])
        event_handlers = arch_info.get('event_handlers', [])
        messaging_patterns = arch_info.get('messaging_patterns', [])
        
        # Count architecture patterns
        arch_count = len(patterns) + len(event_handlers) + len(messaging_patterns)
        total_arch_patterns += arch_count
        
        # Get error handling info
        error_info = result.get('error_handling', {})
        retry_mechanisms = error_info.get('retry_mechanisms', [])
        validation_checks = error_info.get('validation_checks', [])
        rate_limits = error_info.get('rate_limits', [])
        timeout_handlers = error_info.get('timeout_handlers', [])
        
        # Count error handlers
        error_count = len(retry_mechanisms) + len(validation_checks) + len(rate_limits) + len(timeout_handlers)
        total_error_handlers += error_count
        
        # Create table row
        row = f'''
            <tr class="hover:bg-gray-50">
                <td class="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">
                    <button @click="$dispatch('show-modal', {{ id: '{file_name}' }})" class="text-blue-600 hover:text-blue-800">
                        {file_name}
                    </button>
                </td>
                <td class="px-3 py-2 text-sm text-gray-500">
                    {', '.join(model_names) if model_names else '-'}
                </td>
                <td class="px-3 py-2 text-sm text-gray-500 text-center">{fields_count}</td>
                <td class="px-3 py-2 text-sm text-gray-500">
                    {', '.join(f"{source['source_type']}:{source['source_name']}" for source in result['data_sources']) if result['data_sources'] else '-'}
                </td>
                <td class="px-3 py-2 text-sm text-gray-500">
                    {', '.join(sinks) if sinks else '-'}
                </td>
                <td class="px-3 py-2 text-sm text-gray-500 text-center">
                    {security_count}
                </td>
                <td class="px-3 py-2 text-sm text-gray-500 text-center">
                    {arch_count}
                </td>
                <td class="px-3 py-2 text-sm text-gray-500 text-center">
                    {error_count}
                </td>
                <td class="px-3 py-2 text-sm text-gray-500">
                    <button @click="$dispatch('show-modal', {{ id: '{file_name}_analysis' }})" 
                            class="text-green-600 hover:text-green-800 inline-flex items-center">
                        <span class="mr-1">Analysis</span>
                        <span class="bg-green-100 text-green-800 text-xs font-medium px-2 py-0.5 rounded-full">
                            {security_count + arch_count + error_count}
                        </span>
                    </button>
                </td>
            </tr>
        '''
        table_rows.append(row)
        
        # Create modal for Python file content
        if file_name in python_files:
            # Escape the Python code for HTML
            escaped_code = python_files[file_name].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            modal = f'''
                <div x-show="activeModal === '{file_name}'"
                     @show-modal.window="activeModal = $event.detail.id"
                     class="fixed inset-0 z-50 overflow-y-auto"
                     style="display: none;">
                    <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
                        <span class="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
                        <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
                            <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                                <div class="sm:flex sm:items-start">
                                    <div class="mt-3 text-center sm:mt-0 sm:text-left w-full">
                                        <div class="flex justify-between items-center mb-4">
                                            <h3 class="text-lg font-medium text-gray-900">
                                                {file_name}
                                            </h3>
                                            <button @click="activeModal = null" class="text-gray-400 hover:text-gray-500">
                                                <span class="sr-only">Close</span>
                                                <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                                                </svg>
                                            </button>
                                        </div>
                                        <div class="mt-4 max-h-[70vh] overflow-y-auto">
                                            <pre class="bg-gray-50 rounded p-4 overflow-x-auto text-sm"><code class="language-python">{escaped_code}</code></pre>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            '''
            modal_templates.append(modal)

            # Create modal for detailed analysis
            analysis_modal = f'''
                <div x-show="activeModal === '{file_name}_analysis'"
                     @show-modal.window="activeModal = $event.detail.id"
                     class="fixed inset-0 z-50 overflow-y-auto"
                     style="display: none;">
                    <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
                        <span class="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
                        <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
                            <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                                <div class="sm:flex sm:items-start">
                                    <div class="mt-3 text-center sm:mt-0 sm:text-left w-full">
                                        <div class="flex justify-between items-center mb-4">
                                            <h3 class="text-lg font-medium text-gray-900">
                                                Analysis: {file_name}
                                            </h3>
                                            <button @click="activeModal = null" class="text-gray-400 hover:text-gray-500">
                                                <span class="sr-only">Close</span>
                                                <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                                                </svg>
                                            </button>
                                        </div>
                                        <div class="mt-4 max-h-[70vh] overflow-y-auto space-y-6">
                                            <!-- Data Sources Section -->
                                            <div class="bg-indigo-50 p-4 rounded-lg">
                                                <h4 class="text-indigo-800 font-medium mb-2">Data Sources & Fields</h4>
                                                <div class="space-y-4">
                                                    {generate_data_source_sections(result['data_sources'])}
                                                </div>
                                            </div>
                                            
                                            <!-- Security Section -->
                                            <div class="bg-yellow-50 p-4 rounded-lg">
                                                <h4 class="text-yellow-800 font-medium mb-2">Security & Compliance</h4>
                                                <div class="space-y-2">
                                                    <div class="text-yellow-700">
                                                        <strong>Authentication Methods:</strong>
                                                        <p>{', '.join(auth_methods) if auth_methods else 'None'}</p>
                                                    </div>
                                                    <div class="text-yellow-700">
                                                        <strong>Compliance References:</strong>
                                                        <p>{', '.join(compliance_refs) if compliance_refs else 'None'}</p>
                                                    </div>
                                                    <div class="text-yellow-700">
                                                        <strong>Encryption Usage:</strong>
                                                        <p>{', '.join(encryption_usage) if encryption_usage else 'None'}</p>
                                                    </div>
                                                    <div class="text-yellow-700">
                                                        <strong>Audit Logs:</strong>
                                                        <p>{', '.join(audit_logs) if audit_logs else 'None'}</p>
                                                    </div>
                                                    <div class="text-yellow-700">
                                                        <strong>Access Controls:</strong>
                                                        <p>{', '.join(access_controls) if access_controls else 'None'}</p>
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            <!-- Architecture Section -->
                                            <div class="bg-blue-50 p-4 rounded-lg">
                                                <h4 class="text-blue-800 font-medium mb-2">Architecture Patterns</h4>
                                                <div class="space-y-2">
                                                    <div class="text-blue-700">
                                                        <strong>Design Patterns:</strong>
                                                        <p>{', '.join(patterns) if patterns else 'None'}</p>
                                                    </div>
                                                    <div class="text-blue-700">
                                                        <strong>Event Handlers:</strong>
                                                        <p>{', '.join(event_handlers) if event_handlers else 'None'}</p>
                                                    </div>
                                                    <div class="text-blue-700">
                                                        <strong>Messaging Patterns:</strong>
                                                        <p>{', '.join(messaging_patterns) if messaging_patterns else 'None'}</p>
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            <!-- Error Handling Section -->
                                            <div class="bg-red-50 p-4 rounded-lg">
                                                <h4 class="text-red-800 font-medium mb-2">Error Handling</h4>
                                                <div class="space-y-2">
                                                    <div class="text-red-700">
                                                        <strong>Retry Mechanisms:</strong>
                                                        <p>{', '.join(retry_mechanisms) if retry_mechanisms else 'None'}</p>
                                                    </div>
                                                    <div class="text-red-700">
                                                        <strong>Validation Checks:</strong>
                                                        <p>{', '.join(validation_checks) if validation_checks else 'None'}</p>
                                                    </div>
                                                    <div class="text-red-700">
                                                        <strong>Rate Limits:</strong>
                                                        <p>{', '.join(rate_limits) if rate_limits else 'None'}</p>
                                                    </div>
                                                    <div class="text-red-700">
                                                        <strong>Timeout Handlers:</strong>
                                                        <p>{', '.join(timeout_handlers) if timeout_handlers else 'None'}</p>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            '''
            modal_templates.append(analysis_modal)
    
    # Generate the complete HTML
    html = f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Code Analysis Report</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/default.min.css">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
            <script>hljs.highlightAll();</script>
        </head>
        <body class="bg-gray-100" x-data="{{ activeModal: null }}">
            <div class="min-h-screen py-6 flex flex-col justify-center sm:py-12">             
                <div class="px-4 sm:px-6 lg:px-8">
                    <div class="mb-8 bg-white rounded-lg shadow p-6">
                        <h1 class="text-3xl font-bold text-gray-900 mb-4">Code Analysis Report</h1>
                        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div class="bg-blue-50 rounded-lg p-4">
                                <div class="text-2xl font-semibold text-blue-800">{total_models}</div>
                                <div class="text-sm text-blue-600">Data Models</div>
                            </div>
                            <div class="bg-green-50 rounded-lg p-4">
                                <div class="text-2xl font-semibold text-green-800">{total_fields}</div>
                                <div class="text-sm text-green-600">Total Fields</div>
                            </div>
                            <div class="bg-yellow-50 rounded-lg p-4">
                                <div class="text-2xl font-semibold text-yellow-800">{total_security_findings}</div>
                                <div class="text-sm text-yellow-600">Security Findings</div>
                            </div>
                            <div class="bg-purple-50 rounded-lg p-4">
                                <div class="text-2xl font-semibold text-purple-800">{total_arch_patterns + total_error_handlers}</div>
                                <div class="text-sm text-purple-600">Architecture & Error Patterns</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="shadow overflow-hidden border-b border-gray-200 sm:rounded-lg bg-white">
                        <div class="overflow-x-auto max-w-[95vw] mx-auto">
                            <table class="min-w-full divide-y divide-gray-200 table-fixed">
                                <thead class="bg-gray-50">
                                    <tr>
                                        <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[15%]">File Name</th>
                                        <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[12%]">Data Models</th>
                                        <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[8%]">Fields</th>
                                        <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[12%]">Data Sources</th>
                                        <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[12%]">Data Sinks</th>
                                        <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-[8%]">Security</th>
                                        <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-[8%]">Arch.</th>
                                        <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider w-[8%]">Error</th>
                                        <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[12%]">Analysis</th>
                                    </tr>
                                </thead>
                                <tbody class="bg-white divide-y divide-gray-200">
                                    {''.join(table_rows)}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                
                <!-- Modal Templates -->
                {''.join(modal_templates)}
            </div>
        </body>
        </html>
    '''
    
    return html

def generate_data_source_sections(sources):
    """Generate HTML sections for data sources and their fields."""
    if not sources:
        return '<div class="text-indigo-700">No data sources found</div>'
    
    sections = []
    for source in sources:
        fields_html = ''
        if source['fields']:
            fields_list = []
            for field in sorted(source['fields']):
                field_type = source['field_types'].get(field, '')
                field_html = field
                if field_type:
                    field_html += f' <span class="text-indigo-500">({field_type})</span>'
                fields_list.append(field_html)
            fields_html = '<div class="pl-4 mt-1">' + '<br>'.join(fields_list) + '</div>'
        
        section = f'''
            <div class="text-indigo-700">
                <strong>{source['source_type'].title()}:</strong> {source['source_name']}
                {fields_html}
            </div>
        '''
        sections.append(section)
    
    return '\n'.join(sections)

def main():
    """Generate an HTML report from the analysis results."""
    try:
        # Read analysis results
        with open('analysis_results.json', 'r') as f:
            analysis_results = json.load(f)
        
        # Read all Python files from the generated directory
        python_files = {}
        generated_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generated')
        for result in analysis_results:
            file_name = result['file_name']
            file_path = os.path.join(generated_dir, file_name)
            try:
                with open(file_path, 'r') as f:
                    python_files[file_name] = f.read()
            except Exception as e:
                print(f"Warning: Could not read file {file_path}: {e}")
        
        # Generate HTML report
        html_content = generate_html_report(analysis_results, python_files)
        
        # Write HTML report
        output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'analysis_results.html')
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        print(f"✅ Generated HTML report: {output_path}")
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        raise

if __name__ == "__main__":
    main()
