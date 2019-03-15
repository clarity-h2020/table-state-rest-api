activate_this = '/var/data/src/table-state-rest-api/clarityapi/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))
import sys
sys.path.insert(0, '/var/data/src/table-state-rest-api/api/')
from api import app as application
