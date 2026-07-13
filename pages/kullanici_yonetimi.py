import streamlit as st
import sqlite3
import pandas as pd
from utils import init_session, make_hashes

# Güvenlik Kontrolü: Sadece yöneticiler girebilir
init_session()
if not st.session_state.logged_in or st.session_state.role != "Yönetici":
    st.error("⚠️ Bu sayfayı görüntüleme yetkiniz yok!")
    st.stop()

st.title("🔐 Kullanıcı ve Yetki Yönetimi")
st.write("Sisteme yeni kullanıcılar ekleyebilir ve mevcut kullanıcıların yetkilerini görebilirsiniz.")

DB_PATH = "modu_ik/personel_sistemi.db"

col1, col2 = st.columns([1, 1])

with col1:
    # Yeni Kullanıcı Ekleme Formu
    st.subheader("Yeni Kullanıcı Ekle")
    with st.form("yeni_kullanici_formu", clear_on_submit=True):
        yeni_kullanici = st.text_input("Kullanıcı Adı")
        yeni_sifre = st.text_input("Şifre", type="password")
        rol = st.selectbox("Sistem Rolü", ["Yönetici", "Kayıt Uzmanı", "İzleyici"])
        submit = st.form_submit_button("Kullanıcıyı Sisteme Kaydet")

        if submit:
            if yeni_kullanici and yeni_sifre:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                try:
                    hashed_pw = make_hashes(yeni_sifre)
                    cursor.execute("INSERT INTO kullanicilar (kullanici_adi, sifre, rol) VALUES (?, ?, ?)", 
                                   (yeni_kullanici, hashed_pw, rol))
                    conn.commit()
                    st.success(f"✅ '{yeni_kullanici}' başarıyla eklendi!")
                except sqlite3.IntegrityError:
                    st.error("❌ Bu kullanıcı adı zaten sistemde mevcut, lütfen başka bir ad seçin.")
                finally:
                    conn.close()
            else:
                st.warning("Lütfen kullanıcı adı ve şifre alanlarını boş bırakmayın.")

with col2:
    # Mevcut Kullanıcıları Göster (Şifreler hariç)
    st.subheader("Sistemdeki Kullanıcılar")
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT id, kullanici_adi as 'Kullanıcı Adı', rol as 'Sistem Yetkisi' FROM kullanicilar", conn)
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error("Kullanıcılar listelenirken bir hata oluştu.")
    finally:
        conn.close()

st.write("---")
if st.button("⬅️ Ana Menüye Dön"):
    st.switch_page("0_Ana_Menu.py")
