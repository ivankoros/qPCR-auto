from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import pandas as pd
import os
import json
import datetime
from flask_assets import Environment, Bundle

from flask import Flask, render_template

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'


@app.route("/")
@app.route("/index")
def index():
    return render_template("index.html")


if __name__ == '__main__':
    app.run(debug=True)


class TableEntry(object):
    def __init__(self, name, time):
        self.name = name
        self.time = time


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        file_name = secure_filename(file.filename)

        # call the TableEntry class to create a new object
        new_entry = TableEntry(file_name, datetime.datetime.now())

        with open("uploads/data.json") as f:
            data = json.load(f)

        print(data)

        data.append(new_entry.__dict__)

        with open(os.path.join(app.config['UPLOAD_FOLDER'], 'data.json'), 'w') as f:
            json.dump(data, f)

        print("Upload successful for " + file_name)

    # with open(os.path.join(app.config['UPLOAD_FOLDER'], 'data.json'), 'r') as f:
    #     data = json.load(f)
    #
    # uploads = [TableEntry(entry['name'], entry['time']) for entry in data]

    return render_template('index.html')  # uploads=uploads)


if __name__ == '__main__':
    app.run(debug=True)
