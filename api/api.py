from flask import Flask, jsonify, request
from flask import make_response
from flask_cors import CORS
from flask.logging import default_handler

import logging

from helpers import characterization

app = Flask(__name__)
app.config["DEBUG"] = True
CORS(app)

root = logging.getLogger()
root.addHandler(default_handler)

@app.route('/request_hazard', methods=['POST'])
def process_hc_request():
    if not request.json:
        root.warning('Received a request missing JSON headers')
        return make_response(jsonify({'result': 'Missing JSON request'}), 400)
    print(request.json)
    if request.json["type"] == 'eu-gl:hazard-characterization':
        try:
            output = characterization.get_hazard_characterization(request.json)
        except Exception as e:
            root.exception(e)
            return make_response(jsonify(str(e)), 404)
        else:
            return make_response(jsonify(output), 201)
    else:
        root.warning('Received the wrong type in the for a Hazard request:', request.json["type"])
        return make_response(jsonify({'result': 'Wrong type request'}), 201)    

@app.route('/request_exposure', methods=['POST'])
def process_ee_request():
    if not request.json:
        root.warning('Received a request missing JSON headers')
        return make_response(jsonify({'result': 'Missing JSON request'}), 400)
    if request.json["type"] == 'eu-gl:exposure-evaluation':
        try:
            output = characterization.get_exposure_characterization(request.json)
        except Exception as e:
            root.exception(e)
            return make_response(jsonify(str(e)), 404)
        else:
            return make_response(jsonify(output), 201)
    else:
        root.warning('Received the wrong type in an Exposure request: %s', request.json["type"])
        return make_response(jsonify({'result': 'Wrong type request'}), 201)    
    

@app.route('/', methods=['GET'])
def home():
    return "<h1>TABLE API</h1><p>This site is a prototype API for returning data info.</p>"

if __name__ == '__main__':
    app.run()
