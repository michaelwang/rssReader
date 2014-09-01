import sae
import os
import sys
from mysite import wsgi


app_root = os.path.dirname(__file__)
application = sae.create_wsgi_app(wsgi.application)

sys.path.insert(0, os.path.join(app_root, 'virtualenv.bundle.zip'))