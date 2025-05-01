import os
import re
import shutil
import datetime
import json
import subprocess
import sys
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, session
from flask_bootstrap import Bootstrap5

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
app.config['SESSION_TYPE'] = 'filesystem'
bootstrap = Bootstrap5(app)

# Ensure cases directory exists
CASES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cases')
if not os.path.exists(CASES_DIR):
    os.makedirs(CASES_DIR)

# Ensure plugins directory exists
PLUGINS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plugins')
if not os.path.exists(PLUGINS_DIR):
    os.makedirs(PLUGINS_DIR)

# Add plugins directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import plugin base module
try:
    from plugin_base import get_all_plugins, WebToolsPlugin
    PLUGIN_SYSTEM_AVAILABLE = True
except ImportError:
    PLUGIN_SYSTEM_AVAILABLE = False

@app.route('/')
def index():
    # Get all cases (directories in the cases folder) with file counts
    cases_with_counts = []
    if os.path.exists(CASES_DIR):
        case_dirs = [d for d in os.listdir(CASES_DIR) 
                   if os.path.isdir(os.path.join(CASES_DIR, d))]
        
        # For each case, count the files
        for case in case_dirs:
            case_path = os.path.join(CASES_DIR, case)
            file_count = len([f for f in os.listdir(case_path) 
                            if os.path.isfile(os.path.join(case_path, f))])
            cases_with_counts.append({
                'name': case,
                'file_count': file_count
            })
    
    # Count plugins (Python scripts in the plugins folder, non-recursive)
    plugin_count = 0
    if os.path.exists(PLUGINS_DIR):
        plugin_count = len([f for f in os.listdir(PLUGINS_DIR) 
                          if os.path.isfile(os.path.join(PLUGINS_DIR, f)) and f.endswith('.py')])
    
    return render_template('index.html', cases=cases_with_counts, plugin_count=plugin_count)

@app.route('/create_case', methods=['POST'])
def create_case():
    case_name = request.form.get('case_name', '').strip()
    action = request.form.get('action', 'create')

    # Validate case name (only English letters and numbers)
    if not re.match(r'^[a-zA-Z0-9]+$', case_name):
        flash('Case name can only contain English letters and numbers', 'danger')
        return redirect(url_for('index'))
    
    case_path = os.path.join(CASES_DIR, case_name)
    
    # Check if case already exists
    if os.path.exists(case_path):
        flash(f'Case "{case_name}" already exists', 'danger')
    else:
        os.makedirs(case_path)
        # Do not show positive flash message

    if action == 'create_and_open' and os.path.exists(case_path):
        return redirect(url_for('view_case', case_name=case_name))
    else:
        return redirect(url_for('index'))

@app.route('/delete_case/<case_name>', methods=['POST'])
def delete_case(case_name):
    case_path = os.path.join(CASES_DIR, case_name)
    
    # Check if case exists
    if os.path.exists(case_path):
        shutil.rmtree(case_path)
        flash(f'Case "{case_name}" deleted successfully', 'success')
    else:
        flash(f'Case "{case_name}" does not exist', 'danger')
    
    return redirect(url_for('index'))

@app.route('/case/<case_name>')
def view_case(case_name):
    case_path = os.path.join(CASES_DIR, case_name)
    
    # Check if case exists
    if not os.path.exists(case_path):
        flash(f'Case "{case_name}" does not exist', 'danger')
        return redirect(url_for('index'))
    
    # Get files in the case directory
    files = []
    file_count = 0
    if os.path.exists(case_path):
        for filename in os.listdir(case_path):
            file_path = os.path.join(case_path, filename)
            if os.path.isfile(file_path):
                file_count += 1
                # Get file size in KB
                size_kb = os.path.getsize(file_path) / 1024
                # Get file modification time
                mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                
                files.append({
                    'name': filename,
                    'size': f'{size_kb:.2f} KB',
                    'modified': mod_time.strftime('%Y-%m-%d %H:%M:%S')
                })
    
    return render_template('case.html', case_name=case_name, files=files, file_count=file_count)

@app.route('/view_file/<case_name>/<filename>')
def view_file(case_name, filename):
    import mimetypes
    import binascii
    case_path = os.path.join(CASES_DIR, case_name)
    file_path = os.path.join(case_path, filename)
    if not os.path.exists(file_path):
        flash('File not found', 'danger')
        return redirect(url_for('view_case', case_name=case_name))

    # Default mode and content
    viewer_type = 'text'
    content = ''
    try:
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                import json
                data = json.load(f)
                content = json.dumps(data, indent=2, ensure_ascii=False)
                json_obj = data
                viewer_type = 'json'
        else:
            # Try to read as text
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    viewer_type = 'text'
            except Exception:
                # Binary: show hex dump of first 512 bytes
                with open(file_path, 'rb') as f:
                    raw = f.read(512)
                    # Format hex output similar to magic_bytes_formatted (space-separated, 16 bytes per line)
                    hex_bytes = [f'{b:02x}' for b in raw]
                    hex_lines = []
                    ascii_lines = []
                    for i in range(0, len(hex_bytes), 16):
                        chunk = hex_bytes[i:i+16]
                        hex_line = ' '.join(chunk)
                        ascii_line = ''.join(chr(int(h, 16)) if 32 <= int(h, 16) <= 126 else '.' for h in chunk)
                        hex_lines.append(hex_line)
                        ascii_lines.append(ascii_line)
                    lines = list(zip(hex_lines, ascii_lines))
                    viewer_type = 'hex'
    except Exception as e:
        flash(f'Error reading file: {str(e)}', 'danger')
        return redirect(url_for('view_case', case_name=case_name))
    if viewer_type == 'hex':
        return render_template('file_viewer.html', case_name=case_name, filename=filename, lines=lines, viewer_type=viewer_type)
    elif viewer_type == 'json':
        return render_template('file_viewer.html', case_name=case_name, filename=filename, content=content, viewer_type=viewer_type, json_obj=json_obj)
    else:
        return render_template('file_viewer.html', case_name=case_name, filename=filename, content=content, viewer_type=viewer_type)


@app.route('/plugins')
def plugins():
    # Get all plugins with their info
    plugin_info = []
    
    if PLUGIN_SYSTEM_AVAILABLE:
        # Use the plugin system to get all plugins
        all_plugins = get_all_plugins(PLUGINS_DIR)
        for name, plugin in all_plugins.items():
            plugin_info.append(plugin.get_info())
    else:
        # Fallback to just listing Python files
        if os.path.exists(PLUGINS_DIR):
            plugin_files = [f for f in os.listdir(PLUGINS_DIR) 
                         if os.path.isfile(os.path.join(PLUGINS_DIR, f)) and f.endswith('.py')]
            for plugin_file in plugin_files:
                if plugin_file != 'plugin_base.py' and plugin_file != '__init__.py':
                    plugin_info.append({
                        'name': os.path.splitext(plugin_file)[0],
                        'description': 'No description available',
                        'version': 'Unknown',
                        'author': 'Unknown',
                        'parameters': []
                    })
    
    return render_template('plugins.html', plugins=plugin_info)

# API endpoint for JSON plugin list
@app.route('/api/plugins')
def api_plugins():
    plugin_list = []
    if PLUGIN_SYSTEM_AVAILABLE:
        all_plugins = get_all_plugins(PLUGINS_DIR)
        for name, plugin in all_plugins.items():
            plugin_list.append({
                'name': plugin.name,
                'description': plugin.description
            })
    else:
        if os.path.exists(PLUGINS_DIR):
            plugin_files = [f for f in os.listdir(PLUGINS_DIR) 
                         if os.path.isfile(os.path.join(PLUGINS_DIR, f)) and f.endswith('.py')]
            for plugin_file in plugin_files:
                if plugin_file != 'plugin_base.py' and plugin_file != '__init__.py':
                    plugin_list.append({
                        'name': os.path.splitext(plugin_file)[0],
                        'description': 'No description available'
                    })
    return jsonify(plugin_list)


@app.route('/plugin_info/<plugin_name>')
def plugin_info(plugin_name):
    """Get detailed information about a specific plugin"""
    if not PLUGIN_SYSTEM_AVAILABLE:
        return jsonify({'error': 'Plugin system not available'}), 400
    
    all_plugins = get_all_plugins(PLUGINS_DIR)
    if plugin_name not in all_plugins:
        return jsonify({'error': f'Plugin {plugin_name} not found'}), 404
    
    plugin = all_plugins[plugin_name]
    return jsonify(plugin.get_info())

@app.route('/run_plugin/<case_name>', methods=['POST'])
def run_plugin(case_name):
    """Run a plugin on a case"""
    if not PLUGIN_SYSTEM_AVAILABLE:
        flash('Plugin system not available', 'danger')
        return redirect(url_for('view_case', case_name=case_name))
    
    # Check if case exists
    case_path = os.path.join(CASES_DIR, case_name)
    if not os.path.exists(case_path):
        flash(f'Case "{case_name}" does not exist', 'danger')
        return redirect(url_for('index'))
    
    # Get plugin name and parameters from form
    plugin_name = request.form.get('plugin_name')
    if not plugin_name:
        flash('No plugin specified', 'danger')
        return redirect(url_for('view_case', case_name=case_name))
    
    # Load the plugin
    all_plugins = get_all_plugins(PLUGINS_DIR)
    if plugin_name not in all_plugins:
        flash(f'Plugin {plugin_name} not found', 'danger')
        return redirect(url_for('view_case', case_name=case_name))
    
    plugin = all_plugins[plugin_name]
    
    # Extract parameters from form
    params = {}
    for param in plugin.parameters:
        param_name = param['name']
        if param_name in request.form:
            # Convert parameter to the correct type
            if param['type'] == 'boolean':
                params[param_name] = request.form.get(param_name) == 'on'
            elif param['type'] == 'integer':
                try:
                    params[param_name] = int(request.form.get(param_name))
                except ValueError:
                    params[param_name] = param.get('default', 0)
            else:  # string and other types
                params[param_name] = request.form.get(param_name)
    
    # Run the plugin
    try:
        result = plugin.run(case_path, params)
        
        if not result.get('success', False):
            if 'message' in result:
                flash(f"Plugin error: {result['message']}", 'danger')
        # Store the result in session for display
        if 'output' in result and result['output']:
            # Convert any non-serializable objects to strings
            output = json.dumps(result['output'])
            # Store in session with a unique key
            session_key = f"plugin_result_{plugin_name}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            session[session_key] = output
            return redirect(url_for('view_plugin_result', case_name=case_name, result_key=session_key))
        
    except Exception as e:
        flash(f"Error running plugin: {str(e)}", 'danger')
    
    return redirect(url_for('view_case', case_name=case_name))

@app.route('/view_plugin_result/<case_name>/<result_key>')
def view_plugin_result(case_name, result_key):
    """View the result of a plugin run"""
    if result_key not in session:
        flash('Plugin result not found', 'danger')
        return redirect(url_for('view_case', case_name=case_name))
    
    try:
        result = json.loads(session[result_key])
        return render_template('plugin_result.html', case_name=case_name, result=result)
    except Exception as e:
        flash(f"Error displaying plugin result: {str(e)}", 'danger')
        return redirect(url_for('view_case', case_name=case_name))

@app.route('/upload_file/<case_name>', methods=['POST'])
def upload_file(case_name):
    case_path = os.path.join(CASES_DIR, case_name)
    
    # Check if case exists
    if not os.path.exists(case_path):
        flash(f'Case "{case_name}" does not exist', 'danger')
        return redirect(url_for('index'))
    
    # Check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('view_case', case_name=case_name))
    
    file = request.files['file']
    
    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('view_case', case_name=case_name))
    
    # Secure the filename to prevent directory traversal attacks
    filename = secure_filename(file.filename)
    file_path = os.path.join(case_path, filename)
    
    # Check if file already exists
    if os.path.exists(file_path):
        flash(f'File "{filename}" already exists', 'danger')
    else:
        file.save(file_path)
        # Do not show positive flash message for successful upload
    
    return redirect(url_for('view_case', case_name=case_name))

@app.route('/delete_file/<case_name>/<filename>', methods=['POST'])
def delete_file(case_name, filename):
    case_path = os.path.join(CASES_DIR, case_name)
    file_path = os.path.join(case_path, secure_filename(filename))
    
    # Check if file exists
    if os.path.exists(file_path) and os.path.isfile(file_path):
        os.remove(file_path)
        flash(f'File "{filename}" deleted successfully', 'success')
    else:
        flash(f'File "{filename}" does not exist', 'danger')
    
    return redirect(url_for('view_case', case_name=case_name))

@app.route('/download_file/<case_name>/<filename>')
def download_file(case_name, filename):
    case_path = os.path.join(CASES_DIR, case_name)
    return send_from_directory(case_path, secure_filename(filename))

if __name__ == '__main__':
    app.run(debug=True)
