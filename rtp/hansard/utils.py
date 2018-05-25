import os
import nltk 

from lxml import etree
from bs4 import BeautifulSoup

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


def process_hansard_file(filename='House of Representatives_2018_05_10_6091.xml'):
    # Supported parsers
    # https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser
    with open(os.path.join('hansard/data/raw', filename), 'r') as xml: 
        soup = BeautifulSoup(xml.read(), "xml")

    # Word frequency analysis
    stoplist = set(stopwords.words('english') + ['\'m', '.', ',', '\'s', '(', ')', 'n\'t', '\'ve', ';', '$', ':', '\'', '?', '\'ll', '\'re'])
    sample = ''
    for talk in soup.find_all('talk.text'):
        # TODO: remove "(<span class="HPS-Time">09:31</span>):"
        # TODO: remove "(<span class="HPS-Electorate">Forrest</span>—<span class="HPS-MinisterialTitles">Chief Government Whip</span>):"
        # TODO: other embedded elements not part of the talk?
        raw_text = talk.get_text(strip=True)
        sample += raw_text

    # Tokenisation, tagging, chunking
    sentences = nltk.sent_tokenize(sample)
    tokenized_sentences = [nltk.word_tokenize(sentence) for sentence in sentences]
    tagged_sentences = [nltk.pos_tag(sentence) for sentence in tokenized_sentences]
    chunked_sentences = nltk.ne_chunk_sents(tagged_sentences, binary=True)

    # Word frequency over all sentences
    tokens = []
    for sentence in tokenized_sentences:
        tokens += [word for word in sentence if word.lower() not in stoplist]
    display_freq(tokens)

    # Part-of-speech analysis
    pos_analysis(tagged_sentences)

    # Get named entities
    # TODO: split entities by type (using 'label')
    named_entities = []
    for sentence in chunked_sentences:
        named_entities += get_continuous_chunks(sentence)
    display_freq(named_entities, 'Named entities', top=100)

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

def display_freq(tokens, title='Words', top=50):
    freq = nltk.FreqDist(tokens)
    sorted_d = sorted([(key, val) for key, val in freq.items()], key=lambda x: x[1], reverse=True)
    print("%s: %s" % (title, ", ".join([k for k,v in sorted_d[:top]])))

def pos_analysis(sentences):
    wordnet_lemmatizer = WordNetLemmatizer()
    tags = []
    for sentence in sentences:
        tags += sentence
    adjectives = [wordnet_lemmatizer.lemmatize(word) for word, tag in tags if tag=='JJ']
    display_freq(adjectives, 'Adjectives', top=50)
    verbs = [wordnet_lemmatizer.lemmatize(word, pos='v') for word, tag in tags if tag[:2] in ('VB')]
    display_freq(verbs, 'Verbs', top=50)

def get_continuous_chunks(sentence):
    prev = None
    continuous_chunk = []
    current_chunk = []
    for i in sentence:
        if type(i) == nltk.tree.Tree:
            current_chunk.append(" ".join([token for token, pos in i.leaves()]))
        elif current_chunk:
            named_entity = " ".join(current_chunk)
            if named_entity not in continuous_chunk:
                continuous_chunk.append(named_entity)
                current_chunk = []
        else:
            continue
    return continuous_chunk