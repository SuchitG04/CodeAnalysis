#!/usr/bin/env python3

import os
import ast
import json
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DataModelInfo:
    """Information about a data model found in a Python file."""
    class_name: str
    fields: List[str]
    field_types: Dict[str, str]
    docstring: Optional[str] = None

@dataclass
class DataSourceInfo:
    """Information about a data source and its fields."""
    source_type: str  # e.g., 'file', 'database', 'api'
    source_name: str  # e.g., filename, table name, endpoint
    fields: Set[str]  # field names found in the source
    field_types: Dict[str, str]  # mapping of field names to their types

@dataclass
class SecurityInfo:
    """Information about security and compliance features."""
    auth_methods: Set[str]
    compliance_refs: Set[str]
    encryption_usage: Set[str]
    audit_logs: Set[str]
    access_controls: Set[str]

@dataclass
class ArchitectureInfo:
    """Information about architectural patterns used."""
    patterns: Set[str]
    event_handlers: Set[str]
    messaging_patterns: Set[str]

@dataclass
class ErrorHandlingInfo:
    """Information about error handling patterns."""
    retry_mechanisms: Set[str]
    validation_checks: Set[str]
    rate_limits: Set[str]
    timeout_handlers: Set[str]

@dataclass
class FileAnalysis:
    """Analysis results for a single Python file."""
    file_name: str
    data_models: List[DataModelInfo]
    data_sources: List[DataSourceInfo]
    data_sinks: Set[str]
    security_info: SecurityInfo
    architecture_info: ArchitectureInfo
    error_handling: ErrorHandlingInfo
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'file_name': self.file_name,
            'data_models': [
                {
                    'class_name': model.class_name,
                    'fields': model.fields,
                    'field_types': model.field_types,
                    'docstring': model.docstring
                }
                for model in self.data_models
            ],
            'data_sources': [
                {
                    'source_type': source.source_type,
                    'source_name': source.source_name,
                    'fields': list(source.fields),
                    'field_types': source.field_types
                }
                for source in self.data_sources
            ],
            'data_sinks': list(self.data_sinks),
            'security_info': {
                'auth_methods': list(self.security_info.auth_methods),
                'compliance_refs': list(self.security_info.compliance_refs),
                'encryption_usage': list(self.security_info.encryption_usage),
                'audit_logs': list(self.security_info.audit_logs),
                'access_controls': list(self.security_info.access_controls)
            },
            'architecture_info': {
                'patterns': list(self.architecture_info.patterns),
                'event_handlers': list(self.architecture_info.event_handlers),
                'messaging_patterns': list(self.architecture_info.messaging_patterns)
            },
            'error_handling': {
                'retry_mechanisms': list(self.error_handling.retry_mechanisms),
                'validation_checks': list(self.error_handling.validation_checks),
                'rate_limits': list(self.error_handling.rate_limits),
                'timeout_handlers': list(self.error_handling.timeout_handlers)
            }
        }

class DataSourceSinkVisitor(ast.NodeVisitor):
    """AST visitor to find data sources, sinks, and their fields."""
    
    def __init__(self):
        self.sources: List[DataSourceInfo] = []
        self.sinks: Set[str] = set()
        
        # Patterns for identifying data source types
        self.file_patterns = {'open', 'read', 'load', 'parse'}
        self.db_patterns = {'query', 'select', 'find', 'fetch'}
        self.api_patterns = {'get', 'request', 'fetch'}
        
    def visit_Call(self, node: ast.Call) -> None:
        """Visit function calls to identify data sources and sinks."""
        func_name = ''
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            
        # Check for file operations
        if func_name in self.file_patterns:
            source_info = self._extract_file_source(node)
            if source_info:
                self.sources.append(source_info)
                
        # Check for database operations
        elif func_name in self.db_patterns:
            source_info = self._extract_db_source(node)
            if source_info:
                self.sources.append(source_info)
                
        # Check for API operations
        elif func_name in self.api_patterns:
            source_info = self._extract_api_source(node)
            if source_info:
                self.sources.append(source_info)
                
        # Check for data sinks
        if func_name in {'write', 'save', 'insert', 'update', 'post', 'put'}:
            self.sinks.add(func_name)
            
        self.generic_visit(node)
    
    def _extract_file_source(self, node: ast.Call) -> Optional[DataSourceInfo]:
        """Extract information from file operations."""
        fields = set()
        field_types = {}
        
        # Try to get filename from arguments
        filename = None
        if node.args:
            if isinstance(node.args[0], ast.Str):
                filename = node.args[0].s
                
        if filename:
            # Look for field access in the surrounding code
            fields, field_types = self._extract_fields_from_context(node)
            return DataSourceInfo(
                source_type='file',
                source_name=filename,
                fields=fields,
                field_types=field_types
            )
        return None
    
    def _extract_db_source(self, node: ast.Call) -> Optional[DataSourceInfo]:
        """Extract information from database operations."""
        fields = set()
        field_types = {}
        
        # Try to extract table name and fields from SQL-like queries
        table_name = None
        if isinstance(node.args[0], ast.Str):
            query = node.args[0].s.lower()
            # Simple SQL parsing
            if 'select' in query and 'from' in query:
                parts = query.split('from')
                if len(parts) > 1:
                    table_parts = parts[1].strip().split()
                    if table_parts:
                        table_name = table_parts[0]
                        
                # Extract fields from SELECT clause
                select_parts = parts[0].replace('select', '').strip()
                if select_parts != '*':
                    fields = {f.strip() for f in select_parts.split(',')}
        
        if table_name:
            return DataSourceInfo(
                source_type='database',
                source_name=table_name,
                fields=fields,
                field_types=field_types
            )
        return None
    
    def _extract_api_source(self, node: ast.Call) -> Optional[DataSourceInfo]:
        """Extract information from API operations."""
        fields = set()
        field_types = {}
        
        # Try to get API endpoint from arguments
        endpoint = None
        if node.args:
            if isinstance(node.args[0], ast.Str):
                endpoint = node.args[0].s
                
        if endpoint:
            # Look for field access in the surrounding code
            fields, field_types = self._extract_fields_from_context(node)
            return DataSourceInfo(
                source_type='api',
                source_name=endpoint,
                fields=fields,
                field_types=field_types
            )
        return None
    
    def _extract_fields_from_context(self, node: ast.Call) -> Tuple[Set[str], Dict[str, str]]:
        """Extract fields by looking at how the data is used after being read."""
        fields = set()
        field_types = {}
        
        # Get the parent function or class
        parent = self._get_parent_scope(node)
        if parent:
            # Look for attribute access and dictionary lookups
            for child in ast.walk(parent):
                if isinstance(child, ast.Attribute):
                    fields.add(child.attr)
                elif isinstance(child, ast.Subscript) and isinstance(child.slice, ast.Str):
                    fields.add(child.slice.s)
                    
                # Try to infer types
                if isinstance(child, ast.Assign):
                    if isinstance(child.value, ast.Attribute) and child.value.attr in fields:
                        target_name = child.targets[0].id if isinstance(child.targets[0], ast.Name) else None
                        if target_name and hasattr(child, 'type_comment'):
                            field_types[child.value.attr] = child.type_comment
        
        return fields, field_types
    
    def _get_parent_scope(self, node: ast.AST) -> Optional[ast.AST]:
        """Get the parent function or class containing this node."""
        parent = node
        while hasattr(parent, 'parent'):
            parent = parent.parent
            if isinstance(parent, (ast.FunctionDef, ast.ClassDef)):
                return parent
        return None

class DataModelVisitor(ast.NodeVisitor):
    """AST visitor to find data models and their fields."""
    
    def __init__(self):
        self.models: List[DataModelInfo] = []
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definitions to extract model information."""
        # Get docstring if present
        docstring = ast.get_docstring(node)
        
        fields = []
        field_types = {}
        
        # Analyze class body
        for item in node.body:
            # Check class variables and annotations
            if isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name):
                    fields.append(item.target.id)
                    if isinstance(item.annotation, ast.Name):
                        field_types[item.target.id] = item.annotation.id
                    elif isinstance(item.annotation, ast.Subscript):
                        if isinstance(item.annotation.value, ast.Name):
                            field_types[item.target.id] = f"{item.annotation.value.id}[...]"
            
            # Check __init__ method for instance variables
            elif isinstance(item, ast.FunctionDef) and item.name == '__init__':
                for stmt in item.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                                fields.append(target.attr)
        
        if fields:  # Only add if fields were found
            self.models.append(DataModelInfo(
                class_name=node.name,
                fields=fields,
                field_types=field_types,
                docstring=docstring
            ))
        
        self.generic_visit(node)

class SecurityVisitor(ast.NodeVisitor):
    """AST visitor to find security and compliance patterns."""
    
    def __init__(self):
        self.auth_methods: Set[str] = set()
        self.compliance_refs: Set[str] = set()
        self.encryption_usage: Set[str] = set()
        self.audit_logs: Set[str] = set()
        self.access_controls: Set[str] = set()
        
        # Patterns to look for
        self.auth_patterns = {
            'token': {'jwt', 'bearer', 'token', 'oauth'},
            'api_key': {'api_key', 'apikey', 'key'},
            'session': {'session', 'cookie'}
        }
        
        self.compliance_patterns = {
            'gdpr': {'gdpr', 'privacy', 'data_protection'},
            'hipaa': {'hipaa', 'phi', 'health'},
            'pci': {'pci', 'payment', 'card'},
            'ferpa': {'ferpa', 'education', 'student'}
        }
        
        self.encryption_patterns = {
            'encrypt', 'decrypt', 'hash', 'salt', 'cipher'
        }
        
        self.audit_patterns = {
            'audit', 'log', 'track', 'monitor'
        }
        
        self.access_patterns = {
            'rbac', 'acl', 'permission', 'role', 'authorize'
        }
    
    def visit_Call(self, node: ast.Call):
        """Visit function calls to identify security patterns."""
        func_name = ''
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        
        func_name = func_name.lower()
        
        # Check auth methods
        for auth_type, patterns in self.auth_patterns.items():
            if any(pattern in func_name for pattern in patterns):
                self.auth_methods.add(f"{auth_type}:{func_name}")
        
        # Check encryption
        if any(pattern in func_name for pattern in self.encryption_patterns):
            self.encryption_usage.add(func_name)
        
        # Check audit logging
        if any(pattern in func_name for pattern in self.audit_patterns):
            self.audit_logs.add(func_name)
        
        # Check access controls
        if any(pattern in func_name for pattern in self.access_patterns):
            self.access_controls.add(func_name)
        
        self.generic_visit(node)
    
    def visit_Str(self, node: ast.Str):
        """Visit string literals to find compliance references."""
        text = node.s.lower()
        for compliance_type, patterns in self.compliance_patterns.items():
            if any(pattern in text for pattern in patterns):
                self.compliance_refs.add(f"{compliance_type}:{text[:50]}")

class ArchitectureVisitor(ast.NodeVisitor):
    """AST visitor to find architectural patterns."""
    
    def __init__(self):
        self.patterns: Set[str] = set()
        self.event_handlers: Set[str] = set()
        self.messaging_patterns: Set[str] = set()
        
        self.pattern_indicators = {
            'microservice': {'service', 'api', 'gateway'},
            'event_driven': {'event', 'handler', 'listener'},
            'circuit_breaker': {'circuit', 'breaker', 'fallback'},
            'cqrs': {'command', 'query', 'repository'},
            'saga': {'saga', 'transaction', 'compensate'}
        }
        
        self.messaging_indicators = {
            'pubsub': {'publish', 'subscribe', 'topic'},
            'queue': {'queue', 'message', 'broker'},
            'stream': {'stream', 'kafka', 'kinesis'}
        }
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Visit class definitions to identify architectural patterns."""
        class_name = node.name.lower()
        
        for pattern_type, indicators in self.pattern_indicators.items():
            if any(indicator in class_name for indicator in indicators):
                self.patterns.add(f"{pattern_type}:{node.name}")
        
        for msg_type, indicators in self.messaging_indicators.items():
            if any(indicator in class_name for indicator in indicators):
                self.messaging_patterns.add(f"{msg_type}:{node.name}")
        
        # Look for event handlers in method decorators
        for method in node.body:
            if isinstance(method, ast.FunctionDef):
                for decorator in method.decorator_list:
                    if isinstance(decorator, ast.Name):
                        decorator_name = decorator.id.lower()
                        if any(indicator in decorator_name for indicator in self.pattern_indicators['event_driven']):
                            self.event_handlers.add(f"handler:{node.name}.{method.name}")
        
        self.generic_visit(node)

class ErrorHandlingVisitor(ast.NodeVisitor):
    """AST visitor to find error handling patterns."""
    
    def __init__(self):
        self.retry_mechanisms: Set[str] = set()
        self.validation_checks: Set[str] = set()
        self.rate_limits: Set[str] = set()
        self.timeout_handlers: Set[str] = set()
        
        self.retry_patterns = {'retry', 'backoff', 'attempt'}
        self.validation_patterns = {'validate', 'check', 'verify'}
        self.rate_limit_patterns = {'rate', 'limit', 'throttle'}
        self.timeout_patterns = {'timeout', 'deadline', 'wait'}
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions to identify error handling patterns."""
        func_name = node.name.lower()
        
        # Check function names for patterns
        if any(pattern in func_name for pattern in self.retry_patterns):
            self.retry_mechanisms.add(f"function:{node.name}")
        if any(pattern in func_name for pattern in self.validation_patterns):
            self.validation_checks.add(f"function:{node.name}")
        if any(pattern in func_name for pattern in self.rate_limit_patterns):
            self.rate_limits.add(f"function:{node.name}")
        if any(pattern in func_name for pattern in self.timeout_patterns):
            self.timeout_handlers.add(f"function:{node.name}")
        
        # Look for try-except blocks with specific error types
        for item in ast.walk(node):
            if isinstance(item, ast.ExceptHandler):
                if isinstance(item.type, ast.Name):
                    error_name = item.type.id.lower()
                    if 'timeout' in error_name:
                        self.timeout_handlers.add(f"except:{node.name}:{error_name}")
                    elif any(pattern in error_name for pattern in self.retry_patterns):
                        self.retry_mechanisms.add(f"except:{node.name}:{error_name}")
        
        self.generic_visit(node)

def analyze_file(file_path: str) -> FileAnalysis:
    """Analyze a Python file for various attributes."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Add parent references to AST nodes
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                child.parent = parent
        
        # Extract data models
        model_visitor = DataModelVisitor()
        model_visitor.visit(tree)
        
        # Extract data sources and sinks
        source_sink_visitor = DataSourceSinkVisitor()
        source_sink_visitor.visit(tree)
        
        # Extract security patterns
        security_visitor = SecurityVisitor()
        security_visitor.visit(tree)
        
        # Extract architectural patterns
        arch_visitor = ArchitectureVisitor()
        arch_visitor.visit(tree)
        
        # Extract error handling patterns
        error_visitor = ErrorHandlingVisitor()
        error_visitor.visit(tree)
        
        return FileAnalysis(
            file_name=os.path.basename(file_path),
            data_models=model_visitor.models,
            data_sources=source_sink_visitor.sources,
            data_sinks=source_sink_visitor.sinks,
            security_info=SecurityInfo(
                auth_methods=security_visitor.auth_methods,
                compliance_refs=security_visitor.compliance_refs,
                encryption_usage=security_visitor.encryption_usage,
                audit_logs=security_visitor.audit_logs,
                access_controls=security_visitor.access_controls
            ),
            architecture_info=ArchitectureInfo(
                patterns=arch_visitor.patterns,
                event_handlers=arch_visitor.event_handlers,
                messaging_patterns=arch_visitor.messaging_patterns
            ),
            error_handling=ErrorHandlingInfo(
                retry_mechanisms=error_visitor.retry_mechanisms,
                validation_checks=error_visitor.validation_checks,
                rate_limits=error_visitor.rate_limits,
                timeout_handlers=error_visitor.timeout_handlers
            )
        )
        
    except Exception as e:
        logger.error(f"Error analyzing file {file_path}: {str(e)}")
        return None

def analyze_directory(directory_path: str) -> List[Dict[str, Any]]:
    """Analyze all Python files in a directory."""
    results = []
    
    try:
        for file_name in os.listdir(directory_path):
            if file_name.endswith('.py'):
                file_path = os.path.join(directory_path, file_name)
                logger.info(f"Analyzing {file_name}...")
                
                analysis = analyze_file(file_path)
                if analysis:
                    results.append(analysis.to_dict())
    
    except Exception as e:
        logger.error(f"Error processing directory {directory_path}: {str(e)}")
    
    return results

def main():
    """Main function to run the analysis."""
    # Get the absolute path to the generated directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    generated_dir = os.path.join(os.path.dirname(script_dir), 'generated')
    output_file = os.path.join(os.path.dirname(script_dir), 'analysis_results.json')
    
    logger.info(f"Starting analysis of directory: {generated_dir}")
    
    # Analyze all Python files
    results = analyze_directory(generated_dir)
    
    # Write results to JSON file
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Analysis results written to: {output_file}")
    except Exception as e:
        logger.error(f"Error writing results to {output_file}: {str(e)}")

if __name__ == "__main__":
    main()
