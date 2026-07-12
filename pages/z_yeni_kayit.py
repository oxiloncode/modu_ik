import streamlit as st
import pandas as pd
import base64
from datetime import date
from dateutil.relativedelta import relativedelta
import sqlite3
import os

# Sayfa ayarları hata vermemesi için ilk komut olmalı
st.set_page_config(layout="wide")

# Veritabanı ve fotoğraf klasör yolu
DB_PATH = "modu_ik/personel_sistemi.db"
FOTO_DIR = "modu_ik/fotograflar"

if not os.path.exists(FOTO_DIR):
    os.makedirs(FOTO_DIR)

# --- VERİTABANINDAN MESLEK KODLARINI ÇEKME ---
def meslek_kodlarini_getir():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT kod, tanim FROM meslek_kodlari ORDER BY kod ASC", conn)
        conn.close()
        if df.empty:
            return ["Parametrelerden meslek kodu ekleyiniz!"]
        return [f"{row['kod']} - {row['tanim']}" for idx, row in df.iterrows()]
    except Exception:
        return ["Veritabanı hatası!"]

def init_db():
    if not os.path.exists("modu_ik"): os.makedirs("modu_ik")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Personel tablosu
    cursor.execute('''CREATE TABLE IF NOT EXISTS personel (
                        tc_kimlik TEXT PRIMARY KEY, ad_soyad TEXT, bolum TEXT, 
                        ise_giris TEXT, dogum_tarihi TEXT, dogum_yeri TEXT, 
                        baba_adi TEXT, anne_adi TEXT, telefon TEXT, mail TEXT, 
                        adres TEXT, askerlik TEXT, medeni_durum TEXT, mezuniyet TEXT,
                        sirket TEXT, fiili_birim TEXT, iban TEXT, banka TEXT,
                        yillik_izin_baz TEXT, sgk_giris TEXT, banka_sube_kodu TEXT, banka_sube_adi TEXT)''')
    
    # Maaş sütunlarının kontrolü ve eklenmesi
    cursor.execute("PRAGMA table_info(personel)")
    sutunlar = [row[1] for row in cursor.fetchall()]
    if 'maas' not in sutunlar:
        cursor.execute("ALTER TABLE personel ADD COLUMN maas REAL DEFAULT 0")
    if 'maas_tipi' not in sutunlar:
        cursor.execute("ALTER TABLE personel ADD COLUMN maas_tipi TEXT DEFAULT 'Net'")
        
    # İzinler tablosu
    cursor.execute('''CREATE TABLE IF NOT EXISTS izinler (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, tc_kimlik TEXT, 
                        tur TEXT, baslangic TEXT, bitis TEXT, gun INTEGER, aciklama TEXT)''')
    
    # Evraklar tablosu (Güncel 15 Sütun)
    cursor.execute('''CREATE TABLE IF NOT EXISTS evraklar (
                        tc_kimlik TEXT PRIMARY KEY,
                        evrak1_onay INTEGER, evrak1_tarih TEXT,
                        evrak2_onay INTEGER, evrak2_tarih TEXT,
                        evrak3_onay INTEGER, evrak3_tarih TEXT,
                        evrak4_onay INTEGER, evrak4_tarih TEXT,
                        evrak5_onay INTEGER, evrak5_tarih TEXT,
                        evrak6_onay INTEGER, evrak6_tarih TEXT,
                        evrak7_onay INTEGER, evrak7_tarih TEXT)''')
    
    conn.commit()
    conn.close()

# --- AKILLI SQL KAYIT FONKSİYONLARI ---
def personel_kaydet_veya_guncelle(data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    sutunlar = ", ".join(data.keys())
    soru_isaretleri = ", ".join(["?"] * len(data))
    degerler = tuple(data.values())
    
    cursor.execute(f"INSERT OR REPLACE INTO personel ({sutunlar}) VALUES ({soru_isaretleri})", degerler)
    conn.commit()
    conn.close()

def evrak_kaydet_veya_guncelle(tc, e_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''INSERT OR REPLACE INTO evraklar VALUES 
                      (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', 
                   (tc, 
                    int(e_data.get('evrak1_onay', 0)), str(e_data.get('evrak1_tarih', '')),
                    int(e_data.get('evrak2_onay', 0)), str(e_data.get('evrak2_tarih', '')),
                    int(e_data.get('evrak3_onay', 0)), str(e_data.get('evrak3_tarih', '')),
                    int(e_data.get('evrak4_onay', 0)), str(e_data.get('evrak4_tarih', '')),
                    int(e_data.get('evrak5_onay', 0)), str(e_data.get('evrak5_tarih', '')),
                    int(e_data.get('evrak6_onay', 0)), str(e_data.get('evrak6_tarih', '')),
                    int(e_data.get('evrak7_onay', 0)), str(e_data.get('evrak7_tarih', ''))))
    conn.commit()
    conn.close()

init_db()

BUGUN = date.today() 
MIN_TARIH = date(1950, 1, 1)

st.markdown("""
    <style>
    .foto-cerceve {
        width: 200px; 
        height: 300px; 
        border: 2px solid #ccc;
        border-radius: 10px; 
        display: flex; 
        align-items: center;
        justify-content: center; 
        margin-bottom: 10px; 
        background-color: #f9f9f9; 
        overflow: hidden;
    }
    label { 
        color: #2E86C1 !important; 
        font-weight: 600 !important; 
    }
    div[data-baseweb="input"], div[data-baseweb="datepicker"], div[data-baseweb="select"] {
        border: 1px solid #2E86C1 !important; 
        border-radius: 8px !important; 
        background-color: #f0f7ff !important;
    }
    input { 
        background-color: transparent !important; 
    }
    .evrak-container { 
        display: flex; 
        align-items: center; 
        gap: 20px; 
    }
    </style>
""", unsafe_allow_html=True)

def page_wrapper():
    left_spacer, main_content, right_spacer = st.columns([1, 4, 1])
    return main_content

content = page_wrapper()

with content:
    st.title("")

# --- SESSION STATE BAŞLATMA ---
if 'personel_listesi' not in st.session_state: 
    st.session_state.personel_listesi = pd.DataFrame(columns=["Ad Soyad", "TC Kimlik", "Departman"])
    
if "ise_giris_key" not in st.session_state: 
    st.session_state.ise_giris_key = date.today()
    
if "yillik_izin_baz_key" not in st.session_state: 
    st.session_state.yillik_izin_baz_key = date.today()
    
if "sgk_giris_key" not in st.session_state: 
    st.session_state.sgk_giris_key = date.today()
    
if "dogum_tarihi_key" not in st.session_state: 
    st.session_state.dogum_tarihi_key = date.today()

st.title("➕ Yeni Personel Kaydı")

col_geri, col_izin = st.columns([1, 1])
with col_geri:
    if st.button("⬅️ Geri Dön"):
        st.switch_page("pages/1_Personel_Sicil_Kartlari.py")
with col_izin:
    st.caption("💡 İzin kayıtlarını ve bakiye takibini artık **İzin Takibi** sayfasından yönetebilirsiniz.")

# SADECE 3 SEKME VAR
tab1, tab2, tab3 = st.tabs(["Personel Bilgileri", "Şirket Bilgileri", "Evrak Kontrolü"])

with tab1:
    st.markdown("##### Personel Fotoğrafı")
    foto = st.file_uploader("Fotoğraf Seç", type=['jpg', 'png', 'jpeg'])

    with st.container(border=True): 
        if foto is not None:
            st.image(foto, width=200) 
        else:
            st.markdown("""
                <div style="height: 250px; display: flex; align-items: center; justify-content: center; color: #ccc;">
                    Fotoğraf Yok
                </div>
            """, unsafe_allow_html=True)

    st.markdown("##### Kıdem Durumu")
    giris = st.session_state.ise_giris_key
    bugun = date.today()
    fark = relativedelta(bugun, giris)
    toplam_gun = (bugun - giris).days
    kidem_metni = f"{fark.years} Yıl {fark.months} Ay {fark.days} Gün ({toplam_gun} Gün)"
    
    with st.container(border=True):
        st.markdown(f"**Toplam Kıdem:** {kidem_metni}")

    st.markdown("##### Personel Bilgileri")
    st.markdown("""<div style="margin-top: -10px; margin-bottom: 10px; border-bottom: 1px solid #000000; width: 150px;"></div>""", unsafe_allow_html=True)
    
    ad_soyad = st.text_input("Ad Soyad")
    tc_no = st.text_input("TC Kimlik No",max_chars=11)
    
    st.date_input("Doğum Tarihi", value=st.session_state.dogum_tarihi_key, format="DD/MM/YYYY", key="dogum_tarihi_key", min_value=MIN_TARIH)
    
    dogum_yeri = st.text_input("Doğum Yeri")
    baba_adi = st.text_input("Baba Adı")
    anne_adi = st.text_input("Anne Adı")
    telefon_numarasi = st.text_input("Telefon Numarası")
    mail_adresi = st.text_input("Mail Adresi")
    adres = st.text_input("Adres")
    askerlik = st.selectbox("Askerlik Durumu",["Yaptı","Muaf","Tecili","Görev Dışı"])
    medeni_durum = st.selectbox("Medeni Durum",["Evli","Bekar"])
    mezuniyet = st.selectbox("Mezuniyet Durumu",["İlkokul","Ortaokul","Lise","Önlisans","Lisans","Yüksek Lisans","Doktora"])

with tab2:
    st.markdown("##### Şirket Bilgileri")
    st.date_input("İşe Giriş Tarihi", value=st.session_state.ise_giris_key, format="DD/MM/YYYY", key="ise_giris_key", min_value=MIN_TARIH)
    st.date_input("Yıllık İzin Baz Tarihi", value=st.session_state.yillik_izin_baz_key, format="DD/MM/YYYY", key="yillik_izin_baz_key", min_value=MIN_TARIH)
    st.date_input("SGK Giriş Tarihi", value=st.session_state.sgk_giris_key, format="DD/MM/YYYY", key="sgk_giris_key", min_value=MIN_TARIH)
    
    st.markdown("""<div style="margin-top: -10px; margin-bottom: 10px; border-bottom: 1px solid #000000; width: 150px;"></div>""", unsafe_allow_html=True)
    sirket = st.selectbox("Şirket",["Altamira Merkez","Altamira Scalla","Altamira Bonomade"])
    fiili_birim = st.selectbox("Fiili Çalışma Birimi",["MERKEZ","SCALLA","BONOMADE"])
    bolum = st.selectbox("Bölüm", ["İnsan Kaynakları", "Muhasebe", "Mutfak","Salon","Bar","Mimar"])
    
    meslek_listesi = meslek_kodlarini_getir()
    y_meslek_kodu = st.selectbox("SGK Meslek Kodu", meslek_listesi)

    st.markdown("##### Maaş Bilgileri")
    st.markdown("""<div style="margin-top: -10px; margin-bottom: 10px; border-bottom: 1px solid #000000; width: 150px;"></div>""", unsafe_allow_html=True)
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        maas_tutari = st.number_input("Maaş Tutarı (TL)", min_value=0.0, step=1000.0, format="%.2f")
    with col_m2:
        maas_tipi = st.selectbox("Maaş Türü", ["Net", "Brüt"])

    st.markdown("##### Ödeme Bilgileri")
    st.markdown("""<div style="margin-top: -10px; margin-bottom: 10px; border-bottom: 1px solid #000000; width: 150px;"></div>""", unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        iban_bilgisi = st.text_input("IBAN", placeholder="TR000000000000000000000000", max_chars=26)
    with col4 :
        banka = st.text_input("Banka")
    col1, col2 = st.columns(2)
    with col1:
        banka_sube_kodu = st.text_input("Şube Kodu")
    with col2:
        banka_sube_adi = st.text_input("Banka Şube Adı")

with tab3:
    st.markdown("##### Özlük Evrakları Kontrol Listesi")
    st.markdown("""<div style="margin-top: -10px; margin-bottom: 20px; border-bottom: 1px solid #000000; width: 250px;"></div>""", unsafe_allow_html=True)

    with st.container(border=True):
        st.info("💡 Lütfen teslim alınan evrakları işaretleyip tarihlerini giriniz.")
        
        c_sol, c_sag = st.columns([1, 1])
        
        with c_sol:
            st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
            onay1 = st.checkbox("1. Nüfus Cüzdan Fotokopisi", key="evrak1_onay")
            st.markdown("<hr style='margin: 17px 0; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
            
            onay2 = st.checkbox("2. 2 Adet Fotoğraf", key="evrak2_onay")
            st.markdown("<hr style='margin: 17px 0; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
            
            onay3 = st.checkbox("3. Nüfus Kayıt Örneği", key="evrak3_onay")
            st.markdown("<hr style='margin: 17px 0; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
            
            onay4 = st.checkbox("4. İkametgah", key="evrak4_onay")
            st.markdown("<hr style='margin: 17px 0; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
            
            onay5 = st.checkbox("5. Diploma Fotokopisi", key="evrak5_onay")
            st.markdown("<hr style='margin: 17px 0; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
            
            onay6 = st.checkbox("6. Adli Sicil Kaydı", key="evrak6_onay")
            st.markdown("<hr style='margin: 5px 0; border-top: 1px dashed #transparent;'>", unsafe_allow_html=True)

        with c_sag:
            tarih1 = st.date_input("Teslim Tarihi 1", format="DD/MM/YYYY", key="evrak1_tarih", label_visibility="collapsed")
            st.markdown("<hr style='margin: 9px 0; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
            
            tarih2 = st.date_input("Teslim Tarihi 2", format="DD/MM/YYYY", key="evrak2_tarih", label_visibility="collapsed")
            st.markdown("<hr style='margin: 9px 0; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
            
            tarih3 = st.date_input("Teslim Tarihi 3", format="DD/MM/YYYY", key="evrak3_tarih", label_visibility="collapsed")
            st.markdown("<hr style='margin: 9px 0; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
            
            tarih4 = st.date_input("Teslim Tarihi 4", format="DD/MM/YYYY", key="evrak4_tarih", label_visibility="collapsed")
            st.markdown("<hr style='margin: 9px 0; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
            
            tarih5 = st.date_input("Teslim Tarihi 5", format="DD/MM/YYYY", key="evrak5_tarih", label_visibility="collapsed")
            st.markdown("<hr style='margin: 9px 0; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
            
            tarih6 = st.date_input("Teslim Tarihi 6", format="DD/MM/YYYY", key="evrak6_tarih", label_visibility="collapsed")
            st.markdown("<hr style='margin: 5px 0; border-top: 1px dashed #transparent;'>", unsafe_allow_html=True)

# Formu tek bir yerde topla
if st.button("Kaydı Tamamla", type="primary"):
    if not tc_no:
        st.error("TC Kimlik No boş bırakılamaz!")
    else:
        if foto is not None:
            foto_yolu = os.path.join(FOTO_DIR, f"{tc_no}.png")
            with open(foto_yolu, "wb") as f:
                f.write(foto.getbuffer())

        veri_paketi = {
            "tc_kimlik": tc_no, 
            "ad_soyad": ad_soyad, 
            "bolum": bolum,
            "ise_giris": str(st.session_state.ise_giris_key), 
            "dogum_tarihi": str(st.session_state.dogum_tarihi_key), 
            "dogum_yeri": dogum_yeri, 
            "baba_adi": baba_adi, 
            "anne_adi": anne_adi,
            "telefon": telefon_numarasi, 
            "mail": mail_adresi, 
            "adres": adres,
            "askerlik": askerlik, 
            "medeni_durum": medeni_durum, 
            "mezuniyet": mezuniyet,
            "sirket": sirket, 
            "fiili_birim": fiili_birim, 
            "iban": iban_bilgisi, 
            "banka": banka,
            "yillik_izin_baz": str(st.session_state.yillik_izin_baz_key),
            "sgk_giris": str(st.session_state.sgk_giris_key),
            "banka_sube_kodu": banka_sube_kodu, 
            "banka_sube_adi": banka_sube_adi,
            "meslek_kodu": y_meslek_kodu, 
            "maas": maas_tutari, 
            "maas_tipi": maas_tipi
        }
        
        evrak_paketi = {
            "evrak1_onay": 1 if onay1 else 0, 
            "evrak1_tarih": str(tarih1),
            "evrak2_onay": 1 if onay2 else 0, 
            "evrak2_tarih": str(tarih2),
            "evrak3_onay": 1 if onay3 else 0, 
            "evrak3_tarih": str(tarih3),
            "evrak4_onay": 1 if onay4 else 0, 
            "evrak4_tarih": str(tarih4),
            "evrak5_onay": 1 if onay5 else 0, 
            "evrak5_tarih": str(tarih5),
            "evrak6_onay": 1 if onay6 else 0, 
            "evrak6_tarih": str(tarih6),
            "evrak7_onay": 0, 
            "evrak7_tarih": ""
        }
        
        personel_kaydet_veya_guncelle(veri_paketi)
        evrak_kaydet_veya_guncelle(tc_no, evrak_paketi)
        st.success(f"🎉 {ad_soyad} başarıyla tüm detaylarıyla ve fotoğrafıyla kaydedildi!")