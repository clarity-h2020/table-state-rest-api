import gdal
import tempfile
import logging
import json
import numpy as np

from owslib.wcs import WebCoverageService
from xml.etree import ElementTree
from .exceptions import GeoserverError

owslib_log = logging.getLogger('owslib')
owslib_log.setLevel(logging.DEBUG)

WCSURL = 'https://clarity.meteogrid.com/geoserver/wcs'

def get_value(baseline, future):
    # 100 x [(future layer) - (baseline layer)] / (baseline layer)
    #value = 100 * (future - baseline) / baseline
    value = future - baseline
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
            "baseline_value": "",
            "earlyResponseScenario": "",
            "earlyResponseScenario_value": "",
            "effectiveMeasuresScenario": "",
            "effectiveMeasuresScenario_value": "",
            "businessAsUsualScenario": "",
            "businessAsUsualScenario_value": "",
            "period": ""
            }   

            hazard_characterization["period"] = layer_set['time-period']
            baseline_layer = layer_set['layer_ids']['baseline_layer_id']
            rcp26_layer = layer_set['layer_ids']['rcp26_layer_id']
            rcp45_layer = layer_set['layer_ids']['rcp45_layer_id']
            rcp85_layer = layer_set['layer_ids']['rcp85_layer_id']
            
            epsg = request['epsg'].upper()
            bbox = request['bbox']

            try:
                baseline_data, baseline_nodata = get_geoserver_data(epsg, bbox, baseline_layer)
                rcp26_data, rcp26_nodata = get_geoserver_data(epsg, bbox, rcp26_layer)
                rcp45_data, rcp45_nodata = get_geoserver_data(epsg, bbox, rcp45_layer)
                rcp85_data, rcp85_nodata = get_geoserver_data(epsg, bbox, rcp85_layer)
            except:
                raise
            else:
                baseline_median = get_median(baseline_data, baseline_nodata)
                rcp26_median = get_median(rcp26_data, rcp26_nodata)
                rcp45_median = get_median(rcp45_data, rcp45_nodata)
                rcp85_median = get_median(rcp85_data, rcp85_nodata)
                rcp26_value = get_value(baseline_median, rcp26_median)
                rcp45_value = get_value(baseline_median, rcp45_median)
                rcp85_value = get_value(baseline_median, rcp85_median)
                hazard_characterization["baseline"] = compare_thresholds(hazard["baseline_thresholds"], baseline_median)
                hazard_characterization["baseline_value"] = baseline_median
                hazard_characterization["earlyResponseScenario"] = compare_thresholds(hazard["future_thresholds"], rcp26_value)
                hazard_characterization["earlyResponseScenario_value"] = rcp26_value
                hazard_characterization["effectiveMeasuresScenario"] = compare_thresholds(hazard["future_thresholds"], rcp45_value)
                hazard_characterization["effectiveMeasuresScenario_value"] = rcp45_value
                hazard_characterization["businessAsUsualScenario"] = compare_thresholds(hazard["future_thresholds"], rcp85_value)
                hazard_characterization["businessAsUsualScenario_value"] = rcp85_value
            
                output.append(hazard_characterization)
    return output

def get_exposure_characterization(request):
    output = []
    epsg = request['epsg'].upper()
    bbox = request['bbox']
    for vulclass in request['data']:
        out_data = vulclass
        layer_data, layer_nodata = get_geoserver_data(epsg, bbox, vulclass['layer'])
        value = get_median(layer_data, layer_nodata)
        out_data['values'] = str(value)
        out_data.pop('layer')
        output.append(out_data)
    return output

def get_geoserver_data(epsg, bbox, identifier):
    wcs = WebCoverageService(url=WCSURL, version='2.0.1')

    try:
        response = wcs.getCoverage(
                identifier=[identifier], 
                format='GeoTIFF',
                crs=epsg,
                subsets=[('X',bbox[0],bbox[2]), ('Y',bbox[1],bbox[3])]) # resx=500, resy=500
                # For some reason bbox parameter does not work
        owslib_log.debug(response.geturl())
    except Exception as e:
        # This exception handling should change but OWSlib for WCS 2.0.1 does not seem to 
        # handle returned error messages from geoserver OK
        owslib_log.exception('Something went wrong getting the requested coverage: %s', e)
        raise GeoserverError(epsg, bbox, identifier)

    try:    
        # FIXME
        tf = tempfile.NamedTemporaryFile(mode='w+b')
        with open(tf.name, 'wb') as file:
            file.write(response.read())
        raster = gdal.Open(tf.name)
        nodata = raster.GetRasterBand(1).GetNoDataValue()
        data = raster.GetRasterBand(1).ReadAsArray().astype('float')
        tf.close()
        return data, nodata
    except Exception as e:
        owslib_log.exception('Problem encountered processing Coverage: %s', e)
        raise 
    
def get_median(data, nodata):
    median = np.median(data[data != nodata])
    return median