from collections import defaultdict
import pandas as pd
import numpy as np
from unidecode import unidecode
from scrap_utils import tokenize

from google.oauth2 import service_account

import streamlit as st

bq_insert_query_intro = f"""INSERT INTO `prevert.v1.events` 
(timestamp,text_tok,source,action,field,new_value,create_title,create_author,create_note) 
VALUES 
"""

@st.cache_data
def load_data():
    data_v1 = pd.read_parquet('data_v2/raw_data_v1_17_nov.parquet')
    data_v1['text'] = data_v1['text'].astype(str)
    data_v1.set_index('text_tok', inplace = True, drop = False)
    data_v1.sort_values('nb_like', ascending = False, inplace = True)
    data_v1['all_search'] = (data_v1['text_tok'].astype(str)) + (data_v1['text'].astype(str)) + (data_v1['author'].astype(str).apply(tokenize)) + (data_v1['book'].astype(str).apply(tokenize)) + (data_v1['title'].astype(str).apply(tokenize)) + data_v1['quote_react'].astype(str)
    return data_v1

def get_rnd_key():
    return str(np.random.randint(1000000000))
def print_int(x):
    # use k notation
    if x > 1000:
        return str(int(np.round(x/1000, 0))) + "k"
    return str(int(np.round(x, 0)))

def clear_cache():
    # not tested
    st.caching.clear_cache()
    st.toast("Cache cleared")

@st.dialog("Raccourcis dans la barre de recherche")
def help():
    st.write('🦋🦎🎶🔥🐉🧞🍄🌈🌚⛩️')
    st.write(' :rainbow[citation] :red[; ;]  Ajoute la citation')
    st.write(" :orange[auteur] ; :rainbow[citation] :red[; ;]   Ajoute la citation avec l'auteur")

    st.write('*?* : Classement aléatoire')
    st.write('*+* : Top 100')
    st.write('_*_ : Tout')
    st.write(' _stats_ : Statistiques')
    st.write(' -- debug')
    st.write(' _get_context_ : get_context (localhost vs web)')
    st.write(' _batch_bq_ : Send the update-batch to BQ')


# @st.dialog("Stats")
def get_stats(ddata, raw_data):

    st.write(len(raw_data[raw_data['quote_react'].notnull()]) , "emojis")
    st.write(len(raw_data[raw_data['haiku']]) , "haikus")
    st.write(len(raw_data[~raw_data['title'].isin({'nan', None, '', ' '})]) , "poèmes")
    st.write(len(raw_data), "citations")

    ac = ddata.groupby('author')['text'].count()
    al = ddata.groupby('author')['nb_like'].sum()
    ah = ddata.groupby('author')['haiku'].sum()
    ar = ddata.groupby('author')['quote_react'].count()
    stats = pd.merge(ac, al, on = 'author').rename(columns = {'text': 'Citations', 'nb_like': 'Like'}).sort_values('Like', ascending = False)
    stats = pd.merge(stats, ah, on = 'author').rename(columns = {'haiku': 'Haiku'})
    stats = pd.merge(stats, ar, on = 'author').rename(columns = {'quote_react': 'Saved'})
    stats.sort_values('Saved', ascending = False, inplace = True)
    st.write(stats)


def bq_insert_event(text_tok, action, column=None, new_value=None,title=None,author=None,note=None, context=None):
    try:
        credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        query_value = f'(CURRENT_timestamp(), "{text_tok}", "{context}", "{action}", "{column}", "{new_value}", "{title}", "{author}", "{note}")'
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

def add_react(text_tok, icon, context):
    bq_insert_event(text_tok, action="react", new_value=icon, context=context)
    st.toast(icon)

def remove_react(text_tok, context):
    st.toast(f'☢️ Reactions removed not implemented yet ☢️ ')

@st.dialog("Edit quote")
def updating(quote, context):
    
    lala = "🍄🐘🌚🧞⛩️" + ("🌈" if quote.haiku else "")
    le_col = st.columns([1]*(len(lala)) + [5], vertical_alignment = "center")
    for i, icon in enumerate(lala):
        with le_col[i]:
            st.button(icon, key = get_rnd_key(), 
                      on_click = add_react, args = [quote.text_tok, icon, context]) 
            
    new_title = quote.title
    new_text = quote.text
    new_author = quote.author
    new_title = st.text_input("Titre", quote.title)
    new_text = st.text_area("Citation", value = quote.text)
    new_author = st.text_input("Auteur", value = quote.author)
    kill_react = st.button("Retirer les réactions ☢️", key = get_rnd_key(),
                           on_click=remove_react, args=[quote.text_tok,context])
    # add_note = st.text_area("Notes", value = quote.vo)

    if new_text != str(quote.text):
        new_text_saved = new_text.replace('\n','  /n/')
        update_quote(quote.text_tok, 'text', new_text_saved, context)
    if new_author != str(quote.author):
        update_quote(quote.text_tok, 'author', new_author, context)
    if new_title != str(quote.title):
        update_quote(quote.text_tok, 'title', new_title, context)
    # if add_note != str(quote.note):
    #     new_note_saved = add_note.replace('\n','  /n/')
    #     update_quote(quote.text_tok, 'vo', new_note_saved, context)

def dump_raw(raw_data):
    # import pickle
    # pickle.dump(raw_data.drop(['Unnamed: 0.1','Unnamed: 0', 'all_search'], axis=1), open('data/raw_data_v1_17_nov.pkl', 'wb'))
    # raw_data.to_csv('data/raw_data_v1x.csv', index = False)
    # raw_data.drop(['Unnamed: 0.1','Unnamed: 0', 'all_search'], axis=1).to_parquet('data/raw_data_v1_17_nov.parquet', index = False)
    raw_data.head(900).to_parquet('data/raw_data_sample_900.parquet', index = False)
    st.toast(f'\n {len(raw_data)} parquet clean')
    st.write(f'\n {len(raw_data)} parquet clean')