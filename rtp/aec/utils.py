import os

from django.contrib.gis.utils import LayerMapping

from .models import *


def load_data_assets(load_boundaries=True):
    aec_folder = os.path.join(os.path.dirname(__file__), 'data')
    boundaries_file = os.path.join(aec_folder, 'national2016.shp')

    if load_boundaries:
        federal_electorate_2016.objects.all().delete()
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

        # Fixing 2 spelling mistakes in the GIS dataset
        # Detected by comapring with eletcorates in TheyVoteForYou
        federal_electorate_2016.objects.filter(elect_div='Mcmillan').update(elect_div='McMillan')
        federal_electorate_2016.objects.filter(elect_div='Mcpherson').update(elect_div='McPherson')
