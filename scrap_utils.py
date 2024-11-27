import pandas as pd
import os
import re
import requests
from unidecode import unidecode
import time


def tokenize(text):
    return re.sub(' +', ' ', re.sub("\W+", ' ', unidecode(text.lower()))).strip(' \n')

class Quote():
    def __init__(self, text, author = None, *, year = None, book = None, page = None,
                  title = None, source = None, confiance = None, nb_like = None, url = None,
                  haiku = None, sonnet = None, vo = None):
        
        if title is not None:
            if ".txt" in title:
                title = title.replace(".txt", "").replace("", "'")
            title = title[0].upper() + title[1:]
        if author is not None:
            author = author[0].upper() + author[1:]
        text = re.sub(r'\n', '  \n', text) 
        text = text.strip(' ,."()«»[]' + "'").replace("", "'").replace('', 'oe')
        if vo is not None:
            vo = re.sub(r'\n', '  \n', vo) 
            vo = vo.strip(' ,."()«»[]' + "'").replace("", "'").replace('', 'oe')
        # if no punctuation at the end, add a dot
        # if len(text) > 0 and text[-1] not in ['.', '!', '?'] and not(haiku):
        #     text += '.'
        if len(text) > 0 and text is not None:
            text = text[0].upper() + text[1:]

        self.text = text
        self.author = author
        self.year = year # year of publication
        self.book = book # book title
        self.title = title # title of the text/poem
        self.source = source # source of the scrapping (hand-made, babelio, pdf, epub)
        self.confiance = confiance # confidence in the scrapping, from 1 to 5 stars
        self.nb_like = nb_like # number of likes on the website
        self.page = page # page number in the book
        self.url = url # url of the source
        self.vo = vo # version original of the quote
        
        # extra 
        self.text_tok = tokenize(text)
        self.nb_char = len(text)
        self.nb_lines = len(text.split('\n'))
        self.haiku = haiku 
        if self.nb_lines == 3:
            for haikiste in ['Basho', 'Buson', 'Issa', 'Shiki', 'Santoka', 'Kerouac']:
                if tokenize(haikiste) in tokenize(author):
                    self.haiku = True
        self.sonnet = sonnet or self.nb_lines == 15


def convert_manual_author():
    # convert raw authors data into data.csv file

    # load each .txt file
    def load_txt(file):
        with open(file, 'r') as f:
            text = f.read()
        return text

    l_quote = []
    authors = os.listdir("data/manual author")
    # check author is a folder
    authors = [author for author in authors if os.path.isdir(f"data/manual author/{author}")]
    for author in authors:
        print(author)
        files = os.listdir(f"data/manual author/{author}")
        for file in files:
            text = load_txt(f"data/manual author/{author}/{file}")
            title = file.replace(".txt", "")
            if len(title) < 3:
                title = None
            l_quote.append(Quote(text, author = author, title = file, source = 'hand-made', confiance = 5))

    # df = pd.DataFrame(l_df)
    df_quote = pd.DataFrame([quote.__dict__ for quote in l_quote])
    print(df_quote.shape)
    df_quote.to_csv('data/manual author_data.csv')

    print(' ------ author okay ------ ')


def extrat_quote(url = "https://www.babelio.com/auteur/Marshall-B-Rosenberg/26325/citations", file = None):
    from bs4 import BeautifulSoup

    if url is not None:
        response = requests.get(url)
        if response.status_code == 200:
            html_content = response.content
        else:
            # print("Error fetching the webpage :", url)
            return None
    else:
        with open(file, 'r') as f:
            html_content = f.read()

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, features="lxml")


    # Find all elements with the class "post post_con"
    citations = soup.find_all("div", class_="post post_con")

    # Extract the citation text from each element
    extracted_citations = []
    for citation in citations:
        try:
            citation_text = citation.find("div", class_="cri_corps_critique").text.strip()
            # extracted_citations.append(citation_text)
            
            # Try to find the book title using the "cri_titre_auteur" class
            book_title_element = citation.find("div", class_="cri_titre_auteur")
            book_title = None
            if book_title_element:
                try:
                    book_title = book_title_element.find("a", class_="titre_livre").text.strip()
                except:
                    pass

            try:
                like_elements = citation.find("span", class_="post_items_like")
                nb_like = int(like_elements.text)
            except:
                nb_like = None

            try:
                auteur = citation.find("a", class_="auteur_gris").text
            except:
                auteur = None
            extracted_citations.append((citation_text, book_title, nb_like, auteur))

        except:
            pass

    # Print the extracted citations
    # print("--------  Nb citation gathered", len(extracted_citations))
    return extracted_citations

def get_babelio_citation(url, author = None, nb_page = None, sleep = 3):

    try:
        ss = url[url.index('auteur/') + 7:]
        author = ss[:ss.index('/')]
        author = author.replace('-', ' ').strip()
    except:
        author = None
    print(author, end = ': ')
    ll = []
    lenght = 0
    bbreak = 0
    nb_page = 400 if nb_page is None else nb_page
    for npage in range(1, nb_page):
        time.sleep(sleep)
        url_final = url + f"?a=a&pageN={npage}"
        list_quote = extrat_quote(url_final)
        if list_quote is None or len(list_quote) == 0:
            print(f'x', end = '')
            bbreak += 1
            if bbreak > 2:
                break
        else:
            lenght += len(list_quote)
            print(f'{int(len(list_quote)/10)}.', end = '')
            # print((npage,lenght), end=', ' if npage % 10 != 0 else '\n')
            ll.append(list_quote)
    print()
    print(' ---- ', author, f' {lenght=} ', f' {npage=}')

    lq = []
    for l in ll:
        for (txt, book, like, auteur) in l:
            final_author = auteur if auteur is not None else author
            lq.append(Quote(txt, author = final_author, book = book, source = 'babelio', nb_like = like, url = url_final))
            
    df_quote = pd.DataFrame([quote.__dict__ for quote in lq])
    # print(df_quote.shape)
    df_quote.to_csv(f'data/babelio/{author}.csv')


def scrap_recent_babelio():
    # scrapp all recents quote -> into bebelio_recents.csv (done for top300 pages)
    l_quote = []
    for npage in range(1, 300):
        print(npage, end = ', ')
        url = f"https://www.babelio.com/dernierescitations.php?p=3&pageN={npage}"
        lll = extrat_quote(url)
        for (text, book, like, author) in lll:
            q = Quote(text, author = author, book = book, source = 'babelio', nb_like = like, url = url)
            l_quote.append(q)
        time.sleep(10)

        if npage % 10 == 0:
            df_quote = pd.DataFrame([quote.__dict__ for quote in l_quote])
            # print(df_quote.shape)
            df_quote.to_csv(f'data/babelio_recents/{npage}.csv')
            l_quote = []
            print(npage)



def extract_poems_eclair(url = "https://www.eternels-eclairs.fr/poemes-prevert.php"):
    from bs4 import BeautifulSoup
    
    response = requests.get(url)
    html_content = response.content # .decode('utf-8')
    soup = BeautifulSoup(html_content, 'html.parser')

    poems = []
    for ii, card in enumerate(soup.find_all('div', class_='card')):
        try:
            # (text, title, book, auteur))
            if card.find('div', class_='poeme-texte') is not None:
                text = '\n'.join([str(x) for x in card.find('div', class_='poeme-texte').p.contents]).replace('\n<br/>\n', '\n').replace('<br/>', '').strip()
            elif card.find('p', class_='respecter-espaces-bruts') is not None:
                text = card.find('p', class_='respecter-espaces-bruts').text.strip()
            else:
                text = card.find('div', class_='poeme-texte haiku').text.strip()
            try:
                title = card.h3.text.strip()
            except:
                title = None
            try:
                book = card.find('figcaption').cite.text.strip() # book
            except:
                book = None
            auteur = card.find('figcaption').text.split("\n")[1].strip()[2:]
            poems.append(Quote(text, author = auteur, book = book,
                               source = 'eternels-eclairs', title=title,
                               url = url))
        except Exception as e:
            try:
                text = card.p.text
                title = card.h3.text
                figure_element = card.find('figure')
                figcaption_element = figure_element.find('figcaption')
                author_and_book = figcaption_element.text.strip()
                author, book = author_and_book.split(',', 1)
                author = author.strip()[2:]
                book = book.strip()
                poems.append(Quote(text, author = author, book = book,
                               source = 'eternels-eclairs', title=title,
                               url = url))
            except Exception as e:
                if ii > 0:
                    print(ii, "Error:", e) #, e.__class__, e.__class__.__name__)
                    # print(card)
    return poems

def run_eclair():
    l_url = """https://www.eternels-eclairs.fr/poemes-prevert.php
    https://www.eternels-eclairs.fr/poemes-chansons-textes-paroles-jacques-brel.php
    https://www.eternels-eclairs.fr/poemes-victor-hugo.php
    https://www.eternels-eclairs.fr/poemes-jean-de-la-fontaine.php
    https://www.eternels-eclairs.fr/poemes-rimbaud.php
    https://www.eternels-eclairs.fr/poemes-rilke.php
    https://www.eternels-eclairs.fr/poemes-apollinaire.php
    https://www.eternels-eclairs.fr/poemes-eluard.php
    https://www.eternels-eclairs.fr/poemes-maurice-careme.php
    https://www.eternels-eclairs.fr/poemes-baudelaire.php
    https://www.eternels-eclairs.fr/poemes-verlaine.php
    https://www.eternels-eclairs.fr/anthologie-haikus-livres.php
    https://www.eternels-eclairs.fr/haikus-japonais.php
    https://www.eternels-eclairs.fr/haikus-basho-buson-issa-shiki-santoka.php
    https://www.eternels-eclairs.fr/poesie-poemes-beaux-sonnets.php
    https://www.eternels-eclairs.fr/poesie-celebre-les-plus-beaux-poemes-et-poemes-les-plus-connus.php"""

    l_url = l_url.split('\n')

    for url in l_url:
        print(url)
        result = extract_poems_eclair(url)
        print("\t--- nb quotes:", len(result))
        # print(result[0])
        if len(result) > 0:
            df_quote = pd.DataFrame([quote.__dict__ for quote in result])
            df_quote.to_csv(f'data/eclair/{url[url.index(".fr/") + 4:][:-4]}.csv')
        time.sleep(10)