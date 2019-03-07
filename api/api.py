from flask import Flask, jsonify, request
from flask import make_response

import gdal
import tempfile
import numpy as np
from owslib.wcs import WebCoverageService

app = Flask(__name__)
app.config["DEBUG"] = True

WCSURL = 'https://clarity.meteogrid.com/geoserver/wcs'

def get_value(baseline, future):
    # 100 x [(future layer) - (baseline layer)] / (baseline layer)
    value = 100 * (future - baseline) / baseline
    return value

def compare_thresholds(thresholds, value):
    for threshold in thresholds:
        if threshold['name'] == 'low':
            lower = float(threshold['lower'])
        if threshold['name'] == 'high':
            upper = float(threshold['upper'])
    if value <= lower:
        return "Low"
    elif value >= upper:
        return "High"
    else:
        return "Medium"

def get_hazard_characterization(request):
    output = []

    for hazard in request['hazards']:
        for layer_set in hazard['layers']:
            hazard_characterization = {
            "hazard": hazard["hazard"],
            "baseline": "",
            "earlyResponseScenario": "",
            "effectiveMeasuresScenario": "",
            "businessAsUsualScenario": "",
            "period": ""
            }   

            hazard_characterization["period"] = layer_set['time-period']
            baseline_layer = layer_set['layer_ids']['baseline_layer_id']
            rcp26_layer = layer_set['layer_ids']['rcp26_layer_id']
            rcp45_layer = layer_set['layer_ids']['rcp45_layer_id']
            rcp85_layer = layer_set['layer_ids']['rcp85_layer_id']
            
            baseline_median = get_geoserver_data(request['bbox'], baseline_layer)
            rcp26_median = get_geoserver_data(request['bbox'], rcp26_layer)
            rcp45_median = get_geoserver_data(request['bbox'], rcp45_layer)
            rcp85_median = get_geoserver_data(request['bbox'], rcp85_layer)

            hazard_characterization["baseline"] = compare_thresholds(hazard["baseline_thresholds"], baseline_median)
            hazard_characterization["earlyResponseScenario"] = compare_thresholds(hazard["future_thresholds"], get_value(baseline_median, rcp26_median))
            hazard_characterization["effectiveMeasuresScenario"] = compare_thresholds(hazard["future_thresholds"], get_value(baseline_median, rcp45_median))
            hazard_characterization["businessAsUsualScenario"] = compare_thresholds(hazard["future_thresholds"], get_value(baseline_median, rcp85_median))
        
            output.append(hazard_characterization)

        print(output)
    return output
            

def get_geoserver_data(bbox, identifier):
    print(bbox, identifier)
    wcs = WebCoverageService(url=WCSURL, version='2.0.1')

    response = wcs.getCoverage(
            identifier=[identifier], 
            format='GeoTIFF',
            subsets=[('X',bbox[0],bbox[2]), ('Y',bbox[1],bbox[3])], crs='EPSG:3035') #, resx=500, resy=500)
            # For some reason bbox parameters does not work
    
    print(response.geturl())
    tf = tempfile.NamedTemporaryFile(mode='w+b')
    with open(tf.name, 'wb') as file:
        file.write(response.read())
    raster = gdal.Open(tf.name)
    nodata = raster.GetRasterBand(1).GetNoDataValue()
    data = raster.GetRasterBand(1).ReadAsArray().astype('float')
    # mean = np.mean(data[data != nodata])
    median = np.median(data[data != nodata])
    tf.close()
    print('median', median)
    return median

@app.route('/api/request_hazard', methods=['POST'])
def process_hc_request():
    if not request.json:
        abort(400)
    print(request.json)
    if request.json["type"] == 'eu-gl:hazard-characterization':
        output = get_hazard_characterization(request.json)
    else:
        return make_response(jsonify({'result': 'Wrong type request'}), 201)    
    # return make_response(jsonify({'result': 'Received'}), 201)
    return make_response(jsonify(output), 201)

@app.route('/', methods=['GET'])
def home():
    return "<h1>TABLE API</h1><p>This site is a prototype API for returning data info.</p>"

app.run()
