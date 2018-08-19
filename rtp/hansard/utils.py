import os
import nltk 
import logging
import spacy
import datetime
import requests
import string

from lxml import etree
from bs4 import BeautifulSoup, element
from textblob import TextBlob

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tag.stanford import StanfordNERTagger
from nltk.tokenize.punkt import PunktSentenceTokenizer
from nltk.chunk import tree2conlltags

from django.db.utils import DataError

from .models import *

logger = logging.getLogger(__name__)


# Contextualise a tag within a hansard file 
# by extracting speaker, type, time and cleaned text
def contextualise_tag(tag, debate_id):
    try:
        speech, person = {'debate_ref_id': debate_id}, {}

        # Rare: missing time marker
        speech_header = tag.parent.p.span

        # Time: mostly a single tag text value but sometimes spread across several tags
        """
                  <span class="HPS-Time">15</span>
                  <span class="HPS-Time">:</span>
                  <span class="HPS-Time">26</span>
        """
        # Manually fixes:
        # House_of_Representatives_2017_08_14_5360.xml: Shorten's intervention at 14:01
        # House_of_Representatives_2016_08_31_4425.xml: 3 times starting with 13
        # House_of_Representatives_2016_09_12_4432.xml: 1 time starting with 14
        # House_of_Representatives_2016_10_10_4462.xml: 1 time starting with 10
        time_started_tags = speech_header.find_all(attrs={'class':'HPS-Time'})
        allowed_chars = "0123456789:"
        if len(time_started_tags) > 0:
            speech['time_talk_started'] = ''.join([tst.get_text() for tst in time_started_tags])
            speech['time_talk_started'] = ''.join([c for c in speech['time_talk_started'] if c in allowed_chars])
            # TODO: if the time is icomplete with format ':XY', use the 2 chars before the time span tag
            # Oddity
            if speech['time_talk_started']=='24:00':
                speech['time_talk_started'] = '00:00'

        speech_meta = tag.parent.parent.parent.find('talk.start')
        if speech_meta:
            speech['talk_type'] = speech_meta.parent.name

            # TODO: add in_gov and first_speech if they have value / meaning
            # speech['first_speech'] = speech_meta.talker.find('first.speech').get_text()
            # person['in_gov'] = speech_meta.talker.find('in.gov').get_text()

            name_id = speech_meta.talker.find('name.id').get_text()
            person['name'] = speech_meta.talker.find('name').get_text()
            electorate = speech_meta.talker.find('electorate').get_text()
            # Senate members don't have a federal electorate
            if len(electorate) > 0:
                person['electorate'] = FederalElectorate2016.objects.get(elect_div=electorate)
            person['party'] = speech_meta.talker.find('party').get_text()
            pobj, created = Person.objects.update_or_create(name_id=name_id, defaults=person)

            speech['spoken_by']=pobj

            # First element: a bit of wrangling to get the useful text
            if tag==tag.parent.p:
                # Rare: missing time marker
                siblings = [si if isinstance(si, element.NavigableString) else si.get_text() for si in (tag.find(attrs={'class':'HPS-Time'}) or tag.span).next_siblings]
                speech['the_words'] = "".join(siblings)[4:]
            else:
                # Other elements are more straight forward
                speech['the_words'] = tag.get_text()

            # Sanitisation against line returns and non-ASCII chars
            speech['the_words'] = speech['the_words'].strip('\n')
            # TODO: process this kind of stuff: "... northern Western Australiaâ\x80\x94and that\'s thanks ..."
            # parse_hansard('Senate_2017_12_06_5788.xml')
            speech['the_words'] = speech['the_words'].replace("\\x80\\x94", '-')

            # Create referenced sentences records
            Sentence.objects.create(**speech)

            return speech

        else:
            # No meta info -> can't contextualise the sentence
            #logger.debug("Tag has no meta: %s" % (str(tag)[:50],))
            return None

    except Exception as e:
        logger.debug("Error contextualising tag: %s" % (str(tag)[:300],))
        raise


# Returns a structured log of actual speeches devoid of procedural ornements, and annotated by their speaker, start time and type
def parse_hansard(filename='House of Representatives_2018_05_10_6091.xml'):
    # TODO: a general sanitisation step to only keep ASCII characters
    # loads of \x80\x94 everywhere
    # House_of_Representatives_2016_09_15_4439.xml starts with weird characters

    # Supported parsers
    # https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser
    with open(os.path.join('hansard/data/raw', filename), 'r') as xml: 
        soup = BeautifulSoup(xml.read(), "xml")

    session = soup.hansard.find('session.header')
    session_params = {
        'parliament_no': int(session.find('parliament.no').get_text()),
        'date': datetime.datetime.strptime(session.date.get_text(), '%Y-%m-%d'),
        'session_no': int(session.find('session.no').get_text()),
        'period_no': int(session.find('period.no').get_text()),
        'chamber': session.chamber.get_text(),
    }
    sobj, created = SessionReference.objects.update_or_create(**session_params, defaults=session_params)

     # Fragment contextualisation & cleaning
    fragments = []
    interjection_classes = ['HPS-MemberInterjecting', 'HPS-MemberIInterjecting', 'HPS-OfficeInterjecting']

    for talk in soup.find_all('talk.text'):
        skip_talk = False
        # skip <talk.text>\n</talk.text>
        if len(talk.get_text()) > 1:
            sd2 = talk.parent.parent

            base_params = {
                'session': None,
                'debate_title': None,
                'debate_page_no': None,
                'subdebate1_title': None,
                'subdebate1_page_no': None,
                'subdebate2_title': None,
                'subdebate2_page_no': None,                
            }

            try:
                while 1:
                    if sd2.name=='debate':
                        params = base_params
                        params.update({
                            'debate_title': sd2.debateinfo.title.get_text(),
                            'debate_page_no': int(sd2.debateinfo.find('page.no').get_text()),
                            'session': sobj,
                        })
                        # Stop processing the entire debate section!
                        if params['debate_title'] in ('SHADOW MINISTERIAL ARRANGEMENTS', 'MINISTERIAL ARRANGEMENTS'):
                            # Will that go to the next for iteration?
                            logger.debug("Skipping %s talk.text ..." % (params['debate_title'],))
                            skip_talk = True
                            break
                        #logger.debug("debate tag enclosing %s > talk.text: %s" % (talk.parent.name, params))
                        dobj, created = DebateReference.objects.update_or_create(**params, defaults=params)
                        break
                    elif sd2.name=='subdebate.1' and sd2.parent.name=='debate':
                        params = base_params
                        params.update({                    
                            'subdebate1_title': sd2.subdebateinfo.title.get_text(),
                            'subdebate1_page_no': int(sd2.subdebateinfo.find('page.no').get_text()) if len(sd2.subdebateinfo.find('page.no').get_text()) else None,
                            'debate_title': sd2.parent.debateinfo.title.get_text(),
                            'debate_page_no': int(sd2.parent.debateinfo.find('page.no').get_text()),
                            'session': sobj,
                        })
                        #logger.debug("debate > subdebate.1 tag enclosing %s > talk.text: %s" % (talk.parent.name, params))
                        dobj, created = DebateReference.objects.update_or_create(**params, defaults=params)
                        break
                    elif sd2.name=='subdebate.2':
                        params = base_params
                        params.update({
                            'subdebate2_title': sd2.subdebateinfo.title.get_text(),
                            'subdebate2_page_no': int(sd2.subdebateinfo.find('page.no').get_text()) if len(sd2.subdebateinfo.find('page.no').get_text()) else None,
                            'session': sobj,
                        })
                        if sd2.parent.name=='debate':
                            params.update({
                                'debate_title': sd2.parent.debateinfo.title.get_text(),
                                'debate_page_no': int(sd2.parent.debateinfo.find('page.no').get_text()) if len(sd2.parent.debateinfo.find('page.no').get_text()) else None,
                            })
                        elif sd2.parent.name=='subdebate.1' and sd2.parent.parent.name=='debate':
                            params.update({
                                'subdebate1_title': sd2.parent.subdebateinfo.title.get_text(),
                                'subdebate1_page_no': int(sd2.parent.subdebateinfo.find('page.no').get_text()) if len(sd2.parent.subdebateinfo.find('page.no').get_text()) else None,
                                'debate_title': sd2.parent.parent.debateinfo.title.get_text(),
                                'debate_page_no': int(sd2.parent.parent.debateinfo.find('page.no').get_text()),
                            })
                        else:
                            #logger.debug("subdebate.2 tag has no debate or subdebate.1 direct ancestor: %s" % talk.parent.parent.name)
                            pass

                        #logger.debug("%s > %s > %s tag enclosing %s > talk.text: %s" % (sd2.parent.parent.name, sd2.parent.name, sd2.name, talk.parent.name, params))
                        dobj, created = DebateReference.objects.update_or_create(**params, defaults=params)
                        break
                    sd2 = sd2.parent

            except AttributeError as e:
                logger.debug("Couldn't extract debate reference: %s" % str(sd2)[:300])
                raise
            except DataError as e:
                logger.debug("Couldn't persist debate reference: %s" % params)
                raise

            if skip_talk:
                continue
            else:
                # Remove all sentences at this debate reference
                Sentence.objects.filter(debate_ref=dobj).delete()
                # ... and re-create them
                for p in talk.find_all('p'):
                    if p.find(attrs={'class': interjection_classes}):
                        pass
                    else:
                        contextualised_tag = contextualise_tag(p, dobj.id)
                        if contextualised_tag:
                            fragments.append(contextualised_tag)

    sample = " ".join([frag['the_words'] for frag in fragments if frag])
    return soup, sample


def analyse_hansard_file(filename='House of Representatives_2018_05_10_6091.xml'):
    # Word frequency analysis
    my_abbrev = ['\'m', '.', ',', '\'s', '(', ')', 'n\'t', '\'ve', ';', '$', ':', '\'', '?', '\'ll', '\'re']
    stoplist = set(stopwords.words('english') + my_abbrev)
    soup, sample = parse_hansard(filename)

    # Tokenisation, tagging, chunking
    sent_tokenizer = PunktSentenceTokenizer()
    # Stop breaking sentence at "No."
    sent_tokenizer._params.abbrev_types.add('no')
    #sentences = nltk.sent_tokenize(sample)
    # TODO: improve sentence tokenizer - still far from good
    sentences = sent_tokenizer.tokenize(sample)

    tokenized_sentences = [nltk.word_tokenize(sentence) for sentence in sentences]
    tagged_sentences = [nltk.pos_tag(sentence) for sentence in tokenized_sentences]
    chunked_sentences = nltk.ne_chunk_sents(tagged_sentences, binary=True)

    # Word frequency over all sentences
    tokens = []
    for sentence in tokenized_sentences:
        tokens += [word for word in sentence if word.lower() not in stoplist]
    display_freq(tokens)

    # Part-of-speech analysis
    tags = []
    for sentence in tagged_sentences:
        tags += sentence
    pos_analysis(tags, my_abbrev)

    # spaCy NER
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(sample)
    # Find named entities, phrases and concepts
    ne_spacy = {}
    for entity in doc.ents:
        if entity.label_ in ne_spacy:
            ne_spacy[entity.label_] += [entity.text]
        else:
            ne_spacy[entity.label_] = [entity.text]
    logger.debug("Entity number per type: %s" % {k:len(v) for k,v in ne_spacy.items()})
    for k in ne_spacy.keys():
        display_freq(ne_spacy[k], 'Named entities (%s)' % (k,), top=20)

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
    logger.debug("%s interjections: %s" % (len(all_interjections), parties))

def display_freq(tokens, title='Words', top=50):
    freq = nltk.FreqDist(tokens)
    sorted_d = sorted([(key, val) for key, val in freq.items()], key=lambda x: x[1], reverse=True)
    logger.debug("%s (total=%s): %s" % (title, len(tokens), ", ".join([k for k,v in sorted_d[:top]])))

def pos_analysis(tags, stoplist):
    wordnet_lemmatizer = WordNetLemmatizer()
    nouns = [wordnet_lemmatizer.lemmatize(word) for word, tag in tags if tag=='NN']
    display_freq(nouns, 'Nouns', top=50)
    adjectives = [wordnet_lemmatizer.lemmatize(word) for word, tag in tags if tag=='JJ']
    display_freq(adjectives, 'Adjectives', top=50)
    verbs = [wordnet_lemmatizer.lemmatize(word, pos='v') for word, tag in tags if tag[:2] in ('VB') and word not in stoplist]
    display_freq(verbs, 'Verbs', top=50)

def parse_all_hansards(folder='hansard/data/raw'):
    for dirpath, dirnames, filenames in os.walk(folder):
        for fname in sorted(filenames):
            if fname.lower().endswith('.xml'):
                logger.debug("Parsing: %s ... " % (fname))
                parse_hansard(fname)

def download_all_hansards(date_from=datetime.date(2016, 8, 30), date_to=None):
    if date_to is None:
        date_to = datetime.date.today()

    base_url = "https://www.aph.gov.au/Parliamentary_Business/Hansard?wc="

    for x in range((date_to - date_from).days // 7 + 1):
        sitting_week =  "%s%s" % (base_url, (date_from +  datetime.timedelta(days=x * 7)).strftime('%d/%m/%Y'))
        logger.debug("Scraping %s" % (sitting_week,))
        page = requests.get(sitting_week)
        soup = BeautifulSoup(page.text, 'html.parser')

        # All Links to XML documents
        xml_links = soup.find('h2').parent.find_all('a', attrs={'title': 'XML format'})

        # Download these links!
        for xml_link in xml_links:
            base_api = "https://www.aph.gov.au"
            hansard = requests.get(base_api + xml_link['href'])

            target_filename = hansard.url.split('/')[-1].split(';')[0].replace('%20', '_').replace('_Official','')

            with open(os.path.join('hansard/data/raw', target_filename), 'w') as xml:
                xml.write(hansard.text.replace(u'â\x80\x93', u' - ').replace(u'â\x80\x94', u' - ').replace(u'â\x80\x91', u'-').replace(u'â\x80\x98', '\'').replace(u'â\x80\x99', '\'').replace(u'â\x80\xA6', u'...'))
