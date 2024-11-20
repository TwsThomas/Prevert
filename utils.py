from collections import defaultdict
import pandas as pd
import numpy as np
from unidecode import unidecode
from scrap_utils import tokenize

import streamlit as st

from google.oauth2 import service_account
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])


bq_insert_query_intro = f"""INSERT INTO `prevert.v1.events` 
(timestamp,text_tok,source,action,field,new_value,create_title,create_author,create_note) 
VALUES 
"""

@st.cache_data
def load_data():
    data_ram = pd.read_parquet('data_v2/data_ram.parquet')
    # data_ram.set_index('text_tok', inplace = True, drop = True)
    data_ram['all_search'] = (data_ram.index.astype(str)) + (data_ram['author'].astype(str).apply(tokenize))+ (data_ram['text'].astype(str).apply(tokenize)) + (data_ram['book'].astype(str).apply(tokenize)) + (data_ram['title'].astype(str).apply(tokenize)) + data_ram['quote_react'].astype(str)
    data_ram.sort_values('nb_like', ascending = False, inplace = True)
    return data_ram

def get_rnd_key():
    return str(np.random.randint(1000000000))
def print_int(x):
    # use k notation
    if x > 1000:
        return str(int(np.round(x/1000, 0))) + "k"
    return str(int(np.round(x, 0)))

@st.dialog("Raccourcis dans la barre de recherche")
def help(context):
    st.write('🦋🦎🎶🔥🐉🧞🍄🌈🌚⛩️')
    st.write(' :rainbow[citation] :red[; ;]  :grey[Ajoute la citation]')
    st.write(" :orange[auteur] ; :rainbow[citation] :red[; ;]   :grey[Ajoute la citation avec l'auteur]")

    st.write(':blue[?] : :grey[Classement aléatoire]')
    st.write(':blue[+] : :grey[Top 100]')
    st.write(':blue[*] : :grey[Tout]')
    st.write(':blue[stats] : :grey[Statistiques]')

    # st.write(' -- debug')
    st.write(' :green[get_context] : :grey[get current context (localhost vs web)]')
    if 'local' in context:
        st.write(' :green[run_sync] or :green[bq_sync] : :grey[Send the update-batch from csv to BQ then update data, concat and save in data_v2/data_ram.parquet]')
    st.write('Scoobydoobydoo !;Scooby-Doo;')


# @st.dialog("Stats")
def get_stats(ddata):

    st.write(len(ddata[ddata['quote_react'].notnull()]) , "emojis")
    st.write(len(ddata[ddata['haiku']]) , "haikus")
    st.write(len(ddata[~ddata['title'].isin({'nan', None, '', ' '})]) , "poèmes")
    st.write(len(ddata), "citations")

    ac = ddata.groupby('author')['text'].count()
    al = ddata.groupby('author')['nb_like'].sum()
    ah = ddata.groupby('author')['haiku'].sum()
    ar = ddata.groupby('author')['quote_react'].count()
    stats = pd.merge(ac, al, on = 'author').rename(columns = {'text': 'Citations', 'nb_like': 'Like'}).sort_values('Like', ascending = False)
    stats = pd.merge(stats, ah, on = 'author').rename(columns = {'haiku': 'Haiku'})
    stats = pd.merge(stats, ar, on = 'author').rename(columns = {'quote_react': 'Saved'})
    stats.sort_values('Saved', ascending = False, inplace = True)
    st.write(stats)


def bq_insert_event(text, action, column=None, new_value=None,title=None,author=None,note=None, context=None):
    try:
        credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        sn = "\n"
        ssn = "\\n"
        query_value = fr"""(CURRENT_timestamp(), "{text.replace(sn, ssn)}", "{context}", "{action}", "{column}", "{new_value}", "{title}", "{author}", "{note}")"""
        if context == "localhost":
            with open('batch_query_value.txt', 'a') as f:
                f.write(query_value + ' ,\n')
            st.toast("batched")
        else:
            pd.read_gbq(bq_insert_query_intro + '\n' + query_value, credentials=credentials)
    except Exception as e:
        print('unable to insert event', e,  e.__class__.__name__, e.__class__,)
        st.write('unable to insert event', e,  e.__class__.__name__, e.__class__,)
        st.toast(e.__class__.__name__)

def delete_quote(text_tok, context):
    bq_insert_event(text_tok, action = "delete", context=context)
    st.toast(f'⨂ Deleted: \n\n  "{text_tok}"')

def update_quote(text_tok, column, new_value, context):
    bq_insert_event(text_tok, action="update", column=column, new_value=new_value, context=context)
    st.toast(f'✏ Edited {column} \n\n  {new_value}')

def add_react(text_tok, icon, context, toast = True):
    bq_insert_event(text_tok, action="react", new_value=icon, context=context)
    if toast:
        st.toast(icon)

def remove_react(text_tok, context):
    st.toast(f'☢️ Reactions removed not implemented yet ☢️ ')

def get_hyperlink(quote, context):
    return f"https://twsthomas.streamlit.app/?search={quote.author} {' '.join([w for w in quote[0].split(' ') if len(w) > 2][:5])}".replace(' ', "_")

def copyclip(quote, context):
    st.code(get_hyperlink(quote, context), language="python")
    try:
        import pyperclip
        pyperclip.copy(get_hyperlink(quote, context))
        st.toast("🔗 Copied to clipboard")
    except:
        pass

@st.dialog("Edit quote")
def updating(quote, context):
    
    if context == "android":
        lala = "🦎🔥🦋🎶🐉🧞🍄🌈"
    else:
        lala = "🍄🐘🧞⛩️" + ("🌈" if quote.haiku else "") + "🔗"
    le_col = st.columns([1]*(len(lala)) + [5], vertical_alignment = "center")
    for i, icon in enumerate(lala):
        with le_col[i]:
            if icon == "🔗":
                st.button(icon, key = get_rnd_key(), 
                      on_click = copyclip, args = [quote, context]) 
            else:
                st.button(icon, key = get_rnd_key(), 
                      on_click = add_react, args = [quote[0], icon, context, False]) 

    new_title = quote.title
    new_text = quote.text
    new_author = quote.author
    new_title = st.text_input("Titre", quote.title)
    new_text = st.text_area("Citation", value = quote.text)
    new_author = st.text_input("Auteur", value = quote.author)
    st.code(get_hyperlink(quote, context), language="python")
    # kill_react = st.button("Retirer les réactions ☢️", key = get_rnd_key(),
    #                        on_click=remove_react, args=[quote[0],context])
    # add_note = st.text_area("Notes", value = quote.vo)

    if new_text != str(quote.text):
        new_text_saved = new_text.replace('\n','  /n/')
        update_quote(quote[0], 'text', new_text_saved, context)
    if new_author != str(quote.author):
        update_quote(quote[0], 'author', new_author, context)
    if new_title != str(quote.title):
        update_quote(quote[0], 'title', new_title, context)
    # if add_note != str(quote.note):
    #     new_note_saved = add_note.replace('\n','  /n/')
    #     update_quote(quote[0], 'vo', new_note_saved, context)

def dump_data_ram(raw_data):
    # import pickle
    # pickle.dump(raw_data.drop(['Unnamed: 0.1','Unnamed: 0', 'all_search'], axis=1), open('data/raw_data_v1_17_nov.pkl', 'wb'))
    # raw_data.to_csv('data/raw_data_v1x.csv', index = False)
    # raw_data.drop(['Unnamed: 0.1','Unnamed: 0', 'all_search'], axis=1).to_parquet('data/raw_data_v1_17_nov.parquet', index = False)
    raw_data.head(10).to_csv('data_v2/dump_data_ram_10.csv', index = True)
    raw_data.to_csv('data_v2/dump_data_ram.csv', index = True)
    raw_data.head(10).to_parquet('data_v2/dump_data_ram_10.parquet', index = True)
    raw_data.to_parquet('data_v2/dump_data_ram.parquet', index = True)
    st.toast(f'\n {len(raw_data)} csv clean')
    st.write(f'\n {len(raw_data)} csv clean')


def data_append(data_ram, text, author, title = "", note = "", context = ""):
    """ add a new citation on the ram (for cosmetic purpose) """
    new_data = pd.DataFrame({'text': text, 'author': author, 'book' : None, 'title': title, 'nb_like':0, "haiku" : False, "quote_react" : "🐉🐉🐉",
                              'note': note, 'all_search': tokenize(text) + author + title + note},
                              index = [text])
    if "extra_data" not in st.session_state:
        st.session_state['extra_data'] = new_data
    else:
        st.session_state['extra_data'] = pd.concat([st.session_state['extra_data'], new_data], axis = 0)

def bq_update_data():
    """ load data_v1 from parquet
    and events from BQ 
    then update all data 
    dump in data_v2/data_ram.parquet """

    credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])

    # archive from data_v1 (i.e. all scrapping)
    data_v1 = pd.read_parquet('data_v2/raw_data_v1_17_nov_.parquet') 
    data_v1['note'] = data_v1['vo']
    data_v1['all_search'] = (data_v1['text_tok'].astype(str)) + (data_v1['author'].astype(str).apply(tokenize)) + (data_v1['book'].astype(str).apply(tokenize)) + (data_v1['title'].astype(str).apply(tokenize)) + data_v1['quote_react'].astype(str)
    data_v1.set_index('text_tok', inplace = True, drop = True)
    data_v1.drop(['year', 'source', 'confiance', 'page', 'url', 'nb_char', 'nb_lines', 'sonnet', 'vo'], axis = 1, inplace = True)
    data_v1['is_delete'] = False
    st.write('data_v1 loaded')

    # add events
    with open('bq_view_updated.sql', 'r') as f:
        query_view = f.read()
    df_updated = pd.read_gbq(query_view, credentials=credentials)
    st.write(f'{len(df_updated)} events loaded')

    df_updated['text'] = df_updated['quote'].apply(lambda x: x.get('text', ''))
    df_updated['text_tok'] = df_updated['quote'].apply(lambda x: x.get('text', '')) # no tokenize (events text_tok are consider as is (will be tokenize in all_search))
    df_updated['author'] = df_updated['quote'].apply(lambda x: x.get('author', ''))
    df_updated['book'] = df_updated['quote'].apply(lambda x: x.get('book', ''))
    df_updated['title'] = df_updated['quote'].apply(lambda x: x.get('title', ''))
    df_updated['quote_react'] = df_updated['extra'].apply(lambda x: x.get('quote_react', ''))
    df_updated['note'] = df_updated['extra'].apply(lambda x: x.get('note', ''))
    df_updated['haiku'] = df_updated['text'].apply(lambda x: len(x.split('\n')) == 3)
    df_updated['nb_like'] = df_updated['quote_react'].apply(lambda x: (len(x) * 50) if x is not None else 0)
    df_updated['all_search'] = (df_updated['text_tok'].astype(str).apply(tokenize)) + ' ' + (df_updated['author'].astype(str).apply(tokenize)) +' ' + (df_updated['book'].astype(str).apply(tokenize)) + ' ' +(df_updated['title'].astype(str).apply(tokenize)) +' ' + df_updated['quote_react'].astype(str)

    df_updated = df_updated[['text', 'author', 'book', 'title', 'nb_like', 'text_tok', 'haiku', 'quote_react', 'note', 'all_search', 'is_delete']]
    df_updated.set_index('text_tok', inplace = True, drop = True)

    data_ram = pd.concat([df_updated, data_v1], axis = 0)
    data_ram['is_delete'] = data_ram['is_delete'].replace(np.nan, False)
    # drop duplicates index
    data_ram = data_ram[~data_ram.index.duplicated(keep='first')]
    data_ram.sort_values('nb_like', ascending = False, inplace = True)
    data_ram = data_ram[~data_ram['is_delete']]
    data_ram.drop(['is_delete', 'all_search'], axis = 1, inplace = True)
    # data_ram.drop(['is_delete'], axis = 1, inplace = True)

    data_ram['author'] = data_ram['author'].astype(str)
    data_ram['book'] = data_ram['book'].astype(str).replace('None', None)
    data_ram['title'] = data_ram['title'].astype(str).replace('nan', None)
    data_ram['quote_react'] = data_ram['quote_react'].astype(str).replace('None', None)
    data_ram['note'] = data_ram['note'].astype(str).replace('nan', None)
    # data_ram['all_search'] = data_ram['all_search'].astype(str)
    data_ram['text'] = data_ram['text'].astype(str)
    data_ram['haiku'] = data_ram['haiku'].astype(bool)
    data_ram['nb_like'] = data_ram['nb_like'].astype(int)

    st.write('data_ram updated')
    data_ram.to_parquet('data_v2/data_ram.parquet')
    st.write('data_ram dumped on data_v2/data_ram.parquet')