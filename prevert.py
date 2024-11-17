# python -m streamlit run prevert.py

from collections import defaultdict
import pandas as pd
import numpy as np
import pandas_gbq
from unidecode import unidecode
from scrap_utils import tokenize
from copy import copy

from google.oauth2 import service_account

import streamlit as st
from st_keyup import st_keyup # pip install streamlit-keyup
# import streamlit.components.v1 as components # pip install extra-streamlit-components
# from streamlit_extras.let_it_rain import rain
# import streamlit_antd_components as sac
# import streamlit_wordcloud as wordcloud # pip install streamlit-wordcloud

from utils import *

np.set_printoptions(precision=0)
st.set_page_config(page_title= "Prevert", page_icon = "🦋", # "🎶🧞"
                    layout="wide", # centered, wide
                )

st.title("🦋 🦎 🎶 🔥 🐉 🧞 🍄 🌈 🌚 ")
all_emoji = "🦎🔥🦋🎶🐉🧞🍄🌈🌚☘️☢️⛩️🌚꩜🐘" + "𝄞☯︎☣☘︎꩜⛩❄⚝☠𓆝⚕️⚛♫𓆈𓆉𓆏𓆸𓃰𓃥𓆝"

search_query = st_keyup(label = "Enter a value", key="uuid_keyup",
                         label_visibility="collapsed", debounce=400)

### load data
data = load_data()
raw_data = copy(data)
env = "web"
if len(raw_data) > 5000:
    env = "dev"


# @st.cache_data()
def run_bigquery(query):
    credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
    return pd.read_gbq(query, credentials=credentials)
    # Convert to list of dicts. Required for st.cache_data to hash the return value.
    # rows = [dict(row) for row in rows_raw]
    # return rows

def bq_insert_event(text_tok, column, new_value):
    credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
    st.toast(f'Edit {column} \n\n  {new_value}')
    query = f"""INSERT INTO `prevert.v1.events` 
    (timestamp,text_tok,source,action,field,new_value) 
    VALUES 
    CURRENT_timestamp(), {text_tok}, {env}, update, {column}, {new_value}"""
    st.toast(query)
    pd.read_gbq(query, credentials=credentials)

def read_bq(query):
    st.toast("query:" + query)
    a = run_bigquery(query)
    print(query, a)
    st.toast(a)
    st.write(a)

# st.write(client)
# st.write(credentials)
# st.write('start')
# query = "SELECT * from `prevert.v1.sample` limit 10"
# st.write(query)
# rows_raw = pandas_gbq.read_gbq(query, credentials=credentials)
# st.write("rqst received")
# st.write(rows_raw)
# st.write('Done')




# cc = st.color_picker('ccc', '#349E77') # #349E77 vert #C79236 orange 
# l_cc_haiku = ["#603D03", # marron               # "#38ECDE", # cyan               "#9A9317", # yellow               "#A45918", # orange               "#344AB1", # blue               "#8426B5", # purple               "#D25456", # red               "#94923A", # mousse               ]

### UI
def emoji_action(data, emoji):
    if emoji == "🔥":
        st.toast(f"🔥 {search_query}")
    if emoji == "🦋":
        st.toast(f"🦋 {search_query}")

if env == "log":
    lele = "🔥🦋🎶🐉🧞🍄🌈"
    le_col = st.columns([4]*(len(lele)+1) + [30], vertical_alignment = "center")
    with le_col[0]:
        st.button("Help", key = get_rnd_key(), on_click = help)

    for i in range(len(lele)):
        with le_col[i+1]:
            st.button(lele[i], key = get_rnd_key(), on_click = emoji_action, args = [data, lele[i]])


nb_columns = 2
all_expanded = True
show_action_buttons = env == "dev"

list_col_ui = st.columns([1]*10, vertical_alignment = "center")
# with list_col_ui[0]:
    # only_popular = st.toggle("Only popular", value = False) # 
    # like_cap = st.slider("Like", 0, 100, 0, label_visibility = 'collapsed')
    # like_cap = 20 if only_popular else 0
with list_col_ui[0]:    
    only_haiku = st.toggle("Haiku", value = False)
with list_col_ui[1]:
    only_title = st.toggle("Poème", value = False)
with list_col_ui[2]:
    only_react = True
    if env == "dev":
        only_react = st.toggle("Réactions", value = False)

# with list_col_ui[-4]:
#     st.button("dump_raw", key = get_rnd_key(), on_click = dump_raw, args = [raw_data])
with list_col_ui[-3]:
    st.button("Help", key = get_rnd_key(), on_click = help)
with list_col_ui[-2]:
    st.button("BQ get", key = get_rnd_key(), on_click = read_bq, args = [search_query]) # "SELECT * from `prevert.v1.sample` limit 10"
with list_col_ui[-1]:
    st.button("BQ ins", key = get_rnd_key(), on_click = insert_bq)


### Filter data
current_data = data
if search_query != "":
    search_words = unidecode(search_query.lower()) + " ".join([x for x in search_query if x in all_emoji])
    for word in search_words.split(" "):
        if word in '+=*&<>,./:$¨^?':
            continue
        current_data = current_data[current_data['all_search'].str.contains(word, case = False).dropna()]
if only_haiku:
    current_data = current_data[current_data.haiku]
if only_react:
    current_data = current_data[current_data.quote_react.notnull()]
if only_title:
    current_data = current_data[~current_data.title.isin({'nan', None, '', ' '})]
if current_data is None or len(current_data) == 0:
    st.write("No data found")
    st.stop()

# current_data.sort_values('nb_like', ascending = False, inplace = True)
# st.write(current_data)

### UI Sub-Stats
ac = current_data.groupby('author')['text'].count()
al = current_data.groupby('author')['nb_like'].sum()
stats = pd.merge(ac, al, on = 'author').rename(columns = {'text': 'Citations', 'nb_like': 'Like'}).sort_values('Like', ascending = False)
author_options = ['All ' + print_int(len(current_data)),] 
n_max_author = 13
for ii, (row, data) in enumerate(stats.iterrows()):
    if ii < n_max_author:
        author_options.append(f"{row}  {print_int(len(current_data[current_data.author == row]))}")
    else:
        author_options.append('...')
        break
select_author = None
if env == "dev":
    select_author = st.radio("radio", options= author_options,
          horizontal= True, label_visibility = 'collapsed')

if select_author is None:
    pass
elif select_author[:3] == 'All':
    pass
elif select_author == '...':
    current_data = current_data[~current_data.author.isin(list(stats.index)[:n_max_author])]
else:
    select_author_name = select_author.split('  ')[0]
    current_data = current_data[current_data.author == select_author_name]


### Display data
if '?' in search_query:
    current_data = current_data.sample(frac = 1, replace=False, random_state = len(search_query))
display_data = current_data[:30]
if "+" in search_query:
    display_data = current_data[:100]
if "*" in search_query:
    display_data = current_data
if "stats" in search_query:
    get_stats(raw_data, raw_data)
if "help" in search_query:
    help()
# TODO: if "author;text;" in search_query:
#     create_quote(author, text)
if "save" in search_query:
    save_bookmark(raw_data)
# if "dumpraw" in search_query:
#     st.toast(f'wanna \n {len(raw_data)} sss')
#     dump_raw(raw_data)
if search_query == "":
    display_data = current_data[:500].sample(n = min([len(current_data), 20]), replace=False)

list_col = st.columns(nb_columns)
for i, quote in enumerate(display_data.itertuples()):
    always_expand = quote.nb_lines < 4 and quote.nb_char < 400
    current_expand = all_expanded or always_expand
    if len(quote.text)> 1500:
        current_expand = False
    like_str = f'{int(np.round(quote.nb_like, 0))}' if (str(quote.nb_like) not in ['nan', '0', '0.0', '0.', 'None']) else ""
    title_str = f"{quote.title if (str(quote.title) != 'nan' and len(str(quote.title)) > 1) else ''}" 
    
    title_color = 'grey'
    # :red :orange :green :blue :violet :grey :rainbow :blue-background
    if quote.quote_react:
        # if quote.haiku: # 🦎,🦋,🎶,⛩️
        if "🦎" in quote.quote_react:
            title_color = "green"
        if "🎶" in quote.quote_react:
            title_color = "violet"
        if "🦋" in quote.quote_react:
            title_color = "blue"
        if "⛩️" in quote.quote_react or ("⛩" in quote.quote_react):
            title_color = "red"
        if "🔥" in quote.quote_react:
            title_color = "red"
        if "🌈" in quote.quote_react:
            title_color = "rainbow"
        str_quote_react = "".join([e for e in quote.quote_react if e not in "🌈🦋"])

    label = f":{title_color}[{quote.author}]"
    if quote.quote_react:
        label = label + '  ' + str_quote_react
    elif f"{title_str}" != "":
        pass
    elif like_str != "":
        label += "  :grey[ " + like_str + "]"
    else:
        pass
    with list_col[i % nb_columns].expander(
        label = label, #quote,
        expanded = current_expand,
        icon = None):

        if str(quote.title) != 'nan' and len(str(quote.title)) > 1:
            st.write(f":orange[{quote.title}]")

        if quote.haiku:
            st.write("  ")
            st.write(f"{quote.text}")
        else:
            st.write(f"{quote.text}")
            # :rainbow[]
        
        if str(quote.vo) != 'nan':
            st.write(f":grey[{quote.vo}]")

        info = "    " +\
             (f"{quote.book}" if str(quote.book) != 'nan' else "") +\
             (f", p{quote.page}" if str(quote.page) != 'nan' else "") +\
             (f", {quote.year}" if str(quote.year) != 'nan' else "")
            #  f"{quote.nb_lines} ({quote.nb_char}) - " +\
            #  f"{quote.author}" +\
            #  f"{quote.source} - " +\
            

        if show_action_buttons:
            if quote.haiku:
                l_dispo = "🦎,🦋,🎶,🔥,꩜".split(",")
            else:
                l_dispo = "🦎,🌈,🦋,🎶,🔥,🐉".split(",")
            list_col_button = st.columns([6,] + [1] * (len(l_dispo)) + [1,1,1])
            with list_col_button[0]:
                st.write(f":grey[{info}]")
            for i, icon in enumerate(l_dispo):
                with list_col_button[i+1]:
                    ans = st.button(icon,
                        key = get_rnd_key(),
                        on_click = save_quote,
                        args = [quote.text_tok, icon]) 
            with list_col_button[-3]:
                st.button("✏", key = get_rnd_key(),
                            help = "Éditer la citation", on_click = updating, args = [quote,])
            with list_col_button[-2]:
                st.button(f':grey[⨂]',
                               key = get_rnd_key(),
                               help = "Supprimer la citation", on_click = delete_quote,
                                args = [quote.text_tok,])
        
if len(display_data) == 30:
    if st.button("Load more", key = get_rnd_key()):
        search_query += "+"
