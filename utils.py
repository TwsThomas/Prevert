from collections import defaultdict
import pandas as pd
import numpy as np
from unidecode import unidecode
from scrap_utils import tokenize

import streamlit as st

@st.cache_data
def load_data():
    l_data = []
    for datafile in ['babelio_data', 'eclair_data', 'haiku_kerouac', 'manual author_data']:
        try:
            df = pd.read_csv(f'data/{datafile}.csv')
            df['haiku'] = df['haiku'].astype('bool')
            l_data.append(df)
        except Exception as e:
            print(f"Unable to load {datafile}.csv", e)
            
    data = pd.concat(l_data, ignore_index = True)
    data.drop(columns = ['Unnamed: 0',"Unnamed: 0.1"], inplace = True)
    data['text'] = data['text'].astype(str)
    data['vo'] = data['vo'].astype(str)
    data['title'] = data['title'].astype(str)
    data['haiku'] = data['haiku'].astype(bool)
    data['sonnet'] = data['sonnet'].astype(bool)
    data = data.sort_values('nb_like', ascending = False)
    data['text_tok'] = data['text'].apply(lambda x: tokenize(x))
    data.drop_duplicates(subset = ['text_tok'], inplace=True)
    data.set_index('text_tok', inplace = True, drop = False)

    # add saved quote
    data['quote_react'] = None
    d_quote_react = defaultdict(list)
    try:
        with open("interactions/quote_react.txt", "r") as f:
            for line in f:
                icon = line[0].replace("⛩", "⛩️")
                d_quote_react[tokenize(line[1:])] += [icon]
                # st.toast(icon + '**' + line[1:])
    except Exception as e:
        print('unable to load - quote_react.txt', e)
    set_quote_deleted = set()
    # remove deleted quote
    try:
        with open("interactions/quote_deleted.txt", "r") as f:
            for line in f:
                set_quote_deleted.add(line.strip())
    except Exception as e:
        print('unable to load - quote_deleted.txt', e)
    # update quote modified
    try:
        with open("interactions/quote_update.txt", "r") as f:
            for line in f:
                text_tok, column, new_value = line.strip().split('$')
                if text_tok in data.index:
                    data.loc[text_tok, column] = new_value.replace('/n/', '\n')
    except Exception as e:
        print('unable to load - quote_update.txt', e, e.__class__, e.__class__.__name__)

    data['quote_react'] = data.text_tok.apply(lambda txt: "".join(d_quote_react.get(txt, None)) if txt in d_quote_react else None)
    data['all_search'] = (data['text_tok'].astype(str)) + (data['text'].astype(str)) + (data['author'].astype(str).apply(tokenize)) + (data['book'].astype(str).apply(tokenize)) + (data['title'].astype(str).apply(tokenize)) + data['quote_react'].astype(str)
    data['haiku'] = data['haiku'] & (data['nb_lines'] == 3)
    data["nb_like"] = data["nb_like"].apply(lambda a: a if str(a) not in ['nan', 'None'] else 0) + data['quote_react'].apply(lambda x: 50 * len(x) if x else 0)
    data = data[~data.text_tok.isin(set_quote_deleted)]
    data.sort_values('nb_like', ascending = False, inplace = True)
    return data

def get_rnd_key():
    return str(np.random.randint(1000000000))
def print_int(x):
    # use k notation
    if x > 1000:
        return str(int(np.round(x/1000, 0))) + "k"
    return str(int(np.round(x, 0)))

def save_quote(q, icon, toast = True):
    if toast:
        st.toast(icon + icon+\
             f' \n \n  {q}')
    with open("interactions/quote_react.txt", "a") as f:
        # st.toast(":orange[NOT SAVED]")
        f.write(f"{icon}{q}\n")

def delete_quote(q):
    st.toast(f'⨂ Delete: "{q}"')
    with open("interactions/quote_deleted.txt", "a") as f:
        f.write(f"{q}\n")

def update_quote(text_tok, column, new_value):
    with open("interactions/quote_update.txt", "a") as f:
        f.write(f"{text_tok}${column}${new_value}\n")
    st.toast(f'Edit {column} \n\n  {new_value}')
    # data.loc[data.text_tok == text_tok, column] = new_value

def remove_react(text_tok):
    with open("interactions/quote_react.txt", "r") as f:
        lines = f.readlines()
    with open("interactions/quote_react.txt", "w") as f:
        for line in lines:
            if text_tok not in line:
                f.write(line)
    # st.toast(f'☢️ Reactions removed ☢️ ')
