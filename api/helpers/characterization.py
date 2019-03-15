import gdal
import tempfile
import numpy as np

from owslib.wcs import WebCoverageService

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
            crs='EPSG:3035',
            subsets=[('X',bbox[0],bbox[2]), ('Y',bbox[1],bbox[3])]) # resx=500, resy=500
            # For some reason bbox parameter does not work
    
    print(response.geturl())
    
    # FIXME
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

def get_exposure_characterization(request):
    output = []
    for vulclass in request['data']:
        out_data = vulclass
        layer_data = get_geoserver_data(request['bbox'], vulclass['layer'])
        out_data['values'] = str(layer_data)
        out_data.pop('layer')
        output.append(out_data)
    
    print(output)
    return output
