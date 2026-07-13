import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO

from utils import init_session
init_session()
if not st.session_state.logged_in:
    st.warning("⚠️ Lütfen önce Ana Menü'den giriş yapın!")
    st.stop()

st.set_page_config(layout="wide", page_title="Modu İK - Raporlama")

DB_PATH = "modu_ik/personel_sistemi.db"


# --- VERİTABANI GÜVENCESİ: İcra tabloları hiçbir yerde oluşturulmuyordu,
#     bu da sayfanın "no such table" hatasıyla çökmesine sebep oluyordu. ---
def veritabani_kontrol_ve_guncelle():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS icra_dosyalari (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tc_kimlik TEXT,
                        dosya_no TEXT,
                        turu TEXT,
                        alacakli_adi TEXT,
                        dosya_tutari REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS icra_taksitleri (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dosya_id INTEGER,
                        bordro_donemi TEXT,
                        kesilen_tutar REAL,
                        kalan_tutar REAL)''')
    conn.commit()
    conn.close()

veritabani_kontrol_ve_guncelle()


# --- VERİ ÇEKME (artık hata durumunda sayfayı çökertmiyor) ---
def get_data(query):
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Veri okunurken bir hata oluştu: {e}")
        return pd.DataFrame()


# --- EXCEL DÖNÜŞTÜRME ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Rapor')
    return output.getvalue()


def indirme_butonu(df, dosya_adi, label):
    """Boş tabloda indirme butonunu devre dışı bırakır, kullanıcıyı boş dosya indirmekten korur."""
    if df.empty:
        st.info("Bu kritere uygun gösterilecek veri bulunmuyor.")
    else:
        st.download_button(
            label, to_excel(df), dosya_adi,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


st.title("📊 Rapor Hazırlama Ekranı")
st.write("---")

# Filtreleme Paneli
col1, col2 = st.columns(2)
with col1:
    durum_f = st.selectbox("Personel Durumu", ["Tümü", "Aktif", "Pasif"])
with col2:
    sirket_f = st.selectbox("Şirket", ["Tümü", "Altamira Merkez", "Altamira Scalla", "Altamira Bonomade"])

tab1, tab2, tab3 = st.tabs(["👤 Personel Listesi", "🗓️ İzin Raporu", "⚖️ İcra Raporu"])

# 1. PERSONEL RAPORU
with tab1:
    df_p = get_data("SELECT * FROM personel")

    if not df_p.empty:
        # --- DURUM HESABI: Personel Sicil Kartları sayfasıyla AYNI kritere göre
        #     (cikis_tarihi) hesaplanıyor, aksi halde iki ekran birbiriyle çelişebilir. ---
        def durum_hesapla(cikis_tarihi):
            cikis_var_mi = pd.notna(cikis_tarihi) and str(cikis_tarihi).strip() not in ("", "None")
            return "Pasif" if cikis_var_mi else "Aktif"

        if 'cikis_tarihi' in df_p.columns:
            df_p['Durum'] = df_p['cikis_tarihi'].apply(durum_hesapla)
        else:
            df_p['Durum'] = "Aktif"

        if durum_f != "Tümü":
            df_p = df_p[df_p['Durum'] == durum_f]

        if sirket_f != "Tümü" and 'sirket' in df_p.columns:
            df_p = df_p[df_p['sirket'] == sirket_f]

    st.dataframe(df_p, use_container_width=True)
    indirme_butonu(df_p, "personel_listesi.xlsx", "📥 Personel Listesini İndir (XLSX)")

# 2. İZİN RAPORU
with tab2:
    df_i = get_data('''
        SELECT p.ad_soyad, p.sirket, i.*
        FROM izinler i
        JOIN personel p ON i.tc_kimlik = p.tc_kimlik
    ''')

    if not df_i.empty and sirket_f != "Tümü" and 'sirket' in df_i.columns:
        df_i = df_i[df_i['sirket'] == sirket_f]

    st.dataframe(df_i, use_container_width=True)
    indirme_butonu(df_i, "izin_raporu.xlsx", "📥 İzin Raporunu İndir (XLSX)")

# 3. İCRA RAPORU
with tab3:
    # LEFT JOIN kullanıldı: henüz hiç taksit kaydı girilmemiş icra dosyaları da
    # (INNER JOIN'de olduğu gibi sessizce kaybolmadan) raporda görünür.
    df_c = get_data('''
        SELECT p.ad_soyad, p.sirket, d.dosya_no, d.turu, d.alacakli_adi, d.dosya_tutari,
               t.bordro_donemi, t.kesilen_tutar, t.kalan_tutar
        FROM icra_dosyalari d
        JOIN personel p ON d.tc_kimlik = p.tc_kimlik
        LEFT JOIN icra_taksitleri t ON d.id = t.dosya_id
    ''')

    if not df_c.empty and sirket_f != "Tümü" and 'sirket' in df_c.columns:
        df_c = df_c[df_c['sirket'] == sirket_f]

    st.dataframe(df_c, use_container_width=True)
    indirme_butonu(df_c, "icra_raporu.xlsx", "📥 İcra Raporunu İndir (XLSX)")

st.write("---")
if st.button("🏠 Ana Menüye Dön"):
    st.switch_page("0_Ana_Menu.py")
