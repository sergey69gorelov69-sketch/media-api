import os
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import boto3
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# Настройки PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db = SQLAlchemy(app)

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String, nullable=False)
    s3_key = db.Column(db.String, nullable=False)

# Настройки S3 (например, Yandex S3)
s3 = boto3.client('s3',
                  endpoint_url=os.getenv('S3_ENDPOINT'),
                  aws_access_key_id=os.getenv('S3_KEY'),
                  aws_secret_access_key=os.getenv('S3_SECRET'))

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file'}), 400
    filename = secure_filename(file.filename)
    s3_key = f"uploads/{filename}"
    s3.upload_fileobj(file, os.getenv('S3_BUCKET'), s3_key)
    media = Media(filename=filename, s3_key=s3_key)
    db.session.add(media)
    db.session.commit()
    return jsonify({'id': media.id, 'filename': filename}), 200

@app.route('/files/<int:media_id>')
def get_file(media_id):
    media = Media.query.get_or_404(media_id)
    presigned = s3.generate_presigned_url('get_object', {
        'Bucket': os.getenv('S3_BUCKET'),
        'Key': media.s3_key
    }, ExpiresIn=3600)
    return jsonify({'url': presigned})

if __name__ == '__main__':
    app.run()
