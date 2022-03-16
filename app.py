import glob
import io
import os
from io import BytesIO

import boto3
import requests
from PIL import Image
from PIL import io
from flask import Flask, render_template, request, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(ROOT_DIR, "static")
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR

# create 'static' folder if not exists
if not os.path.exists(UPLOAD_DIR):
    os.mkdir(UPLOAD_DIR)

# configure boto3 client
s3_client = boto3.client('s3', aws_access_key_id = os.environ['AWS_ACCESS_KEY_ID'], aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY'])


# utility functions
def get_s3_url(bucket_name, filename):
    return f"https://{bucket_name}.s3.amazonaws.com/{filename}"


def request_and_save(url, filename):
    req = requests.get(url)

    '''byteImgIO = io.BytesIO()
    byteImg = Image.open(req.content)
    byteImg.save(byteImgIO, "PNG")
    byteImgIO.seek(0)
    byteImg = byteImgIO.read()

    dataBytesIO = io.BytesIO(byteImg)
    Image.open(dataBytesIO)'''

    byteImgIO = io.BytesIO()
    im = Image.open(req.content)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    #im.save(path, "PNG")
    im.save(byteImgIO, "PNG")
    byteImgIO.seek(0)
    byteImg = byteImgIO.read()

    return path


# app endpoints
@app.route('/', methods=['GET', 'POST'])
def index():

    filename = None
    if request.method == 'POST':
        f = request.files['file']
        filename = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return render_template('upload.html', filename=filename)


@app.route('/watermark', methods=['POST'])
def apply_watermark():
    bucket_name = "heroku-bucket-gruppo-4" # INSERT YOUR BUCKET NAME

    filename = request.form['filename']
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    r1 = s3_client.upload_file(path, bucket_name, filename, ExtraArgs={'ACL': 'public-read'})

    # GENERATE REQUEST FOR QRACKAJACK
    qr_image = get_s3_url(bucket_name, filename)
    qrack_api = os.environ['QRACKAJACK_API_KEY']
    qr_req_url = "https://qrackajack.expeditedaddons.com/?api_key={qrack_api}&content={qr_image}"

    qr_name = f"qr_{filename}"
    qr_path = request_and_save(qr_req_url, qr_name)

    r2 = s3_client.upload_file(qr_path, bucket_name, qr_name, ExtraArgs={'ACL': 'public-read'})


    # GENERATE REQUEST FOR WATERMARKER
    qr_watermark = get_s3_url(bucket_name, qr_name)
    water_api = os.environ['WATERMARKER_API_KEY']
    watermark_req_url = "https://watermarker.expeditedaddons.com/?api_key={water_api}&image_url={qr_image}&watermark_url={qr_watermark}&opacity=50&position=center&width=100&height=100"

    watermark_name = f"watermark_{filename}"
    request_and_save(watermark_req_url, watermark_name)

    print("watermark done")

    # clean bucket
    s3_client.delete_object(Bucket=bucket_name, Key=qr_name)

    return render_template("upload.html", filename=watermark_name)


if __name__ == '__main__':
    app.run(debug=True)
