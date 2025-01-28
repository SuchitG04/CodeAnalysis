import os
import json
import requests
from pathlib import Path
import random

def analyze_code_with_fireworks(file_path, api_key):
    """
    Analyze a code file using the Fireworks API to extract data sources, sinks, and models.
    
    Args:
        file_path (str): Path to the code file to analyze
        api_key (str): Fireworks API key
    
    Returns:
        dict: The analysis results in JSON format
    """
    # Read the file content
    with open(file_path, 'r') as f:
        code_content = f.read()
    
    print(f"\nAnalyzing file: {file_path}")
    print("="*80)
    print("File contents:")
    print("-"*80)
    print(code_content)
    print("="*80)
    
    # Construct the prompt
    prompt = """
Instructions:

1. Understand the Code Context
Review the Codebase: Examine the entire codebase thoroughly to comprehend its functionality and components.
Identify Primary Purpose: Determine the main purpose of the code (e.g., data processing, communication between services, etc.).

2. Identify Data Sources
Definition: Components or interfaces from which the code retrieves data.

Tasks:
Locate Data Retrieval Points: Identify all locations in the code where data is fetched or received.
Examples of Data Sources: Databases, APIs, file systems, external services, in-memory caches, etc.

For Each Data Source, Extract the Following:

Name: The exact identifier or designation of the data source as defined in the code (e.g., UserDB, PaymentAPI, /configs/settings.yaml, RedisCache).
Type: The specific category of the data source (e.g., Database, API, File, Cache).
Details: Precise connection parameters or configurations extracted directly from the code (e.g., host: "db.example.com", port: 5432, authToken: "abcd1234").

Data Elements:

Element Name: The exact name of the data entity or endpoint accessed, as defined in the code (e.g., users_table, /v1/payments, /data/input.csv).
Description: A clear and concise explanation of the data element's purpose or the information it provides, based on code comments or functionality.

3. Identify Data Sinks
Definition: Components or interfaces to which the code sends or stores data.
Tasks:

Locate Data Writing Points: Identify all locations in the code where data is written, sent, or stored.
Examples of Data Sinks: Databases, APIs, file systems, external services, in-memory caches, etc.
For Each Data Sink, Extract the Following:

Name: The exact identifier or designation of the data sink as defined in the code (e.g., AnalyticsDB, NotificationAPI, /logs/output.log, MemCache).
Type: The specific category of the data sink (e.g., Database, API, File, Cache).
Details: Precise connection parameters or configurations extracted directly from the code (e.g., host: "analytics.example.com", port: 8080, apiKey: "xyz789").

Sent Data:
Data Name: The exact name of the data being sent or stored, as defined in the code (e.g., session_key, order_table, /v1/notify, cache_item).
Description: A clear and concise explanation of the data's purpose or the information it contains, based on code comments or functionality.

4. Identify Data Models
Definition: Classes, structures, or schemas that represent and organize data within the code.
Tasks:
Locate Data Models: Identify all classes or data structures that encapsulate data attributes.
For Each Data Model, Extract the Following:
Name: The exact name of the class or data structure as defined in the code (e.g., User, OrderDetails, ConfigSettings).
Attributes: A comprehensive list of attributes or properties within the model, extracted exactly as defined in the code.
Attribute Name: The exact name of the attribute (e.g., userId, orderAmount, isActive).
Type: The specific data type of the attribute as defined in the code (e.g., String, Integer, CustomObject).
Description: A clear and concise explanation of the attribute's purpose or usage, based on code comments or context.

5. Organize Extracted Information into JSON
Structure the extracted data into the following JSON format, ensuring all names are exact and derived directly from the code: 
{
  "dataSources": [
    {
      "name": "ExactDataSourceName",
      "type": "ExactDataSourceType",
      "details": {
        "parameter1": "ExactValue1",
        "parameter2": "ExactValue2"
        ...   
      },
      "dataElements": [
        {
          "elementName": "ExactElementName",
          "description": "Precise description of the data element."
        }
       
      ]
    }    
  ],
  "dataSinks": [
    {
      "name": "ExactDataSinkName",
      "type": "ExactDataSinkType",
      "details": {
        "parameter1": "ExactValue1",
        "parameter2": "ExactValue2"        
      },
      "sentData": [
        {
          "dataName": "ExactDataName",
          "description": "Precise description of the sent data."
        }
        // Additional sent data entries as defined in the code
      ]
    }
    // Additional data sinks as defined in the code
  ],
  "dataModels": [
    {
      "name": "ExactDataModelName",
      "attributes": [
        {
          "attributeName": "ExactAttributeName",
          "type": "ExactAttributeType",
          "description": "Precise description of the attribute."
        }
        // Additional attributes as defined in the code
      ]
    }
    // Additional data models as defined in the code
  ]
}
6. Ensure Explicit Naming
Data Model Elements:
Exact Attribute Names: Extract and provide the exact names of all attributes within each data model as defined in the code.
Data Received from Data Sources:
Exact Data Entity Names: Clearly specify the exact names of the data entities being received from each data source, as defined in the code.
Data Sent to Data Sinks:
Exact Data Entity Names: Clearly specify the exact names of the data entities being sent to each data sink, as defined in the code.
7. General Guidelines
Use Precise and Descriptive Names: Extract names exactly as they appear in the code to avoid ambiguity.
Consistency in Naming Conventions: Maintain consistent naming conventions throughout the JSON structure, reflecting the codebase's conventions.
\n\n""" +  "\n-----------\n" + str(code_content) + "\n-----------\n" +  "Follow the instructions to analyze this code and provide the output in the specified JSON format."



    print(prompt)
    # API configuration
    url = "https://api.fireworks.ai/inference/v1/completions"
    payload = {
        "model": "accounts/fireworks/models/deepseek-r1",
        "max_tokens": 20480,
        "top_p": 1,
        "top_k": 40,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "temperature": 0.1,
        "prompt": prompt
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer fw_3ZnkM3DDfxYG6e5W5c6mempB"
    }

    # Make the API request
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Extract the completion from the response
        completion = result.get('choices', [{}])[0].get('text', '').strip()
        
        print("\nAPI Response:")
        print("="*80)
        print(completion)
        print("="*80)
        
        # Extract JSON from the completion
        json_start = completion.find('```json')
        json_end = completion.rfind('```')
        
        if json_start != -1 and json_end != -1:
            # Extract the JSON content between the markers
            json_content = completion[json_start + 7:json_end].strip()
            
            # Try to parse the JSON content
            try:
                analysis_result = json.loads(json_content)
                print("\nExtracted and Validated JSON Response:")
                print("="*80)
                print(json.dumps(analysis_result, indent=2))
                print("="*80)
                return analysis_result
            except json.JSONDecodeError as e:
                print(f"Warning: Extracted content is not valid JSON: {str(e)}")
                print("Raw extracted content:")
                print("-"*80)
                print(json_content)
                print("-"*80)
                return None
        else:
            print("Warning: Could not find JSON markers in the response")
            try:
                # Try to parse the entire response as JSON as fallback
                analysis_result = json.loads(completion)
                print("\nParsed Complete Response as JSON:")
                print("="*80)
                print(json.dumps(analysis_result, indent=2))
                print("="*80)
                return analysis_result
            except json.JSONDecodeError:
                print("Warning: Complete response is not valid JSON either")
                return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {str(e)}")
        return None

def main():
    """
    Main function to analyze a Python file using Fireworks API.
    Can be used either with command line arguments or by importing and calling directly.
    """
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description='Analyze a Python file using Fireworks API')
    parser.add_argument('--file', '-f', type=str, help='Path to the Python file to analyze')
    parser.add_argument('--random', '-r', action='store_true', help='Analyze a random file from the generated directory')
    args = parser.parse_args()

    # Get API key
    api_key = "fw_3ZnkM3DDfxYG6e5W5c6mempB"

    if args.file:
        # Use the specified file
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File {file_path} does not exist")
            return
        if not file_path.suffix == '.py':
            print(f"Error: File {file_path} is not a Python file")
            return
    elif args.random:
        # Use random file from generated directory (original behavior)
        generated_dir = Path('/Users/harshsinghal/workspace/armor1/generated')
        python_files = list(generated_dir.glob('*.py'))
        if not python_files:
            print("No Python files found in the generated directory")
            return
        file_path = random.choice(python_files)
    else:
        parser.print_help()
        return

    # Analyze the file
    result = analyze_code_with_fireworks(str(file_path), api_key)
    return result

if __name__ == '__main__':
    main()
