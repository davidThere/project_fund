from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

# If you plan to handle Word documents, install python-docx:
try:
    from docx import Document
except ImportError:
    Document = None  # If not installed, Word uploads won’t work

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configuration and Constants
UPLOAD_FOLDER = 'static/uploads'  # Folder for image uploads
IMAGE_DATA_FILE = 'image_data.json'  # JSON file to store the last uploaded image
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """Check if the uploaded file is an allowed image type."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image_filename(filename):
    """Saves the uploaded image filename to a JSON file."""
    with open(IMAGE_DATA_FILE, 'w') as f:
        json.dump({'image_filename': filename}, f)

def get_last_uploaded_image():
    """Retrieves the last uploaded image filename from the JSON file."""
    if os.path.exists(IMAGE_DATA_FILE):
        with open(IMAGE_DATA_FILE, 'r') as f:
            data = json.load(f)
            return data.get('image_filename')
    return None

def get_posts():
    """Reads and returns a list of posts from the JSON file."""
    if os.path.exists('posts.json'):
        with open('posts.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def add_post(title, content):
    """Adds a new post to the JSON file with the current timestamp."""
    posts = get_posts()
    new_post = {
        'title': title,
        'content': content,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    posts.append(new_post)
    posts.sort(key=lambda x: x['date'], reverse=True)
    with open('posts.json', 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=4)

# ---------------------------- 
# Existing Routes (Kept Intact) 
# ----------------------------

@app.route('/')
def home():
    return render_template('home.html', title='Home')

@app.route('/about')
def about():
    return render_template('about.html', title='About')

@app.route('/contact')
def contact():
    return render_template('contact.html', title='Contact')

@app.route('/weekly')
def weekly():
    posts = get_posts()
    return render_template('weekly.html', posts=posts, title='Weekly Market Musings')

@app.route('/upload_post', methods=['GET', 'POST'])
def upload_post():
    if request.method == 'POST':
        title = request.form.get('title', 'Untitled Post')
        content = request.form.get('content', '')
        
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            ext = filename.rsplit('.', 1)[1].lower()
            
            if ext == 'docx':
                if Document is None:
                    content = "Error: python-docx is not installed; cannot process .docx files."
                else:
                    document = Document(file_path)
                    content_from_file = "\n".join([para.text for para in document.paragraphs])
                    if content_from_file.strip():
                        content = content_from_file
            elif ext == 'txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content_from_file = f.read()
                    if content_from_file.strip():
                        content = content_from_file

            os.remove(file_path)
        
        add_post(title, content)
        return redirect(url_for('weekly'))
    
    return render_template('upload_post.html', title='Upload Weekly Post')

# ---------------------------- 
# New Account Summary Route (Now with Persistent Image Support) 
# ----------------------------

@app.route('/account_summary', methods=['GET', 'POST'])
def account_summary():
    """Handles displaying the account summary and uploading an image."""
    image_filename = get_last_uploaded_image()
    image_url = url_for('static', filename=f'uploads/{image_filename}') if image_filename else None

    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Save the image filename persistently
            save_image_filename(filename)

            # Update image URL after upload
            image_url = url_for('static', filename=f'uploads/{filename}')

    return render_template('account_summary.html', title='Account Summary', image_url=image_url)

# Run the Flask Development Server
if __name__ == '__main__':
    app.run(debug=True)
