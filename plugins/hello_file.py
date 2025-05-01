#!/usr/bin/env python
"""
Hello File Plugin for Web Tools Framework
Shows basic file details (name, size, modification time, and type by extension)
"""
import os
import sys
import datetime
from typing import Dict, Any, List

# Import the plugin base class
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plugin_base import WebToolsPlugin

class HelloFilePlugin(WebToolsPlugin):
    """Plugin to show basic file details"""

    @property
    def name(self) -> str:
        return "hello_file"

    @property
    def description(self) -> str:
        return "Shows basic details about a file: name, size, modified time, and extension."

    @property
    def long_description(self) -> str:
        return "This plugin displays basic information about a file in the case: its name, size (in bytes), last modification time, and its file extension/type."

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def author(self) -> str:
        return "Web Tools Framework Team"

    @property
    def parameters(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "filename",
                "type": "string",
                "description": "Name of the file to show details for",
                "required": True
            }
        ]

    def run(self, case_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # Validate parameters
        errors = self.validate_parameters(params)
        if errors:
            return {
                "success": False,
                "message": "Parameter validation failed",
                "errors": errors,
                "output": None
            }

        filename = params["filename"]
        file_path = os.path.join(case_path, filename)
        if not os.path.exists(file_path):
            return {
                "success": False,
                "message": f"File '{filename}' not found in case directory",
                "output": None
            }

        size = os.path.getsize(file_path)
        mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        ext = os.path.splitext(filename)[1].lower() or "(none)"

        output = {
            "filename": filename,
            "size_bytes": size,
            "modified": mod_time,
            "extension": ext
        }

        return {
            "success": True,
            "message": f"Basic details for file '{filename}' shown successfully.",
            "output": output
        }

# This allows the plugin to be run directly from command line for testing
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hello File Plugin")
    parser.add_argument("--case-path", required=True, help="Path to the case directory")
    parser.add_argument("--filename", required=True, help="Name of the file to show details for")
    args = parser.parse_args()
    plugin = HelloFilePlugin()
    result = plugin.run(args.case_path, {"filename": args.filename})
    print(result)
