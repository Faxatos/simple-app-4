import os
import requests

from flask import Flask, render_template, request, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(ROOT_DIR, "static")
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR

# app endpoints
@app.route('/', methods=['GET', 'POST'])
def index():

    filename = None
    if request.method == 'POST':
        f = request.files['file']
        filename = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return render_template('upload.html', filename=filename)

if __name__ == '__main__':
    app.run(debug=True)
