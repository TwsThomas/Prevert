# python -m streamlit run prevert.py

from collections import defaultdict
import pandas as pd
import numpy as np
from unidecode import unidecode
from copy import copy
# from scrap_utils import tokenize

import streamlit as st
from st_keyup import st_keyup # pip install streamlit-keyup
# import streamlit.components.v1 as components # pip install extra-streamlit-components
# from streamlit_extras.let_it_rain import rain
# import streamlit_antd_components as sac
# import streamlit_wordcloud as wordcloud # pip install streamlit-wordcloud
# streamlit_user_device
from utils import *

np.set_printoptions(precision=0)
st.set_page_config(page_title= "Prevert", page_icon = "🦋", # "🎶🧞"
                    layout="wide", # centered, wide
                )
context = "unknow"
try:
    if "localhost" in st.context.headers["Host"]:
        context = "localhost"
    else:
        if "android" in st.context.headers["User-Agent"].lower():
            context = "android"
        if "iphone" in st.context.headers["User-Agent"].lower():
            context = "iphone"
        if "Mac OS X" in st.context.headers["User-Agent"]:
            context = "mac"
        if st.context.headers.get("X-Streamlit-User", "none") not in ["eyJlbWFpbCI6IiIsImlzUHVibGljQ2xvdWRBcHAiOnRydWV9", "eyJlbWFpbCI6InR3c3Rob21hc0BnbWFpbC5jb20iLCJpc1B1YmxpY0Nsb3VkQXBwIjpmYWxzZX0="]:
            context += '?'
except Exception as e:
    st.toast(e)

if context == "android":
    st.title("🦋🦎🍄🎶🌈🌚") 
else:
    st.title("🦋 🦎 🎶 🔥 🐉 🧞 " + ("🍄" if context == "localhost" else "⛩️") +" 🌈 🌚 ")
all_emoji = "🦎🔥🦋🎶🐉🧞🍄🌈🌚☘️☢️⛩️🌚꩜🐘🩸🎏" + "𝄞☯︎☣☘︎꩜⛩❄⚝☠𓆝⚕️⚛♫𓆈𓆉𓆏𓆸𓃰𓃥𓆝"

init_search = st.query_params.get("search", "").replace('_', ' ')
search_query = st_keyup(label = "Enter a value", key="uuid_keyup",
                         label_visibility="collapsed", debounce=400,
                         value = init_search)


### load data
all_data = load_data()
if 'extra_data' in st.session_state:
    all_data = pd.concat([st.session_state['extra_data'], all_data,], axis = 0)


# cc = st.color_picker('ccc', '#349E77') # #349E77 vert #C79236 orange 
# l_cc_haiku = ["#603D03", # marron               # "#38ECDE", # cyan               "#9A9317", # yellow               "#A45918", # orange               "#344AB1", # blue               "#8426B5", # purple               "#D25456", # red               "#94923A", # mousse               ]

### Special search
if "stats" in search_query:
    get_stats(all_data)
    st.stop()
# "quote;author;;" in search_query
if ";;" == search_query[-2:]:
    pp = search_query[:-2].split(";")
    author = "Inconnu"
    if len(pp) == 1:
        text = pp[0]
    if len(pp) == 2:
        text, author = pp[0].strip(), pp[1].strip()
        if len(author) > len(text):
            text, author = author, text

    st.write(":orange[Création d'une nouvelle citation] : ")
    bq_insert_event(text, "create", column=None, new_value=None,title=None,author=author, note=None, context=context)
    all_data = data_append(all_data, text, author, title="", note="", context=context)
    st.write({"Texte": text, "Auteur": author})
    st.stop()
if "help" in search_query:
    help(context)

# local functions
if "get_context" in search_query:
    with open('batch_query_value.txt', 'r') as f:
            query_values = f.read()[:-1]
    st.write(":orange[context]: " + context)
    st.write(st.query_params)
    st.write(st.context.headers)
    st.stop()

if "st.session_state" in search_query:
    st.write(st.session_state)
    st.stop()
if search_query in ["run_sync", "bq_run", "bq_sync", "bq_batch", "bq_update"]:
    st.write('run bq_update_data()')
    """ Insert into bq.events all batch_query_value.txt then update data """
    st.write(':orange[run data_sync...]')
    if 'local' in context:
        try:
            with open('batch_query_value.txt', 'r') as f:
                query_values = f.read()[:-2] # remove last comma
                if len(query_values) > 0:
                    pd.read_gbq(bq_insert_query_intro + query_values, credentials=credentials)
                    # st.toast("batch send to BQ\n\n" + str(len(query_values.split('\n')))  + "elements")
                    st.write("batch send to BQ\n\n", str(len(query_values.split('\n'))), "elements")
                with open('batch_query_value.txt', 'w') as f:
                    f.write("")
        except Exception as e:
            print('unable to insert event', e,  e.__class__.__name__, e.__class__,)
            st.write('/!!\ Unable to insert event', e,  e.__class__.__name__, e.__class__,)
            st.toast(e.__class__)
            st.stop()
    st.write('run bq_update_data()')
    bq_update_data()
    st.write(':blue[Done --]')
    load_data.clear()
    st.toast('Clean & Done !')
    st.stop()

### UI
nb_columns = 2
show_action_buttons = True
n_max_author = 6 if context == "android" else 13 

list_col_ui = st.columns([1]*8, vertical_alignment = "center")
with list_col_ui[0]:    
    only_haiku = st.toggle("Haiku", value = st.query_params.get("haiku") is not None)
with list_col_ui[1]:
    only_title = st.toggle("Poème", value = st.query_params.get("poeme") is not None)
with list_col_ui[2]:
    only_react = st.toggle("Réactions", value = st.query_params.get("reaction") is not None)

with list_col_ui[-1]:
    st.button("Help", key = get_rnd_key(), on_click = help, args=[context])


### Filter data -- search
current_data = all_data
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
    current_data = current_data[~current_data.title.isin({'nan', None, '', ' ', 'Nan'})]


### UI Sub-Stats
ac = current_data.groupby('author')['text'].count()
al = current_data.groupby('author')['nb_like'].sum()
stats = pd.merge(ac, al, on = 'author').rename(columns = {'text': 'Citations', 'nb_like': 'Like'}).sort_values('Like', ascending = False)
author_options = ['All ' + print_int(len(current_data)),] 
for ii, (row, _) in enumerate(stats.iterrows()):
    if ii < n_max_author:
        author_options.append(f"{row}  *{print_int(len(current_data[current_data.author == row]))}*")
    else:
        author_options.append('...')
        break
select_author = None
if len(author_options) > 1:
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


### Search display results
if '?' in search_query:
    current_data = current_data.sample(frac = 1, replace=False, random_state = len(search_query))
display_data = current_data[:30]
if "+" in search_query:
    display_data = current_data[:100]
if "*" in search_query:
    display_data = current_data

# if "dump_data_ram" in search_query:
#     dump_data_ram(raw_data)
#     st.stop()


### Display data
if current_data is None or len(current_data) == 0:
    st.write("No data found")
    st.stop()
if search_query == "":
    display_data = current_data[:500].sample(n = min([len(current_data), 20]), replace=False, random_state=0)

list_col = st.columns(nb_columns)
for i, quote in enumerate(display_data.itertuples()):
    text_tok = quote[0]
    current_expand = len(quote.text.split('\n')) < 7 and len(quote.text) < 900
    like_str = f'{int(np.round(quote.nb_like, 0))}' if (str(quote.nb_like) not in ['nan', '0', '0.0', '0.', 'None']) else ""
    title_str = f"{quote.title if (str(quote.title) not in ['nan', 'None', None, '', ' '] and len(str(quote.title)) > 1) else ''}" 
    
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
        label = label + '  ' + str_quote_react.replace('𝄞', '')
    elif f"{title_str}" != "":
        pass
    elif like_str != "":
        label += "  :grey[ " + like_str + "]"
    else:
        pass
    with list_col[i % nb_columns].expander(
        label = label + (f" - - :orange[{title_str}] - - " if not current_expand else ""),
        expanded = current_expand,
        icon = None):

        if title_str != "":
            st.write(f":orange[{title_str}]")

        if quote.haiku:
            st.write("  ")
            st.write(f"{quote.text}")
        else:
            st.write(f"{quote.text}")
            # :rainbow[]
        
        if str(quote.note) not in ['nan', 'None', None, '']:
            st.write(f":grey[{quote.note}]")

        info = "    " +\
             (f"{quote.book[:45]}" if str(quote.book) not in  ["None", 'nan'] else "")
            #  (f", p{quote.page}" if str(quote.page) not in  ["None", 'nan'] else "") +\
            #  (f", {quote.year}" if str(quote.year) not in  ["None", 'nan'] else "")
            #  f"{quote.nb_lines} ({quote.nb_char}) - " +\
            #  f"{quote.author}" +\
            #  f"{quote.source} - " +\
            

        if show_action_buttons:
            if quote.haiku:
                l_dispo = "🦎,🦋,🎶,🔥,🌚".split(",")
            else:
                l_dispo = "🦎,🌈,🦋,🎶,🔥,🐉,🌚".split(",")
            if context == "android":
                l_dispo = []
            list_col_button = st.columns([6,] + [1] * (len(l_dispo)) + [1,1,1])
            with list_col_button[0]:
                st.write(f":grey[{info}]")
            for i, icon in enumerate(l_dispo):
                with list_col_button[i+1]:
                    ans = st.button(icon,
                        key = get_rnd_key(),
                        on_click = add_react,
                        args = [text_tok, icon, context]) 
            with list_col_button[-3]:
                st.button("✏", key = get_rnd_key(),
                            help = "Éditer la citation", on_click = updating, args = [quote, context, all_data])
            with list_col_button[-2]:
                if context != "android":
                    st.button(f':grey[⨂]',
                               key = get_rnd_key(),
                               help = "Supprimer la citation", on_click = delete_quote,
                                args = [text_tok, context])

if len(display_data) == 30:
    if st.button("Load more", key = get_rnd_key()):
        search_query += "+"
