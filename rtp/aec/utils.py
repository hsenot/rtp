import os

from django.contrib.gis.utils import LayerMapping

from .models import *

def load_data_assets(load_boundaries=True):
    aec_folder = os.path.join(os.path.dirname(__file__), 'data')
    boundaries_file = os.path.join(aec_folder, 'national2016.shp')

    if load_boundaries:
        # Layer mapping
        lm = LayerMapping(
            federal_electorate_2016,
            boundaries_file,
            federal_electorate_2016_mapping,
            transform=False,
            encoding='iso-8859-1',
        )
        # Load
        # strict=False allows us to skip features that can't be loaded
        lm.save(strict=True, verbose=True)