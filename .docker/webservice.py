from flask import Flask, Response, flash, request, redirect, url_for, abort, send_from_directory
from subprocess import run, PIPE
from tempfile import TemporaryDirectory
from werkzeug.utils import secure_filename
import os
import shlex

app = Flask(__name__)
app.secret_key = "secret"

uploaddir = TemporaryDirectory(prefix="ocrmypdf-upload")
downloaddir = TemporaryDirectory(prefix="ocrmypdf-download")

app.config["UPLOAD_FOLDER"] = uploaddir
ALLOWED_EXTENSIONS = set(["pdf"])


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def do_ocrmypdf(file):
    filename = secure_filename(file.filename)
    up_file = os.path.join(uploaddir.name, filename)
    file.save(up_file)
    down_file = os.path.join(downloaddir.name, filename)

    cmd_args = [arg for arg in shlex.split(request.form["params"])]
    if "--sidecar" in cmd_args:
        return Response("--sidecar not supported", 501, mimetype='text/plain')

    ocrmypdf_args = ["ocrmypdf", *cmd_args, up_file, down_file]
    proc = run(ocrmypdf_args, stdout=PIPE, stderr=PIPE, encoding="utf-8")
    if proc.returncode != 0:
        stderr = proc.stderr
        return Response(stderr, 400, mimetype='text/plain')

    return send_from_directory(downloaddir.name, filename)


@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return Response("No file in POST", 400, mimetype='text/plain')
        file = request.files["file"]
        if file.filename == "":
            return Response("Empty filename", 400, mimetype='text/plain')
        if not allowed_file(file.filename):
            return Response("Invalid filename", 400, mimetype='text/plain')
        if file and allowed_file(file.filename):
            return do_ocrmypdf(file)
        return Response("Some other problem", 400, mimetype='text/plain')

    return """
    <!doctype html>
    <title>OCRmyPDF webapp</title>
    <h1>Upload a PDF (debug UI)</h1>
    <form method=post enctype=multipart/form-data>
      <label for="args">Command line parameters</label>
      <input type=textbox name=params>
      <label for="file">File to upload</label>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    """

if __name__ == "__main__":
    app.run(host='0.0.0.0')
