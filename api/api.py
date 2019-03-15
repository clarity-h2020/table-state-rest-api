from flask import Flask, jsonify, request
from flask import make_response

#from owslib.wcs import WebCoverageService

from helpers import characterization

app = Flask(__name__)
app.config["DEBUG"] = True

@app.route('/request_hazard', methods=['POST'])
def process_hc_request():
    if not request.json:
        abort(400)
    print(request.json)
    if request.json["type"] == 'eu-gl:hazard-characterization':
        output = characterization.get_hazard_characterization(request.json)
    else:
        return make_response(jsonify({'result': 'Wrong type request'}), 201)    
    # return make_response(jsonify({'result': 'Received'}), 201)
    return make_response(jsonify(output), 201)

@app.route('/request_exposure', methods=['POST'])
def process_ee_request():
    if not request.json:
        abort(400)
    print(request.json)
    if request.json["type"] == 'eu-gl:exposure-evaluation':
        output = characterization.get_exposure_characterization(request.json)
    else:
        return make_response(jsonify({'result': 'Wrong type request'}), 201)    
    # return make_response(jsonify({'result': 'Received'}), 201)
    return make_response(jsonify(output), 201)

@app.route('/', methods=['GET'])
def home():
    return "<h1>TABLE API</h1><p>This site is a prototype API for returning data info.</p>"

if __name__ == '__main__':
    app.run()
