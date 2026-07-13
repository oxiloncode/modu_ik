import streamlit as st
import sqlite3
import pandas as pd
from utils import init_session, make_hashes

# Güvenlik Kontrolü: Sadece yöneticiler girebilir
init_session()
if not st.session_state.logged_in or st.session_state.role != "Yönetici":
    st.error("⚠️ Bu sayfayı görüntüleme yetkiniz yok!")
    st.stop()

# Sayfa ayarları
st.set_page_config(page_title="Kullanıcı Yönetimi", layout="wide")

st.title("🔐 Kullanıcı ve Yetki Yönetimi")
st.write("Sisteme yeni kullanıcılar ekleyebilir, mevcut şifreleri güncelleyebilir veya kullanıcıları silebilirsiniz.")

DB_PATH = "modu_ik/personel_sistemi.db"

# Veritabanından kullanıcıları taze çekmek için yardımcı fonksiyon
def kullanicilari_getir():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT id, kullanici_adi as 'Kullanıcı Adı', rol as 'Sistem Yetkisi' FROM kullanicilar", conn)
    conn.close()
    return df

# Sayfayı 3 Sekmeye (Tab) ayırıyoruz
tab1, tab2, tab3 = st.tabs(["👥 Kullanıcı Listesi", "➕ Yeni Kullanıcı Ekle", "⚙️ Şifre Değiştir / Sil"])

# --- 1. SEKME: KULLANICI LİSTESİ ---
with tab1:
    st.subheader("Sistemdeki Aktif Kullanıcılar")
    df_users = kullanicilari_getir()
    if not df_users.empty:
        st.dataframe(df_users, use_container_width=True, hide_index=True)
    else:
        st.info("Sistemde kayıtlı kullanıcı bulunamadı.")

# --- 2. SEKME: YENİ KULLANICI EKLE ---
with tab2:
    col_bos1, col_form, col_bos2 = st.columns([1, 2, 1])
    with col_form:
        st.subheader("Yeni Kullanıcı Ekle")
        with st.form("yeni_kullanici_formu", clear_on_submit=True):
            yeni_kullanici = st.text_input("Kullanıcı Adı")
            yeni_sifre = st.text_input("Şifre", type="password")
            rol = st.selectbox("Sistem Rolü", ["Yönetici", "Kayıt Uzmanı", "İzleyici"])
            submit_add = st.form_submit_button("Kullanıcıyı Sisteme Kaydet")

            if submit_add:
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

# --- 3. SEKME: ŞİFRE DEĞİŞTİRME VE SİLME ---
with tab3:
    st.subheader("Kullanıcı İşlemleri")
    df_users = kullanicilari_getir()
    kullanici_listesi = df_users['Kullanıcı Adı'].tolist()
    
    if kullanici_listesi:
        # Hangi kullanıcı üzerinde işlem yapılacağını seç
        secilen_kullanici = st.selectbox("İşlem Yapılacak Kullanıcıyı Seçin", kullanici_listesi)
        
        st.write("---")
        col_sifre, col_sil = st.columns(2)
        
        # Şifre Değiştirme Bölümü
        with col_sifre:
            st.markdown("#### 🔑 Şifre Değiştir")
            with st.form("sifre_degistir_formu", clear_on_submit=True):
                yeni_sifre_input = st.text_input("Yeni Şifre", type="password")
                yeni_sifre_tekrar = st.text_input("Yeni Şifre (Tekrar)", type="password")
                submit_pass = st.form_submit_button("Şifreyi Güncelle")
                
                if submit_pass:
                    if yeni_sifre_input == yeni_sifre_tekrar and len(yeni_sifre_input) > 0:
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        hashed_pw = make_hashes(yeni_sifre_input)
                        cursor.execute("UPDATE kullanicilar SET sifre = ? WHERE kullanici_adi = ?", (hashed_pw, secilen_kullanici))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ {secilen_kullanici} kullanıcısının şifresi başarıyla güncellendi.")
                    else:
                        st.error("Şifreler eşleşmiyor veya boş bırakıldı!")
        
        # Kullanıcı Silme Bölümü
        with col_sil:
            st.markdown("#### 🗑️ Kullanıcıyı Sil")
            st.warning("Bu işlem geri alınamaz ve kullanıcının sisteme erişimi derhal kesilir!")
            
            # Admin hesabının silinmesini güvenlik amacıyla kilitliyoruz
            if secilen_kullanici == "admin":
                st.error("⚠️ 'admin' (Ana Yönetici) hesabı sistemden silinemez!")
            else:
                if st.button(f"'{secilen_kullanici}' Kullanıcısını Sil"):
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM kullanicilar WHERE kullanici_adi = ?", (secilen_kullanici,))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ {secilen_kullanici} kullanıcısı sistemden kalıcı olarak silindi.")
                    st.rerun() # Ekranı yenile ki silinen listeden çıksın
    else:
        st.info("Sistemde işlem yapılacak kullanıcı bulunamadı.")

st.write("---")
col_back, col_bos = st.columns([1, 5])
with col_back:
    if st.button("⬅️ Ana Menüye Dön", use_container_width=True):
        st.switch_page("0_Ana_Menu.py")
