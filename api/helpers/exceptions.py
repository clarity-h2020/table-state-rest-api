from owslib.wcs import WebCoverageService
from xml.etree import ElementTree

import logging
import json

owslib_log = logging.getLogger('owslib')
owslib_log.setLevel(logging.DEBUG)

WCSURL = 'https://clarity.meteogrid.com/geoserver/wcs'

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class GeoserverError(Error):
    """Exception raised for errors in the input.

    Attributes:
        epsg -- EPGS of the failed request
        bbox -- Bounding Box of the failed request
        identifier -- Identifier of the failed request
        message -- explanation of the error
    """
    def __init__(self, epsg, bbox, identifier):
        self.epsg = epsg
        self.bbox = bbox
        self.identifier = identifier
        # self.message = self._get_response()

    def __str__(self):
        wcs = WebCoverageService(url=WCSURL, version='1.0.0')
        try:
            response = wcs.getCoverage(
                    identifier=[self.identifier],
                    format='GeoTIFF',
                    crs=self.epsg,
                    subsets=[('X',self.bbox[0],self.bbox[2]), ('Y',self.bbox[1],self.bbox[3])])
                    # For some reason bbox parameter does not work
            owslib_log.debug(response.geturl())
        except Exception as e:
            owslib_log.exception('Something went wrong getting the requested coverage: %s', e)
        else:
            tree = ElementTree.fromstring(response.read())
            service_except = tree.getchildren()[0]
            code, locator = service_except.items()
            text = service_except.text
            return json.dumps({'code': code[1], 'locator': locator[1], 'message': text})
