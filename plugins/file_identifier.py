#!/usr/bin/env python
"""
File Identifier Plugin for Web Tools Framework
Identifies file types using Google's Magika for accurate file type detection
"""
import os
import json
import sys
import datetime
from typing import Dict, Any, List, Optional

# Import the plugin base class
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plugin_base import WebToolsPlugin

class FileIdentifierPlugin(WebToolsPlugin):
    """Plugin to identify file types using Google's Magika for accurate file type detection"""
    
    @property
    def name(self) -> str:
        return "file_identifier"
    
    @property
    def description(self) -> str:
        return "Identifies file types using Google's Magika for accurate file type detection"
    
    @property
    def long_description(self) -> str:
        return "This plugin uses Google's Magika library to accurately identify file types based on content analysis rather than just file extensions. It analyzes the file's binary content to determine its actual type, which is useful for detecting file type mismatches or identifying unknown files."
    
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
                "description": "Name of the file to identify",
                "required": True
            },
            {
                "name": "detailed",
                "type": "boolean",
                "description": "Whether to include detailed information about the file",
                "required": False,
                "default": False
            }
        ]
    
    def run(self, case_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run the file identification process using Google's Magika"""
        # Validate parameters
        errors = self.validate_parameters(params)
        if errors:
            return {
                "success": False,
                "message": "Parameter validation failed",
                "errors": errors,
                "output": None
            }
        
        # Get parameters
        filename = params["filename"]
        detailed = params.get("detailed", False)
        
        # Check if file exists in case directory
        file_path = os.path.join(case_path, filename)
        if not os.path.exists(file_path):
            return {
                "success": False,
                "message": f"File '{filename}' not found in case directory",
                "output": None
            }
        
        try:
            # Try to import magika
            try:
                from magika import Magika
                magika_available = True
            except ImportError:
                magika_available = False
                
            # Get file size and basic info
            file_size = os.path.getsize(file_path)
            file_extension = os.path.splitext(filename)[1].lower()
            mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            
            # Prepare results
            results = {
                "file": filename,
                "path": file_path,
                "size": {
                    "bytes": file_size,
                    "formatted": self._format_size(file_size)
                },
                "extension": file_extension,
                "last_modified": mod_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Use Magika for file identification if available
            if magika_available:
                # Initialize Magika
                magika = Magika()
                
                # Identify the file
                result = magika.identify_path(file_path)
                
                # Add Magika results
                results["mime_type"] = result.output.mime_type
                results["file_type"] = result.output.ct_label
                results["group_type"] = result.output.group_label
                results["confidence"] = float(result.output.score)
            else:
                # Fallback to basic file type detection
                # Read first 16 bytes for magic number identification
                with open(file_path, 'rb') as f:
                    header = f.read(16)
                
                # Simple mime type mapping based on file extension
                extension_mime_map = {
                    '.txt': 'text/plain',
                    '.html': 'text/html',
                    '.htm': 'text/html',
                    '.pdf': 'application/pdf',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.mp3': 'audio/mpeg',
                    '.mp4': 'video/mp4',
                    '.zip': 'application/zip',
                    '.doc': 'application/msword',
                    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    '.xls': 'application/vnd.ms-excel',
                    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    '.ppt': 'application/vnd.ms-powerpoint',
                    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                }
                
                # Get mime type from extension or default to octet-stream
                mime_type = extension_mime_map.get(file_extension, 'application/octet-stream')
                
                # Add basic results
                results["mime_type"] = mime_type
                results["file_type"] = "Unknown (Magika not available)"
                results["group_type"] = "Unknown"
                results["confidence"] = 0.0
                results["note"] = "Google Magika is not installed. Install with: pip install magika"
            
            # Add detailed information if requested
            if detailed:
                # Get magic bytes (first 16 bytes as hex)
                with open(file_path, 'rb') as f:
                    magic_bytes = f.read(16).hex()
                
                # Try to determine text encoding for text files
                is_text = False
                encoding = "binary"
                
                # Simple check if file might be text
                if results["mime_type"].startswith("text/") or results["mime_type"] in [
                    "application/json", "application/xml", "application/javascript"
                ]:
                    is_text = True
                    encoding = "utf-8"  # Assume UTF-8 for text files
                
                # Add to results
                results["is_text"] = is_text
                results["encoding"] = encoding
                results["magic_bytes"] = magic_bytes
                results["magic_bytes_formatted"] = ' '.join(magic_bytes[i:i+2] for i in range(0, len(magic_bytes), 2))
            
            # Write results to a JSON file in the case directory
            output_file = os.path.join(case_path, f"{filename}_identification.json")
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Return success
            return {
                "success": True,
                "message": f"File identification completed for '{filename}'",
                "output": results,
                "output_file": output_file
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error identifying file: {str(e)}",
                "output": None
            }
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in a human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

# This allows the plugin to be run directly from command line for testing
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="File Identifier Plugin")
    parser.add_argument("--case-path", required=True, help="Path to the case directory")
    parser.add_argument("--filename", required=True, help="Name of the file to identify")
    parser.add_argument("--detailed", action="store_true", help="Include detailed information")
    
    args = parser.parse_args()
    
    plugin = FileIdentifierPlugin()
    result = plugin.run(args.case_path, {
        "filename": args.filename,
        "detailed": args.detailed
    })
    
    print(json.dumps(result, indent=2))
