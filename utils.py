import streamlit as st
import pandas as pd

# Sayfa ayarları
st.set_page_config(layout="wide")

# Sayfayı ortalayan ve sabitleyen çerçeve yapısı
def page_wrapper():
    # Sayfayı 3'e böl, ortadaki kısımları ana içerik alanı yap
    left_spacer, main_content, right_spacer = st.columns([1, 4, 1])
    return main_content

# Kullanımı:
# İçeriğini artık 'content' değişkeninin içinde yazacaksın
content = page_wrapper()

with content:
    st.title("Personel Sicil Kartları")
    # Formların, butonların ve tabloların artık bu 'content' içinde olacak
    # Bu sayede asla ekranın kenarlarına kadar esnemeyecekler!

def init_session():
    if 'personel_listesi' not in st.session_state:
        st.session_state.personel_listesi = pd.DataFrame(columns=["Ad Soyad", "TC Kimlik", "Departman"])
    if 'icra_listesi' not in st.session_state:
        st.session_state.icra_listesi = pd.DataFrame(columns=["Dosya No", "Borçlu Adı", "Tutar"])

def display_tabs():
    # Buraya sekmelerin içeriğini fonksiyon olarak yazın
    pass