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


class TableEntry(object):
    def __init__(self, name, time):
        self.name = name
        self.time = time

    def to_dict(self):
        return {
            'name': self.name,
            'time': self.time
        }

# Define the route for the default URL, which loads the form
@app.route('/')
def default():

    with open(os.path.join(app.config['UPLOAD_FOLDER'], 'data.json'), 'r') as f:
        data = json.load(f)

    uploads = [TableEntry(entry['name'], entry['time']) for entry in data]

    return render_template('index.html', uploads=uploads)

# Define the route for the upload page, which uploads the file after submitting the form
@app.route('/process', methods=['GET', 'POST'])
@app.route('/process', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('file')
        new_entries = []

        for file in files:
            file_name = secure_filename(file.filename)
            new_entry = TableEntry(file_name, str(datetime.datetime.now()))
            new_entries.append(new_entry)

        with open("uploads/data.json") as f:
            data = json.load(f)

        for entry in new_entries:
            data.append(entry.__dict__)

        with open("uploads/data.json", "w") as f:
            json.dump(data, f)

        print("Upload successful for " + ", ".join([entry.name for entry in new_entries]))

        with open("uploads/data.json", "r") as f:
            data = json.load(f)

        uploads = [TableEntry(entry['name'], entry['time']) for entry in data]
        table_html = render_template('update_table.html', uploads=uploads)

        return jsonify({'table_html': table_html})

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
