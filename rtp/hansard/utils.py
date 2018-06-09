import os
import nltk 
import logging
import spacy

from lxml import etree
from bs4 import BeautifulSoup, element
from textblob import TextBlob

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tag.stanford import StanfordNERTagger
from nltk.tokenize.punkt import PunktSentenceTokenizer
from nltk.chunk import tree2conlltags

logger = logging.getLogger(__name__)


# Contextualise a tag within a hansard file 
# by extracting speaker, type, time and cleaned text
def contextualise_tag(tag):
    try:
        speech = {}
        speech_header = tag.parent.p.span
        # returns the full context for a sentence
        # Type classes
        # TODO: HPS-MemberContinuation?
        type_classes = ['HPS-MemberSpeech', 'HPS-MemberQuestion', 'HPS-MemberAnswer', 'HPS-OfficeSpeech']
        speech['type'] = speech_header.find(attrs={'class':type_classes})['class']
        speech['person'] = speech_header.find(attrs={'class':type_classes}).get_text()
        speech['time'] = speech_header.find(attrs={'class':'HPS-Time'}).get_text()

        # First element: a bit of wrangling to get the useful text
        if tag==tag.parent.p:
            siblings = [si if isinstance(si, element.NavigableString) else si.get_text() for si in tag.find(attrs={'class':'HPS-Time'}).next_siblings]
            speech['text'] = "".join(siblings)[4:]
        else:
            # Other elements are more straight forward
            speech['text'] = tag.get_text().strip('\n')

        return speech

    except Exception as e:
        logger.debug("Error contextualising tag: %s" % (tag,))


# Returns a structured log of actual speeches devoid of procedural ornements, and annotated by their speaker, start time and type
def parse_hansard(filename='House of Representatives_2018_05_10_6091.xml'):
    # Supported parsers
    # https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser
    with open(os.path.join('hansard/data/raw', filename), 'r') as xml: 
        soup = BeautifulSoup(xml.read(), "xml")

    # Fragment contextualisation & cleaning
    fragments = []
    interjection_classes = ['HPS-MemberInterjecting', 'HPS-MemberIInterjecting', 'HPS-OfficeInterjecting']

    for talk in soup.find_all('talk.text'):
        for p in talk.find_all('p'):
            if p.find(attrs={'class': interjection_classes}):
                pass
            else:
                fragments.append(contextualise_tag(p))

    sample = " ".join([frag['text'] for frag in fragments])
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
