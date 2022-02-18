#!/usr/bin/env python

from flask import Flask, request, jsonify, render_template
import os
import const

savedData = None

app = Flask(__name__)


@app.route("/", methods=['GET'])
def githubRepoAnalysisDashboard():
    return render_template('dashboard.html')

@app.route("/update", methods=['POST'])
def update():
    global savedData
    data = request.get_json()
    savedData = data
    return "OK"

@app.route("/refresh", methods=['GET'])
def refresh():
    data = savedData
    return jsonify(labels = const.KEYWORDS, data = savedData)

if __name__ == "__main__":
    app.run(host='localhost', port=os.environ.get('PORT', 443))