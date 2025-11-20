# app.py - UPDATED WITH IMAGE UPLOAD + URL SUPPORT
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = 'super-secret-key'  # Change in production!

DATA_FILE = 'data.json'

# Image upload config
UPLOAD_FOLDER = 'static/project_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Default data
DEFAULT_DATA = {
    "config": {
        "name": "Your Name",
        "course_number": "CS101",
        "course_description": "Introduction to Web Development",
        "profile_info": "I'm a passionate developer learning Flask and building portfolios."
    },
    "projects": []
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump(DEFAULT_DATA, f, indent=4)
        return DEFAULT_DATA
    
    try:
        with open(DATA_FILE, 'r') as f:
            content = f.read().strip()
            if not content:
                with open(DATA_FILE, 'w') as f2:
                    json.dump(DEFAULT_DATA, f2, indent=4)
                return DEFAULT_DATA
            return json.loads(content)
    except json.JSONDecodeError:
        print("data.json corrupted. Resetting...")
        with open(DATA_FILE, 'w') as f:
            json.dump(DEFAULT_DATA, f, indent=4)
        return DEFAULT_DATA

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    data = load_data()
    return render_template('index.html', config=data['config'], projects=data['projects'])

@app.route('/config', methods=['GET', 'POST'])
def config():
    data = load_data()
    if request.method == 'POST':
        data['config']['name'] = request.form['name']
        data['config']['course_number'] = request.form['course_number']
        data['config']['course_description'] = request.form['course_description']
        data['config']['profile_info'] = request.form['profile_info']
        save_data(data)
        flash('Configuration updated!', 'success')
        return redirect(url_for('config'))
    return render_template('config.html', config=data['config'])

@app.route('/project/add', methods=['GET', 'POST'])
def add_project():
    data = load_data()
    if request.method == 'POST':
        image_path = None

        # 1. Handle uploaded file
        if 'image_file' in request.files and request.files['image_file'].filename != '':
            file = request.files['image_file']
            if file and allowed_file(file.filename):
                ext = os.path.splitext(file.filename)[1]
                filename = str(uuid.uuid4()) + ext
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = url_for('static', filename=f'project_images/{filename}')

        # 2. If no upload, use URL
        elif request.form.get('image_url'):
            image_path = request.form['image_url']

        # Must have at least one image source
        if not image_path:
            flash('You must upload an image or provide a URL!', 'danger')
            return redirect(request.url)

        project = {
            "id": int(datetime.now().timestamp() * 1000),
            "image": image_path,
            "title": request.form['title'],
            "website_url": request.form.get('website_url', ''),
            "github_url": request.form.get('github_url', ''),
            "description": request.form['description']
        }
        data['projects'].append(project)
        save_data(data)
        flash('Project added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_project.html')

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    data = load_data()
    project = next((p for p in data['projects'] if p['id'] == project_id), None)
    if not project:
        flash('Project not found!', 'danger')
        return redirect(url_for('index'))
    return render_template('project_detail.html', project=project)

@app.route('/project/edit/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    data = load_data()
    project = next((p for p in data['projects'] if p['id'] == project_id), None)
    if not project:
        flash('Project not found!', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        image_path = project['image']  # keep current by default

        # New upload replaces old
        if 'image_file' in request.files and request.files['image_file'].filename != '':
            file = request.files['image_file']
            if file and allowed_file(file.filename):
                ext = os.path.splitext(file.filename)[1]
                filename = str(uuid.uuid4()) + ext
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = url_for('static', filename=f'project_images/{filename}')

        # New URL replaces old
        elif request.form.get('image_url'):
            image_path = request.form['image_url']

        project.update({
            'image': image_path,
            'title': request.form['title'],
            'website_url': request.form.get('website_url', ''),
            'github_url': request.form.get('github_url', ''),
            'description': request.form['description']
        })
        save_data(data)
        flash('Project updated!', 'success')
        return redirect(url_for('index'))

    return render_template('edit_project.html', project=project)

@app.route('/project/delete/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    data = load_data()
    data['projects'] = [p for p in data['projects'] if p['id'] != project_id]
    save_data(data)
    flash('Project deleted!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)