import os
import logging
import requests

from django.conf import settings

from aec.models import federal_electorate_2016

logger = logging.getLogger(__name__)
api = settings.APIS['THEYVOTEFORYOU']


def api_call(endpoint='people', id=None):
    r = requests.get(api['ROOT'] + '/' + endpoint + '.json' + '?key=' + api['KEY'])

    try:
        if r.status_code == 200:
            response = r.json()
            return response
        else:
            logger.error('Status code: %s ' % (r.status_code))
    except Exception as e:
        raise


def check_electorates():
    # TheyWorkForYou
    tv4u_electorates = [peep['latest_member']['electorate'] for peep in api_call('people') if peep['latest_member']['house']=='representatives']
    # AEC electorates
    aec_electorates = list(federal_electorate_2016.objects.all().values_list('elect_div', flat=True))

    unknown_to_aec = set(tv4u_electorates) - set(aec_electorates)
    logger.debug("Unknown to AEC: %s" % unknown_to_aec)

    unknown_to_tv4u = set(aec_electorates) - set(tv4u_electorates)
    logger.debug("Unknown to TheyVoteForYou: %s" % unknown_to_tv4u)
