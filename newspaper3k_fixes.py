import re
import string
'''
Here are my attempts at fixing the problems described in the notebook @ ./newspaper3k_fixes_demo.ipynb
The code below is ripped from newspaper3k, with small bug fixes applied
'''

def getElementsByTag(
            node, tag=None, attr=None, value=None, childs=False, use_regex=False) -> list:
        NS = None
        # selector = tag or '*'
        selector = 'descendant-or-self::%s' % (tag or '*')
        if attr and value:
            if use_regex:
                NS = {"re": "http://exslt.org/regular-expressions"}
                selector = '%s[re:test(@%s, "%s", "i")]' % (selector, attr, value)
            else:
                trans = 'translate(@%s, "%s", "%s")' % (attr, string.ascii_uppercase, string.ascii_lowercase)
                # FIX FOR PROBLEM #1: JUST IGNORE ANY TAG THAT CONTAINS THE PHRASE 'bio'
                selector = '%s[contains(%s, "%s") and not(contains(%s, "bio"))]' % (selector, trans, value.lower(), trans)
        elems = node.xpath(selector, namespaces=NS)
        # remove the root node
        # if we have a selection tag
        if node in elems and (tag or childs):
            elems.remove(node)
        return elems

def get_authors(article):
    """Fetch the authors of the article, return as a list
    Only works for english articles
    """
    doc = article.clean_doc

    _digits = re.compile('\d')

    def contains_digits(d):
        return bool(_digits.search(d))

    def uniqify_list(lst):
        """Remove duplicates from provided list but maintain original order.
          Derived from http://www.peterbe.com/plog/uniqifiers-benchmark
        """
        seen = {}
        result = []
        for item in lst:
            if item.lower() in seen:
                continue
            seen[item.lower()] = 1
            result.append(item.title())
        return result

    def parse_byline(search_str):
        """
        Takes a candidate line of html or text and
        extracts out the name(s) in list form:
        >>> parse_byline('<div>By: <strong>Lucas Ou-Yang</strong>,<strong>Alex Smith</strong></div>')
        ['Lucas Ou-Yang', 'Alex Smith']
        """
        # Remove HTML boilerplate
        search_str = re.sub('<[^<]+?>', '', search_str)

        # Remove original By statement
        search_str = re.sub('[bB][yY][\:\s]|[fF]rom[\:\s]', '', search_str)

        search_str = search_str.strip()

        # Chunk the line by non alphanumeric tokens (few name exceptions)
        # >>> re.split("[^\w\'\-\.]", "Tyler G. Jones, Lucas Ou, Dean O'Brian and Ronald")
        # ['Tyler', 'G.', 'Jones', '', 'Lucas', 'Ou', '', 'Dean', "O'Brian", 'and', 'Ronald']
        name_tokens = re.split("[^\w\'\-\.]", search_str)
        name_tokens = [s.strip() for s in name_tokens]

        _authors = []
        # List of first, last name tokens
        curname = []
        delimiters = ['and', ',', '']

        for token in name_tokens:
            if token in delimiters:
                if len(curname) > 0:
                    _authors.append(' '.join(curname))
                    curname = []

            elif not contains_digits(token):
                curname.append(token)

        # One last check at end
        valid_name = (len(curname) >= 2)
        if valid_name:
            _authors.append(' '.join(curname))

        return _authors

    # Try 1: Search popular author tags for authors

    ATTRS = ['name', 'rel', 'itemprop', 'class', 'id']
    VALS = ['author', 'byline', 'dc.creator', 'byl']
    matches = []
    authors = []

    for attr in ATTRS:
        for val in VALS:
            # found = doc.xpath('//*[@%s="%s"]' % (attr, val))
            found = getElementsByTag(doc, attr=attr, value=val)
            matches.extend(found)

    for match in matches:
        content = ''
        if match.tag == 'meta':
            mm = match.xpath('@content')
            if len(mm) > 0:
                content = mm[0]
        else:
            content = match.text or ''
        if len(content) > 0:
            authors.extend(parse_byline(content))

    return uniqify_list(authors)

# Loads local stopwords file @ ./stopwords.txt
def get_stopwords():
    stopwords = set()
    stopwordsFile = './stopwords.txt'
    with open(stopwordsFile, 'r', encoding='utf-8') as f:
        stopwords.update(set([w.strip() for w in f.readlines()]))
        
    return stopwords

def split_words(text):
    """Split a string into array of words
    """
    try:
        text = re.sub(r'[^\w ]', '', text)  # strip special chars
        return [x.strip('.').lower() for x in text.split()]
    except TypeError:
        return None

def keywords(text):
    """Get the top 10 keywords and their frequency scores ignores blacklisted
    words in stopwords, counts the number of occurrences of each word, and
    sorts them in reverse natural order (so descending) by number of
    occurrences.
    """
    # -------------------------------------------------------
    # THIS IS A TANGENTIAL CHANGE - GETTING STOPWORDS HERE
    # INSTEAD OF THEM BEING DECLARED AS A PUBLIC VARIABLE EARLIER
    # -------------------------------------------------------
    stopwords = get_stopwords()
    
    NUM_KEYWORDS = 10
    text = split_words(text)
    # of words before removing blacklist words
    if text:
        num_words = len(text)
        text = [x for x in text if x not in stopwords]
        freq = {}
        for word in text:
            if word in freq:
                freq[word] += 1
            else:
                freq[word] = 1

        min_size = min(NUM_KEYWORDS, len(freq))
        keywords = sorted(freq.items(),
                          key=lambda x: (x[1], x[0]),
                          reverse=True)
        keywords = keywords[:min_size]
        keywords = dict((x, y) for x, y in keywords)

        for k in keywords:
            articleScore = keywords[k] * 1.0 / max(num_words, 1)
            keywords[k] = articleScore * 1.5 + 1
            
        return dict(keywords)
    else:
        return dict()


def get_keywords(article):
    text_keyws = list(keywords(article.text).keys())
    title_keyws = list(keywords(article.title).keys())
    keyws = {"text": text_keyws, "title": title_keyws}
    return keyws