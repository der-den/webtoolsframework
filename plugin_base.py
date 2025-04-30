#!/usr/bin/env python
"""
Plugin Base Module for Web Tools Framework
Defines the base structure and interfaces for plugins
"""
import json
import os
import sys
import argparse
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class WebToolsPlugin(ABC):
    """Base class for all Web Tools Framework plugins"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the plugin"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return a short description of what the plugin does (one line)"""
        pass
    
    @property
    @abstractmethod
    def long_description(self) -> str:
        """Return a detailed description of what the plugin does"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Return the version of the plugin"""
        pass
    
    @property
    @abstractmethod
    def author(self) -> str:
        """Return the author of the plugin"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> List[Dict[str, Any]]:
        """
        Return a list of parameters that the plugin accepts
        
        Each parameter should be a dictionary with the following keys:
        - name: The name of the parameter
        - type: The type of the parameter (string, integer, file, etc.)
        - description: A description of the parameter
        - required: Whether the parameter is required or optional
        - default: Default value for the parameter (for optional parameters)
        """
        pass
    
    @abstractmethod
    def run(self, case_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the plugin with the given parameters
        
        Args:
            case_path: Path to the case directory
            params: Dictionary of parameter names and values
            
        Returns:
            Dictionary containing the results of the plugin run
            Should include at least:
            - success: Boolean indicating if the plugin ran successfully
            - message: A message describing the result
            - output: The output of the plugin (text, file paths, etc.)
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Return information about the plugin in a standardized format"""
        return {
            "name": self.name,
            "description": self.description,
            "long_description": self.long_description,
            "version": self.version,
            "author": self.author,
            "parameters": self.parameters
        }
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate the provided parameters against the required parameters
        
        Returns:
            Dictionary of error messages, empty if all parameters are valid
        """
        errors = {}
        
        # Check for required parameters
        for param in self.parameters:
            if param.get("required", False) and param["name"] not in params:
                errors[param["name"]] = f"Required parameter '{param['name']}' is missing"
            
            # Type validation could be added here
        
        return errors

def load_plugin_from_file(plugin_file: str) -> Optional[WebToolsPlugin]:
    """
    Load a plugin from a Python file
    
    Args:
        plugin_file: Path to the plugin Python file
        
    Returns:
        An instance of the plugin, or None if loading failed
    """
    try:
        import importlib.util
        
        # Get the filename without extension as the module name
        module_name = os.path.splitext(os.path.basename(plugin_file))[0]
        
        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        if spec is None or spec.loader is None:
            return None
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find the plugin class (subclass of WebToolsPlugin)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, WebToolsPlugin) and attr != WebToolsPlugin:
                return attr()
        
        return None
    except Exception as e:
        print(f"Error loading plugin {plugin_file}: {str(e)}")
        return None

def get_all_plugins(plugins_dir: str) -> Dict[str, WebToolsPlugin]:
    """
    Get all plugins from the plugins directory
    
    Args:
        plugins_dir: Path to the plugins directory
        
    Returns:
        Dictionary mapping plugin names to plugin instances
    """
    plugins = {}
    
    if not os.path.exists(plugins_dir):
        return plugins
    
    for filename in os.listdir(plugins_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            plugin_path = os.path.join(plugins_dir, filename)
            plugin = load_plugin_from_file(plugin_path)
            if plugin:
                plugins[plugin.name] = plugin
    
    return plugins

if __name__ == "__main__":
    # This allows plugins to be run directly from the command line for testing
    print("This is the plugin base module and should not be run directly.")
    print("To run a plugin, use the Web Tools Framework interface or run the plugin file directly.")
