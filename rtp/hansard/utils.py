import os
import nltk 
import logging
import spacy

from lxml import etree
from bs4 import BeautifulSoup
from textblob import TextBlob

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tag.stanford import StanfordNERTagger
from nltk.tokenize.punkt import PunktSentenceTokenizer
from nltk.chunk import tree2conlltags

logger = logging.getLogger(__name__)

def parse_hansard(filename='House of Representatives_2018_05_10_6091.xml'):
    # Returns a structured log of actual speeches devoid of procedural ornements 
    # Actual speeches are flagged by:
    # 

    # HPS-MemberSpeech
    # Note: usually decorated with some regularly expressed markup
    """
                    <a href="00APG" type="MemberSpeech">
                        <span class="HPS-MemberSpeech">The SPEAKER</span>
                    </a> (<span class="HPS-Time">09:31</span>):
    """
    # or
    """
                    <a href="HWP" type="MemberSpeech">
                        <span class="HPS-MemberSpeech">Ms MARINO</span>
                    </a> (<span class="HPS-Electorate">Forrest</span>—<span class="HPS-MinisterialTitles">Chief Government Whip</span>) (<span class="HPS-Time">09:31</span>):
    """

    # HPS-MemberQuestion
    """
                    <a href="M3C" type="MemberQuestion">
                        <span class="HPS-MemberQuestion">Mr BANDT</span>
                    </a> (<span class="HPS-Electorate">Melbourne</span>) (<span class="HPS-Time">14:19</span>):
    """
    # or
    """
                    <a href="00ATG" type="MemberQuestion">
                        <span class="HPS-MemberQuestion">Mr SHORTEN</span>
                    </a> (<span class="HPS-Electorate">Maribyrnong</span>—<span class="HPS-MinisterialTitles">Leader of the Opposition</span>) (<span class="HPS-Time">14:25</span>):
    """
    # HPS-MemberAnswer
    """
                    <a href="208884" type="MemberAnswer">
                        <span class="HPS-MemberAnswer">Mr PORTER</span>
                    </a> (<span class="HPS-Electorate">Pearce</span>—<span class="HPS-MinisterialTitles">Attorney-General</span>) (<span class="HPS-Time">14:27</span>):
    """
    # HPS-MemberContinuation
    """
                    <a href="E3L" type="MemberContinuation">
                        <span class="HPS-MemberContinuation">Mr MORRISON:</span>
                    </a>
    """
    # HPS-MemberInterjecting
    # Note: HPS-MemberIInterjecting is excluded as it contains no spoken words
    # Note: HPS-OfficeInterjecting is excluded as it contains only procedural gibberish
    # Note: HPS-GeneralInterjecting is excluded as it not attributable to anyone
    # Target structure to be a list of dict
    # each dict contains:
    # speaker
    # type of contribution (speech, question, answer, continuation, interjection)
    # time (for speech, question and answer)
    # a list of paragraphs, in the same order they were delivered
    # Supported parsers
    # https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser
    with open(os.path.join('hansard/data/raw', filename), 'r') as xml: 
        soup = BeautifulSoup(xml.read(), "xml")

    # Cleaning up
    sample = ''
    current_speaker = None
    fragments, fragment = [], {}

    for talk in soup.find_all('talk.text')[:3]:
        for p in talk.find_all('p'):
            try:
                spans = p.find_all('span')
                for span in spans:
                    if span.has_attr('class'):
                        if span['class'] in ["HPS-MemberSpeech", "HPS-MemberQuestion", "HPS-MemberAnswer"]:
                            # Changing speaker: need a new fragment
                            print("Fragment: %s" % (fragment))
                            if fragment.keys():
                                fragments.append(fragment)
                            fragment = {
                                'speaker': span.get_text(),
                                'type': span['class'],
                                'time': None,
                                'text': []
                            }
                        elif span['class'] in ["HPS-Time"]:
                            fragment['time'] = span.get_text()
                        elif span['class'] in ["HPS-Normal"]:
                            if 'text' in fragment.keys():
                                fragment['text'] += [span.get_text()]
                            else:
                                fragment['text'] = [span.get_text()]
                        else:
                            # Unrecognised class
                            pass
                    else:
                        # Non-tagged spans not interesting
                        pass

            except AttributeError as e:
                # Not a tag element, probably a string like '\n'
                print(str(e))



    # Add a space after each dot
    #raw_text = talk.get_text(strip=True).replace('.', '. ')
    #sample += raw_text



def process_hansard_file(filename='House of Representatives_2018_05_10_6091.xml'):
    # Supported parsers
    # https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser
    with open(os.path.join('hansard/data/raw', filename), 'r') as xml: 
        soup = BeautifulSoup(xml.read(), "xml")

    # Word frequency analysis
    my_abbrev = ['\'m', '.', ',', '\'s', '(', ')', 'n\'t', '\'ve', ';', '$', ':', '\'', '?', '\'ll', '\'re']
    stoplist = set(stopwords.words('english') + my_abbrev)
    sample = ''
    for talk in soup.find_all('talk.text'):
        # TODO: clean up the junk
        # TODO: remove "(<span class="HPS-Time">09:31</span>):"
        # TODO: remove "(<span class="HPS-Electorate">Forrest</span>—<span class="HPS-MinisterialTitles">Chief Government Whip</span>):"
        # TODO: other embedded elements not part of the talk?
        # Add a space after each dot
        raw_text = talk.get_text(strip=True).replace('.', '. ')
        sample += raw_text

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

    # Same with TextBlob -> produces the exact same output
    #sample_blob = TextBlob(sample)
    #pos_analysis(sample_blob.tags, my_abbrev)

    # Get named entities
    # nltk way -> label extraction for a continuous chunk needs improvement
    named_entities_tags = []
    for sentence in chunked_sentences:
        named_entities_tags += get_continuous_chunks(sentence)
    display_freq([ne for ne, ne_type in named_entities_tags if ne_type=='PERSON'], 'Named entities (PERSON)', top=20)

    # Stanford NER tagger
    jar = 'hansard/stanford-ner-tagger/stanford-ner.jar'
    model = 'hansard/stanford-ner-tagger/english.all.3class.distsim.crf.ser.gz'

    try:
        # Prepare NER tagger with english model
        ner_tagger = StanfordNERTagger(model, jar, encoding='utf8')
        named_entities_stanford = []
        # TODO: far too slow - how can this be useful at all?
        #for sentence in tokenized_sentences:
        #    named_entities_stanford += ner_tagger.tag(sentence)
        #display_freq([ne for ne, ne_type in named_entities_stanford if ne_type!='O'], 'Named entities (Stanford)', top=100)
    except LookupError as e:
        logger.error("Are the Stanford NER tagger JAR and model in the stanford-ner-tagger folder?")
        logger.error("Hint: https://blog.sicara.com/train-ner-model-with-nltk-stanford-tagger-english-french-german-6d90573a9486")

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

def get_continuous_chunks(sentence):
    return [(" ".join(w for w, t in elt), [t for w, t in elt][-1]) for elt in sentence if isinstance(elt, nltk.tree.Tree)]