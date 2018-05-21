import os
import nltk 

from lxml import etree
from bs4 import BeautifulSoup

from nltk.corpus import stopwords


def process_hansard_file(filename='House of Representatives_2018_05_10_6091.xml'):
    # Supported parsers
    # https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser
    with open(os.path.join('hansard/data/raw', filename), 'r') as xml: 
        soup = BeautifulSoup(xml.read(), "xml")

    # Word frequency analysis
    tokens = []
    stoplist = stopwords.words('english') + ['i\'m',]
    for talk in soup.find_all('talk.text'):
        text = talk.get_text(strip=True)
        tokens += [t for t in text.split() if t.lower() not in stoplist]
    freq = nltk.FreqDist(tokens)
    sorted_d = sorted([(key, val) for key, val in freq.items()], key=lambda x: x[1], reverse=True)
    print(" ".join([k for k,v in sorted_d[:100]]))

    # Interjection analysis
    parties = {}
    all_interjections = soup.find_all('interjection')
    for interjection in all_interjections:
        # Can be either a party or a role (Speaker, President, etc, ...)
        party = interjection.party.text or interjection.find('name', role='metadata').text
        if party in parties:
            parties[party] = parties[party] + 1
        else:
            parties[party] = 1
    print("%s interjections: %s" % (len(all_interjections), parties))