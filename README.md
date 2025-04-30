# Web Tools Framework

A Python-based framework using Flask and Bootstrap for offline web tools and case management.

## Features

- Create, delete, and access cases
- Each case is stored as a directory in the "cases" folder
- Case names are restricted to English letters and numbers
- Plugin management system for Python scripts
- Plugin counter showing available scripts in the plugins directory
- Fully functional offline (no internet connection required)
- Bootstrap-based responsive UI

## Setup

1. Make sure you have Python installed (Python 3.7 or higher recommended)

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python app.py
   ```

4. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## Project Structure

- `app.py` - Main application file
- `requirements.txt` - Python dependencies
- `templates/` - HTML templates
  - `base.html` - Base template with Bootstrap integration
  - `index.html` - Home page with case management and plugin access
  - `case.html` - Individual case view
  - `plugins.html` - Plugin management page
- `cases/` - Directory where all cases are stored
- `plugins/` - Directory where Python script plugins are stored
