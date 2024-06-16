import os
import json
import streamlit as st
import random
from google.cloud import storage
from datetime import datetime
import tempfile

# Accesarea variabilei de mediu
credentials_content = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_CONTENT')

# Crearea unui fișier temporar pentru cheile de autentificare
with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
    temp_file.write(credentials_content.encode())
    temp_file_name = temp_file.name

# Initializare
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_file_name

storage_client = storage.Client()
bucket_name = 'sondaj1_bucket'
bucket = storage_client.bucket(bucket_name)

def download_json_from_gcs(bucket_name, json_filename):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(json_filename)
    data = blob.download_as_text()
    return json.loads(data)

json_filename = "expressions.json"
data = download_json_from_gcs(bucket_name, json_filename)

st.title("Interpretarea Creativă a Metaforelor Lingvistice prin Modele Multimodale")

descriere = """
Scopul acestui site este de a realiza un sondaj de opinie pentru a valida dacă imaginile generate de mine sunt mai bune decât cele dintr-un set de date existent. 
Contextul acestei lucrări de licență este crearea unui model multimodal care primește ca input o metaforă și produce o imagine ce ilustrează sensul acesteia. 
Setul de date existent conține imagini generate care reprezintă doar metafora în mod concret, nu și sensul ei profund. 
Acest site este creat pentru a evalua dacă imaginile generate de mine pentru un set minimal de metafore sunt mai bune decât cele din setul de date existent.
"""
st.write(descriere)

# CSS pentru alinierea radio button-urilor
st.markdown("""
    <style>
        .stRadio [role=radiogroup]{
            align-items: center;
            justify-content: center;
        }
    </style>
""", unsafe_allow_html=True)

# Dicționar pentru a stoca răspunsurile utilizatorilor
if "responses" not in st.session_state:
    st.session_state.responses = {}

if "initial_images" not in st.session_state:
    st.session_state.initial_images = {}

# Funcție pentru afișarea imaginilor și radio button-urilor
def afiseaza_metafore(metafore_imagini):
    for idx, metafora in enumerate(metafore_imagini):
        st.subheader(metafora["text"])

        if metafora["text"] not in st.session_state.initial_images:
            imagini_random = list(metafora["image_urls"])
            random.shuffle(imagini_random)
            st.session_state.initial_images[metafora["text"]] = imagini_random
        else:
            imagini_random = st.session_state.initial_images[metafora["text"]]

        num_imagini = len(imagini_random)
        options = [f"Imagine {i + 1}" for i in range(num_imagini)] + ["Toate", "Niciuna"]

        col = st.columns(num_imagini)

        label_to_url = {f"Imagine {idx + 1}": img for idx, img in enumerate(imagini_random)}

        for idx, img in enumerate(imagini_random):
            with col[idx]:
                st.image(img, use_column_width=True)

        selected_option = st.radio('Selecteaza o optiune', options=options, horizontal=True,
                                   key=f'radio_{metafora["text"]}', index=None)

        if selected_option == "Toate":
            st.session_state.responses[metafora["text"]] = imagini_random
        elif selected_option == "Niciuna":
            st.session_state.responses[metafora["text"]] = []
        elif selected_option is not None:
            st.session_state.responses[metafora["text"]] = [label_to_url[selected_option]]

# Afișarea metaforelor cu imaginile și radio button-urile
afiseaza_metafore(data)

# Buton pentru trimiterea răspunsurilor
if st.button('Trimite răspunsurile'):
    # Generarea unui timestamp pentru unicitatea numelui fișierului
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    responses_filename = f"responses_{timestamp}.json"

    # Salvarea răspunsurilor într-un fișier JSON
    with open(responses_filename, "w") as responses_file:
        json.dump(st.session_state.responses, responses_file)

    # Încărcarea fișierului JSON în Google Cloud Storage
    responses_blob = bucket.blob(f"responses/{responses_filename}")
    responses_blob.upload_from_filename(responses_filename)
    responses_blob.make_public()  # Opțional: face fișierul JSON public

    st.write("Răspunsurile au fost trimise. Mulțumim pentru participare!")
