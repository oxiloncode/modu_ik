import streamlit as st
from utils import init_session

# Sayfa ayarları - Streamlit kuralı gereği en üstte ve tek bir yerde olmalıdır
st.set_page_config(page_title="Modu İK - Ana Menü", page_icon="https://i.hizliresim.com/19ai6mx.png", layout="wide")

# Sayfayı ortalayan ve sabitleyen çerçeve yapısı
def page_wrapper():
    left_spacer, main_content, right_spacer = st.columns([1, 4, 1])
    return main_content

content = page_wrapper()

# DÜZENLENMİŞ CSS (Buton ezilmelerini engelleyen yapı)
st.markdown("""
    <style>
    .stTextInput {
        max-width: 500px;
    }
    
    /* Butonlardaki sabit 300px sınırını kaldırdık. 
       Metinlerin alt satıra inmesine izin verip yüksekliği artırdık. */
    div.stButton > button {
        height: 65px;
        font-size: 16px !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        white-space: normal !important; 
        word-wrap: break-word;
        transition: all 0.3s ease;
    }
    
    /* Fareyle üzerine gelince şık bir havaya kalkma efekti */
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Ana uygulama arka planı */
    .stApp {
        background-color: #ffffff !important;
    }
    
    /* Yan menü (eğer görünürse) arka planı */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
    }

    /* Sağ üst köşedeki Geliştirici LinkedIn Butonu */
    .linkedin-dev-btn {
        position: fixed;
        top: 55px;
        right: 25px;
        z-index: 999;
        display: flex;
        align-items: center;
        gap: 8px;
        background-color: #0A66C2;
        color: #ffffff !important;
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        text-decoration: none !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        transition: all 0.2s ease;
    }
    .linkedin-dev-btn:hover {
        background-color: #084d94;
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        color: #ffffff !important;
    }
    .linkedin-dev-btn svg {
        width: 18px;
        height: 18px;
        fill: #ffffff;
    }
    </style>

    <a href="https://www.linkedin.com/in/onuroturak/" target="_blank" class="linkedin-dev-btn">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512">
            <path d="M100.28 448H7.4V148.9h92.88zm-46.44-340a53.6 53.6 0 1 1 53.6-53.6 53.61 53.61 0 0 1-53.6 53.6zM447.9 448h-92.68V302.4c0-34.7-.7-79.3-48.3-79.3-48.3 0-55.7 37.7-55.7 76.7V448h-92.8V148.9h89.1v40.8h1.3c12.4-23.5 42.7-48.3 87.9-48.3 94 0 111.3 61.9 111.3 142.3V448z"/>
        </svg>
        Geliştirici LinkedIn Hesabı
    </a>
""", unsafe_allow_html=True)

with content:
    st.title("")

    # 1. Logo Bölümü
    st.markdown("""
        <style>
        .logo-container { display: flex; justify-content: center; margin-bottom: 30px; }
        .logo-box { 
            border: 2px solid #333; 
            padding: 15px 40px; 
            border-radius: 10px; 
            background-color: #f8f9fa;
            font-size: 28px; 
            font-weight: bold; 
            color: #333;
        }
        </style>
        <div class="logo-container">
            <div class="logo-box">Modu İK</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='text-align: center;'>Personel Yönetim Sistemi</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Hoş geldiniz, lütfen bir işlem seçin:</p>", unsafe_allow_html=True)
    st.write("---")

    # --- 1. SATIR (3 Buton) ---
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("👤 Personel Sicil Kartlari", use_container_width=True):
            st.switch_page("pages/1_Personel_Sicil_Kartlari.py")

    with col2:
        if st.button("🗓️ İzin Takibi", use_container_width=True):
            st.switch_page("pages/izin_takibi.py")

    with col3:
        if st.button("⚖️ İcra Takibi", use_container_width=True):
            st.switch_page("pages/icra_takibi.py")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 2. SATIR (2 Butonu Ortalamak İçin Boşluklu Yapı) ---
    bos_sol, col4, col5, bos_sag = st.columns([0.5, 1, 1, 0.5])

    with col4:
        if st.button("⚙️ Parametre Yönetimi", use_container_width=True):
            st.switch_page("pages/parametreler.py")

    with col5:
        # Rapor Hazırlama ekranına yönlendirme (Aktif edildi)
        if st.button("📊 Rapor Hazırlama Ekranı", use_container_width=True):
            st.switch_page("pages/rapor_hazirlama_ekrani.py")

    st.write("---")