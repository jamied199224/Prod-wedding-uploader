import os
import json
import zipfile
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
DATA_FILE = 'media_data.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/media', methods=['GET'])
def get_media():
    items = load_data()
    return jsonify(items)

@app.route('/api/upload', methods=['POST'])
def upload_files():
    uploader = request.form.get('uploader', 'Guest')
    files = request.files.getlist('files')
    items = load_data()
    new_items = []

    for file in files:
        if file and file.filename:
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            is_video = ext in ['mp4', 'mov', 'avi', 'webm', 'mkv']
            
            file_id = str(uuid.uuid4())
            filename = f"{file_id}_{file.filename}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            item = {
                "id": file_id,
                "filename": file.filename,
                "url": f"/uploads/{filename}",
                "uploader": uploader,
                "is_video": is_video,
                "likes": 0
            }
            items.insert(0, item)
            new_items.append(item)

    save_data(items)
    return jsonify({"status": "success", "items": new_items})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/like/<id>', methods=['POST'])
def like_item(id):
    req_data = request.get_json() or {}
    action = req_data.get('action', 'like')
    items = load_data()
    for item in items:
        if item['id'] == id:
            if action == 'like':
                item['likes'] += 1
            else:
                item['likes'] = max(0, item['likes'] - 1)
            break
    save_data(items)
    return jsonify({"status": "success"})

@app.route('/api/media/<id>', methods=['DELETE'])
def delete_item(id):
    items = load_data()
    item_to_delete = None
    new_items = []
    for item in items:
        if item['id'] == id:
            item_to_delete = item
        else:
            new_items.append(item)
    
    if item_to_delete:
        filename = item_to_delete['url'].split('/')[-1]
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        save_data(new_items)
        return jsonify({"status": "success"})
    return jsonify({"error": "Item not found"}), 404

@app.route('/api/download-zip', methods=['POST'])
def download_zip():
    req_data = request.get_json() or {}
    file_ids = req_data.get('file_ids', [])
    items = load_data()
    
    zip_filename = f"wedding_photos_{uuid.uuid4()}.zip"
    zip_path = os.path.join(UPLOAD_FOLDER, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for item in items:
            if item['id'] in file_ids:
                filename = item['url'].split('/')[-1]
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.exists(filepath):
                    zipf.write(filepath, arcname=item['filename'])
                    
    return jsonify({"download_url": f"/uploads/{zip_filename}"})

if __name__ == '__main__':
    app.run(debug=True)