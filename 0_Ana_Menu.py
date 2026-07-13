import streamlit as st
from utils import init_session, init_users_db, login_user

# Sayfa ayarları - Streamlit kuralı gereği en üstte olmalıdır
st.set_page_config(page_title="Modu İK - Ana Menü", page_icon="https://i.hizliresim.com/19ai6mx.png", layout="wide")

# Oturumu ve Kullanıcı tablosunu başlat
init_session()
init_users_db()

# Sayfayı ortalayan çerçeve yapısı
def page_wrapper():
    left_spacer, main_content, right_spacer = st.columns([1, 4, 1])
    return main_content

content = page_wrapper()

# DÜZENLENMİŞ CSS
st.markdown("""
    <style>
    .stTextInput {
        max-width: 500px;
    }
    div.stButton > button {
        height: 65px;
        font-size: 16px !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        white-space: normal !important; 
        word-wrap: break-word;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .stApp {
        background-color: #ffffff !important;
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
    }
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
    # Logo Alanı
    st.markdown("""
        <style>
        .logo-container { display: flex; justify-content: center; margin-bottom: 20px; margin-top: 40px; }
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
    st.write("---")

    # KULLANICI GİRİŞ KONTROLÜ
    if not st.session_state.logged_in:
        st.markdown("<h3 style='text-align: center; color: #333;'>Sistem Girişi</h3>", unsafe_allow_html=True)
        
        # Giriş panelini ortalayan kolon düzeni
        col_sol, col_orta, col_sag = st.columns([1, 1.5, 1])
        with col_orta:
            kullanici_adi = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı adınızı girin")
            sifre = st.text_input("Şifre", type="password", placeholder="Şifrenizi girin")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🔑 Giriş Yap", use_container_width=True):
                user_info = login_user(kullanici_adi, sifre)
                if user_info:
                    st.session_state.logged_in = True
                    st.session_state.username = user_info["kullanici_adi"]
                    st.session_state.role = user_info["rol"]
                    st.success("Giriş Başarılı! Sisteme yönlendiriliyorsunuz...")
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre hatalı!")
                    
    else:
        # Oturum açık ise ana menü arayüzü gösterilir
        st.markdown(f"<p style='text-align: center;'>Hoş geldiniz, <b>{st.session_state.username} ({st.session_state.role})</b></p>", unsafe_allow_html=True)
        
        # Oturumu kapat butonu
        c_sol, c_orta, c_sag = st.columns([2, 1, 2])
        with c_orta:
            if st.button("🚪 Oturumu Kapat", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.session_state.role = ""
                st.rerun()
                
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

        # --- 2. SATIR (2 Buton) ---
        bos_sol, col4, col5, bos_sag = st.columns([0.5, 1, 1, 0.5])

        with col4:
            if st.button("⚙️ Parametre Yönetimi", use_container_width=True):
                st.switch_page("pages/parametreler.py")

        with col5:
            if st.button("📊 Rapor Hazırlama Ekranı", use_container_width=True):
                st.switch_page("pages/rapor_hazirlama_ekrani.py")

        st.write("---")

# Sadece Yöneticilere Özel Alan
        if st.session_state.role == "Yönetici":
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔐 Sistem ve Kullanıcı Yönetimi", use_container_width=True):
                st.switch_page("pages/kullanici_yonetimi.py")
            st.write("---")
