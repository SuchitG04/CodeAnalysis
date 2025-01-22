#!/usr/bin/env python3

import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import requests
import random
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
FIREWORKS_API_URL = "https://api.fireworks.ai/inference/v1/chat/completions"

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json file."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.template.json')
    
    if not os.path.exists(config_path):
        if os.path.exists(template_path):
            raise FileNotFoundError(
                f"config.json not found. Please copy {template_path} to {config_path} "
                "and update it with your API key."
            )
        else:
            raise FileNotFoundError(
                "Neither config.json nor config.template.json found. "
                "Please create config.json with your API key."
            )
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {str(e)}")
    except Exception as e:
        raise Exception(f"Error reading config file: {str(e)}")

@dataclass
class CodeGenerationRequest:
    """Data class for code generation request parameters."""
    description: str
    template_name: Optional[str] = None
    output_file: Optional[str] = None
    additional_context: Optional[Dict[str, Any]] = None

class PromptGenerator:
    """Class to generate diverse prompts for code generation."""

    def __init__(self):
        self.contexts = [
            {
                "title": "Banking Security Context",
                "description": """We are an online bank's security team evaluating customer data access and usage.
                The system integrates multiple SaaS platforms (M365, Google Workspace, HubSpot, Salesforce) and internal microservices.
                Each data source introduces compliance requirements and security approval flows."""
            },
            {
                "title": "Data Integration Platform",
                "description": """You're building a data integration platform that connects various enterprise systems.
                The platform handles sensitive customer information and must comply with privacy regulations.
                Different teams contribute to the codebase, leading to varying coding styles and practices."""
            },
            {
                "title": "Financial Data Processing",
                "description": """This system processes financial transactions and customer data across multiple services.
                It includes both internal APIs and third-party integrations.
                Security and compliance are critical but implementation may vary."""
            },
            {
                "title": "Healthcare Data Exchange",
                "description": """A healthcare provider's system that exchanges patient data between different departments and external labs.
                Must handle HIPAA compliance requirements and secure PHI (Protected Health Information).
                Includes integration with Electronic Health Record (EHR) systems and insurance providers."""
            },
            {
                "title": "E-commerce Platform",
                "description": """Multi-vendor e-commerce platform handling customer data, payment processing, and inventory management.
                Integrates with multiple payment gateways, shipping providers, and vendor systems.
                Must comply with PCI-DSS for payment data and GDPR for customer information."""
            },
            {
                "title": "IoT Device Management",
                "description": """System managing a network of IoT devices in smart buildings.
                Collects and processes sensor data, manages device credentials, and handles firmware updates.
                Security concerns include device authentication and sensitive data transmission."""
            },
            {
                "title": "Educational Platform",
                "description": """Learning management system handling student data, course materials, and assessment results.
                Integrates with various educational tools and content providers.
                Must comply with FERPA regulations and protect student privacy."""
            },
            {
                "title": "Government Data Portal",
                "description": """Government agency system managing citizen data and service requests.
                Interfaces with multiple department databases and external verification services.
                Strict security requirements and audit logging for all data access."""
            }
        ]

        self.data_flows = [
            "Data flows from SaaS platforms to internal databases",
            "Information is shared with third-party systems for specialized processing",
            "Customer data moves between microservices and external APIs",
            "Files are processed and uploaded to cloud storage",
            "Data is extracted, transformed, and loaded across systems",
            "Real-time data streaming between services with event processing",
            "Batch processing of historical data with compliance checks",
            "Multi-stage data pipeline with validation and enrichment",
            "Bidirectional sync between internal and external systems",
            "Data aggregation from multiple sources with transformation rules"
        ]

        self.security_aspects = [
            "Incomplete identity verification checks",
            "Partial compliance policy implementations (GDPR, internal rules)",
            "Inconsistent audit logging",
            "Mixed credential management practices",
            "Varying levels of error handling",
            "Token-based authentication with expiration handling",
            "Role-based access control implementation",
            "API key rotation and management",
            "Data encryption in transit and at rest",
            "Rate limiting and request throttling",
            "Input validation and sanitization",
            "Session management and timeout handling"
        ]

        self.data_sources = [
            "SaaS Platforms (M365, Google Workspace, HubSpot, Salesforce)",
            "Databases (MySQL, PostgreSQL, MongoDB, Redis)",
            "Data Warehouses (Snowflake, BigQuery)",
            "Local Files (CSV, JSON, XML)",
            "Internal/External APIs",
            "Message Queues (RabbitMQ, Kafka)",
            "Cloud Storage (S3, GCS, Azure Blob)",
            "Cache Systems (Redis, Memcached)",
            "Time Series Databases (InfluxDB, TimescaleDB)",
            "Graph Databases (Neo4j, Amazon Neptune)",
            "Search Engines (Elasticsearch, Solr)",
            "Blockchain Networks (Ethereum, Hyperledger)"
        ]

        self.code_quality_variations = [
            "Well-documented functions mixed with unclear ones",
            "Inconsistent error handling approaches",
            "Mix of secure and insecure credential management",
            "Varying levels of code organization",
            "Random TODOs and FIXMEs",
            "Different logging styles and verbosity levels",
            "Mixture of synchronous and asynchronous code",
            "Inconsistent parameter validation",
            "Variable naming convention differences",
            "Mixed use of OOP and functional programming",
            "Varying levels of code modularization",
            "Different approaches to configuration management"
        ]

        self.compliance_elements = [
            "Third-party approval checks",
            "Compliance officer approval flags",
            "Identity and role verification",
            "Data access logging",
            "Policy reference implementations",
            "Data retention policy enforcement",
            "Personal data anonymization",
            "Consent management implementation",
            "Audit trail generation",
            "Data classification handling",
            "Cross-border data transfer checks",
            "Privacy impact assessment references",
            "Data subject rights handling",
            "Breach notification procedures"
        ]

        self.architecture_patterns = [
            "Microservices with API Gateway",
            "Event-driven architecture",
            "Layered architecture with separation of concerns",
            "Pub/Sub messaging pattern",
            "CQRS pattern for data operations",
            "Circuit breaker for external services",
            "Saga pattern for distributed transactions",
            "Adapter pattern for external integrations"
        ]

        self.error_scenarios = [
            "Network timeouts and retries",
            "Invalid data format handling",
            "Authentication failures",
            "Rate limit exceeded scenarios",
            "Database connection issues",
            "Third-party service outages",
            "Data validation failures",
            "Concurrent access conflicts"
        ]

    def generate_prompt(self) -> str:
        """Generate a random prompt for code generation."""
        context = random.choice(self.contexts)
        num_data_sources = random.randint(2, 4)
        num_security_aspects = random.randint(2, 3)
        num_compliance_elements = random.randint(1, 3)
        num_architecture_patterns = random.randint(1, 2)
        num_error_scenarios = random.randint(1, 2)

        selected_data_sources = random.sample(self.data_sources, num_data_sources)
        selected_security = random.sample(self.security_aspects, num_security_aspects)
        selected_compliance = random.sample(self.compliance_elements, num_compliance_elements)
        selected_patterns = random.sample(self.architecture_patterns, num_architecture_patterns)
        selected_errors = random.sample(self.error_scenarios, num_error_scenarios)
        data_flow = random.choice(self.data_flows)
        code_quality = random.sample(self.code_quality_variations, 2)

        prompt = f"""Generate a Python script that demonstrates data handling in a security-sensitive environment.

Context:
{context['description']}

Requirements:

1. Data Flow:
- {data_flow}
- Must involve these data sources: {', '.join(selected_data_sources)}
- Implement these architectural patterns: {', '.join(selected_patterns)}

2. Security & Compliance:
- Implement these security aspects: {', '.join(selected_security)}
- Include these compliance elements: {', '.join(selected_compliance)}
- Handle these error scenarios: {', '.join(selected_errors)}

3. Code Quality:
- {code_quality[0]}
- {code_quality[1]}

4. Structure:
- Create a main class or function that orchestrates the data flow
- Include appropriate imports (can be stubbed)
- Add relevant error handling (can be inconsistent)
- Include some form of logging or monitoring

5. Output:
- Provide the complete Python code
- Include docstrings (can be of varying quality)
- Add comments explaining key parts of the implementation

The code should be runnable (with stubbed external dependencies) and demonstrate realistic but imperfect security practices.
"""
        return prompt

class PromptTemplate:
    """Manages prompt templates for different types of code generation."""

    @staticmethod
    def get_python_script_template() -> str:
        """Template for generating Python scripts with varying code quality."""
        return """
        Create a Python script that simulates real-world code quality and practices. The code should feel authentic, as if written by different developers with varying experience levels and coding habits.

        Description:
        {description}

        Code Style Requirements (randomly vary these aspects):
        1. Documentation:
           - Some functions might have detailed docstrings
           - Others might have no documentation at all
           - Mix of helpful and unclear/outdated comments
           - Some TODOs or FIXMEs that were never addressed

        2. Variable Naming:
           - Mix of well-named and poorly named variables (e.g., 'x', 'temp', 'data', etc.)
           - Inconsistent naming conventions (camelCase, snake_case, etc.)
           - Some meaningless or confusing abbreviations

        3. Error Handling:
           - Some places with proper try-except blocks
           - Other places with bare except clauses
           - Mix of detailed and generic error messages
           - Some error cases completely unhandled

        4. Code Organization:
           - Varying levels of code organization
           - Some functions might be too long
           - Possible duplicate code
           - Mix of clear and confusing logic flows

        5. Real-world Data Handling:
           - Include realistic data sources (files, APIs, databases)
           - Mix of proper and improper resource cleanup
           - Various data formats (JSON, CSV, XML, etc.)
           - Some hardcoded values and credentials
           - Occasional debug print statements left in code

        Additional Context:
        {additional_context}

        Remember: The goal is to simulate real-world code that might be found in production systems, including both good and bad practices. The code should work but reflect the reality of how software is often written in practice.
        """

    @staticmethod
    def get_class_template() -> str:
        """Template for generating Python classes with varying implementation quality."""
        return """
        Create a Python class that reflects real-world implementation patterns and anti-patterns. The code should feel like it was written and maintained by multiple developers over time.

        Description:
        {description}

        Implementation Requirements (mix these aspects):
        1. Class Structure:
           - Some methods might be well-organized
           - Others might be too long or do too many things
           - Mix of instance and class variables
           - Possible unused attributes
           - Some commented-out code

        2. Data Handling:
           - Various data sources and sinks:
             * Database connections (MySQL, PostgreSQL, SQLite)
             * File operations (reading/writing different formats)
             * API calls (REST, GraphQL, SOAP)
             * Cache systems (Redis, Memcached)
           - Mix of synchronous and asynchronous operations
           - Some race conditions or thread safety issues
           - Occasional memory leaks

        3. Security Practices:
           - Mix of proper and improper credential handling
           - Some hardcoded secrets
           - Varying levels of input validation
           - Mix of secure and insecure defaults

        4. Dependencies:
           - Mix of explicit and implicit dependencies
           - Some version-specific code
           - Occasional use of deprecated functions
           - Mix of standard library and external packages

        5. Real-world Complexity:
           - Business logic mixed with technical implementation
           - Some technical debt indicators
           - Legacy code patterns
           - Workarounds for external system limitations

        Additional Context:
        {additional_context}

        Note: Create code that reflects real-world development practices, including both patterns and anti-patterns. The implementation should work but include common issues found in production code.
        """

class CodeGenerator:
    """Handles interaction with Fireworks AI API for code generation."""

    # Available LLM models
    MODELS = [
        "accounts/fireworks/models/deepseek-v3",
        "accounts/fireworks/models/llama-v3p1-405b-instruct",
        "accounts/fireworks/models/llama-v3p3-70b-instruct",
        "accounts/fireworks/models/qwen2p5-coder-32b-instruct",
        "accounts/fireworks/models/mixtral-8x22b-instruct",
        "accounts/fireworks/models/qwen2p5-72b-instruct"
    ]

    def __init__(self):
        """Initialize the code generator with API key from config."""
        try:
            config = load_config()
            self.api_key = config['fireworks_api']['api_key']
            if self.api_key == "your-api-key-here":
                raise ValueError("Please update config.json with your actual API key")
        except Exception as e:
            logger.error(f"Failed to load API key from config: {str(e)}")
            raise
            
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def _prepare_prompt(self, request: CodeGenerationRequest) -> str:
        """Prepare the prompt based on the request and template."""
        template = PromptTemplate.get_python_script_template()
        if request.template_name == "class":
            template = PromptTemplate.get_class_template()

        additional_context = json.dumps(request.additional_context) if request.additional_context else "None"
        return template.format(
            description=request.description,
            additional_context=additional_context
        )

    def _extract_python_code(self, content: str) -> str:
        """Extract Python code from markdown response."""
        # Look for Python code blocks
        import re
        
        # Try to find code block with ```python
        pattern = r'```python\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            # Return the first Python code block found
            return matches[0].strip()
        
        # If no ```python block found, try just ``` blocks
        pattern = r'```\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            # Return the first code block found
            return matches[0].strip()
            
        # If no code blocks found, return the original content
        # (assuming it's raw Python code)
        return content.strip()

    def generate_code(self, request: CodeGenerationRequest) -> Optional[str]:
        """Generate code using Fireworks AI API."""
        try:
            print(f"\n Preparing prompt for: {request.output_file}")
            prompt = request.description
            
            # Print the formatted prompt
            print(format_prompt(prompt))

            # Randomly select a model
            selected_model = random.choice(self.MODELS)
            print(f" Using model: {selected_model}")
            
            print(f" Sending request to Fireworks AI API...")
            payload = {
                "model": selected_model,
                "max_tokens": 20480,
                "top_p": 1,
                "top_k": 40,
                "presence_penalty": 0,
                "frequency_penalty": 0,
                "temperature": 0.6,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            response = requests.post(
                FIREWORKS_API_URL,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            print(f" Received response from API")

            result = response.json()
            raw_content = result['choices'][0]['message']['content']
            
            # Extract only the Python code from the response
            generated_code = self._extract_python_code(raw_content)
            
            # Save to file if output_file is specified
            if request.output_file:
                print(f" Saving generated code to: {request.output_file}")
                os.makedirs(os.path.dirname(request.output_file), exist_ok=True)
                with open(request.output_file, 'w') as f:
                    f.write(generated_code)
                print(f" Successfully saved: {request.output_file}")

            return generated_code

        except requests.exceptions.RequestException as e:
            print(f" API request failed: {str(e)}")
            logger.error(f"API request failed: {str(e)}")
            raise
        except Exception as e:
            print(f" Code generation failed: {str(e)}")
            logger.error(f"Code generation failed: {str(e)}")
            raise

def format_prompt(prompt: str) -> str:
    """Format a prompt for nice console output."""
    separator = "="*80
    formatted = f"""
🤖 Prompt to LLM:
{separator}
{prompt}
{separator}
"""
    return formatted

def generate_short_uuid() -> str:
    """Generate a short UUID (8 characters)."""
    return str(uuid.uuid4())[:8]

def get_random_data_sources() -> List[str]:
    """Get a random selection of data sources."""
    sources = [
        "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
        "CSV files", "JSON files", "XML files", "Excel sheets",
        "REST APIs", "GraphQL endpoints", "SOAP services",
        "Message queues", "Kafka topics", "S3 buckets",
        "FTP servers", "WebSocket streams", "gRPC services"
    ]
    return random.sample(sources, k=random.randint(2, 4))

def get_random_issues() -> List[str]:
    """Get a random selection of common issues."""
    issues = [
        "race conditions", "memory leaks", "connection timeouts",
        "invalid data formats", "missing fields", "encoding errors",
        "authentication failures", "rate limiting", "stale cache",
        "deadlocks", "data corruption", "version conflicts",
        "permission denied", "resource exhaustion", "network latency",
        "incomplete transactions", "data inconsistency", "API changes"
    ]
    return random.sample(issues, k=random.randint(2, 4))

def get_random_features() -> List[str]:
    """Get a random selection of features."""
    features = [
        "data validation", "error retry", "caching", "logging",
        "monitoring", "authentication", "authorization", "rate limiting",
        "data encryption", "compression", "backup", "recovery",
        "audit trails", "notifications", "scheduling", "pagination",
        "search", "filtering", "sorting", "reporting"
    ]
    return random.sample(features, k=random.randint(2, 4))

def get_random_context() -> Dict[str, Any]:
    """Generate random additional context."""
    contexts = {
        "data_sources": get_random_data_sources(),
        "issues": get_random_issues(),
        "features": get_random_features(),
        "complexity": random.choice(["low", "medium", "high"]),
        "performance_critical": random.choice([True, False]),
        "security_sensitive": random.choice([True, False]),
        "legacy_compatibility": random.choice([True, False])
    }
    return {k: v for k, v in contexts.items() if random.random() > 0.3}  # Randomly exclude some contexts

def get_random_script_type() -> Tuple[str, str, Dict[str, Any]]:
    """Get a random script type with description and context."""
    script_types = [
        ("data_processor", "Create a data processing script that handles {sources} with focus on {features}.", 
         {"sources": get_random_data_sources(), "features": get_random_features()}),
        ("api_client", "Implement an API client for integrating with {sources}. Handle {issues}.", 
         {"sources": get_random_data_sources(), "issues": get_random_issues()}),
        ("auth_handler", "Create an authentication system supporting {features} while addressing {issues}.", 
         {"features": get_random_features(), "issues": get_random_issues()}),
        ("data_model", "Define data models for {sources} with {features}.", 
         {"sources": get_random_data_sources(), "features": get_random_features()}),
        ("task_processor", "Implement a task processor handling {sources} with {features}.", 
         {"sources": get_random_data_sources(), "features": get_random_features()}),
        ("cache_manager", "Create a caching system for {sources} dealing with {issues}.", 
         {"sources": get_random_data_sources(), "issues": get_random_issues()}),
        ("config_handler", "Implement a configuration handler for {sources} with {features}.", 
         {"sources": get_random_data_sources(), "features": get_random_features()}),
        ("log_processor", "Create a log processing system for {sources} handling {issues}.", 
         {"sources": get_random_data_sources(), "issues": get_random_issues()})
    ]
    
    script_type, desc_template, base_context = random.choice(script_types)
    description = desc_template.format(**base_context)
    context = {**base_context, **get_random_context()}
    
    return script_type, description, context

class ScriptTypeDistribution:
    """Manages the distribution of script types and suggests under-represented ones."""
    
    # Target percentages for each script type
    TARGET_DISTRIBUTION = {
        "data_processor": 0.15,
        "api_client": 0.15,
        "auth_handler": 0.10,
        "data_model": 0.15,
        "task_processor": 0.10,
        "cache_manager": 0.10,
        "config_handler": 0.10,
        "log_processor": 0.15
    }
    
    def __init__(self, generated_dir: str):
        """Initialize with the directory containing generated files."""
        self.generated_dir = generated_dir
        self.current_distribution = self._analyze_existing_files()
        
    def _analyze_existing_files(self) -> Dict[str, int]:
        """Analyze existing files to get current distribution."""
        distribution = {script_type: 0 for script_type in self.TARGET_DISTRIBUTION}
        
        # Type mapping for shortened names
        type_mapping = {
            'api': 'api_client',
            'auth': 'auth_handler',
            'cache': 'cache_manager',
            'config': 'config_handler',
            'data': 'data_model',
            'task': 'task_processor',
            'log': 'log_processor',
            'db': 'data_processor',
            'payment': 'task_processor'
        }
        
        try:
            logger.info(f"Analyzing directory: {self.generated_dir}")
            if not os.path.exists(self.generated_dir):
                logger.warning(f"Directory does not exist: {self.generated_dir}")
                return distribution
            
            files = os.listdir(self.generated_dir)
            logger.info(f"Found {len(files)} files in directory")
            
            for filename in files:
                if filename.endswith('.py'):
                    # Handle both formats: "type.py" and "type_uuid.py"
                    base_name = filename.rsplit('.', 1)[0]  # Remove .py extension
                    short_type = base_name.split('_')[0]  # Get type before underscore or whole name if no underscore
                    
                    # Map the short type to full type
                    script_type = type_mapping.get(short_type)
                    
                    logger.info(f"Processing file: {filename} -> short_type: {short_type} -> mapped_type: {script_type}")
                    if script_type in distribution:
                        distribution[script_type] += 1
                        logger.info(f"Counted {script_type} script: {filename}")
                    else:
                        logger.warning(f"Unknown script type '{short_type}' in file: {filename}")
            
            logger.info("Final distribution:")
            for script_type, count in sorted(distribution.items()):
                logger.info(f"  {script_type}: {count}")
        
        except Exception as e:
            logger.error(f"Error analyzing existing files: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        return distribution

    def get_weighted_script_type(self) -> str:
        """Get a script type weighted towards under-represented types."""
        total_files = sum(self.current_distribution.values()) or 1  # Avoid division by zero
        
        # Calculate current percentages
        current_percentages = {
            script_type: count / total_files 
            for script_type, count in self.current_distribution.items()
        }
        
        # Calculate how far each type is from its target
        deficits = {
            script_type: self.TARGET_DISTRIBUTION[script_type] - current_percentages.get(script_type, 0)
            for script_type in self.TARGET_DISTRIBUTION
        }
        
        # Add a small random factor to avoid getting stuck in patterns
        randomized_deficits = {
            script_type: deficit + random.uniform(0, 0.1)  # Add up to 10% randomness
            for script_type, deficit in deficits.items()
        }
        
        # Weight more heavily towards types with larger deficits
        weights = {
            script_type: max(0.1, deficit * 10)  # Ensure at least a small chance for all types
            for script_type, deficit in randomized_deficits.items()
        }
        
        # Select a type based on weights
        script_types = list(weights.keys())
        weights_list = list(weights.values())
        total_weight = sum(weights_list)
        normalized_weights = [w/total_weight for w in weights_list]
        
        selected_type = random.choices(script_types, weights=normalized_weights, k=1)[0]
        
        # Update the distribution
        self.current_distribution[selected_type] += 1
        
        return selected_type
    
    def get_distribution_stats(self) -> Dict[str, Dict[str, float]]:
        """Get current distribution statistics."""
        total_files = sum(self.current_distribution.values()) or 1
        
        return {
            "current_distribution": {
                script_type: count / total_files
                for script_type, count in self.current_distribution.items()
            },
            "target_distribution": self.TARGET_DISTRIBUTION,
            "total_files": total_files
        }

def test_distribution_counting():
    """Debug function to test distribution counting."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    generated_dir = os.path.join(os.path.dirname(script_dir), 'generated')
    
    print(f"\n🔍 Testing distribution counting in: {generated_dir}")
    
    try:
        files = os.listdir(generated_dir)
        print(f"\nFound {len(files)} total files")
        
        # Count Python files and their types
        py_files = [f for f in files if f.endswith('.py')]
        print(f"\nPython files ({len(py_files)}):")
        for filename in sorted(py_files):
            base_name = filename.rsplit('.', 1)[0]
            script_type = base_name.split('_')[0]
            if script_type == "db":
                script_type = "data_processor"
            elif script_type == "payment":
                script_type = "task_processor"
            print(f"  {filename:<40} -> {script_type}")
        
        # Initialize distribution counter
        distribution = ScriptTypeDistribution(generated_dir)
        counts = distribution.current_distribution
        
        print("\n📊 Final counts:")
        for script_type, count in sorted(counts.items()):
            print(f"  {script_type:<20} : {count:>3} files")
        
        total = sum(counts.values())
        print(f"\nTotal counted: {total} files")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        print(traceback.format_exc())

def generate_sample_scripts() -> None:
    """Generate different Python scripts using various templates."""
    generator = CodeGenerator()
    prompt_generator = PromptGenerator()
    
    print("\n🚀 Starting script generation process...")
    num_scripts = random.randint(15, 25)  # Random number of scripts to generate
    
    # Analyze existing files to determine script type distribution
    distribution = ScriptTypeDistribution(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generated'))
    
    for i in range(num_scripts):
        try:
            # Generate prompt using the new generator
            prompt = prompt_generator.generate_prompt()
            
            # Generate the script
            request = CodeGenerationRequest(
                description=prompt,
                template_name=random.choice(["script", "class"]),
                output_file=f"generated/{distribution.get_weighted_script_type()}_{generate_short_uuid()}.py",
                additional_context=get_random_context()
            )
            script_content = generator.generate_code(request)
            if not script_content:
                continue
            
            print(f"✅ Generated script {i+1}/{num_scripts}: {request.output_file}")
            
            # Update the distribution
            distribution.current_distribution[distribution.get_weighted_script_type()] += 1
            
        except Exception as e:
            print(f"❌ Error generating script {i+1}: {str(e)}")
            continue
    
    print("\n📊 Final distribution of generated scripts:")
    for script_type, count in sorted(distribution.current_distribution.items()):
        print(f"  {script_type}: {count}")
    
    print("\n🎉 Script generation completed!")
    print(f"📊 Summary:")
    print(f"   - Total scripts: {sum(distribution.current_distribution.values())}")
    print(f"   - Location: {os.path.abspath('generated')}\n")

if __name__ == "__main__":
    # Run test function first
    test_distribution_counting()
    
    # Then run the main script generation
    generate_sample_scripts()
    logger.info("Sample script generation completed successfully")
