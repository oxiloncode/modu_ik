import streamlit as st
import pandas as pd
import sqlite3
import hashlib

# -----------------------------------------------------
# 1. GÖRSEL VE ARAYÜZ FONKSİYONLARI 
# -----------------------------------------------------

# Sayfayı ortalayan ve sabitleyen çerçeve yapısı
def page_wrapper():
    # Sayfayı 3'e böl, ortadaki kısımları ana içerik alanı yap
    left_spacer, main_content, right_spacer = st.columns([1, 4, 1])
    return main_content

def init_session():
    # Tablo verileri
    if 'personel_listesi' not in st.session_state:
        st.session_state.personel_listesi = pd.DataFrame(columns=["Ad Soyad", "TC Kimlik", "Departman"])
    if 'icra_listesi' not in st.session_state:
        st.session_state.icra_listesi = pd.DataFrame(columns=["Dosya No", "Borçlu Adı", "Tutar"])
        
    # Giriş ve Yetkilendirme durumları (Yeni Eklenen Kısım)
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'role' not in st.session_state:
        st.session_state.role = None

def display_tabs():
    pass

# -----------------------------------------------------
# 2. GÜVENLİK VE ŞİFRELEME FONKSİYONLARI 
# -----------------------------------------------------

def make_hashes(password):
    """Girilen şifreyi SHA-256 algoritması ile kriptolar."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    """Kullanıcının girdiği şifre ile veritabanındaki kriptolu şifreyi karşılaştırır."""
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# -----------------------------------------------------
# 3. VERİTABANI VE KULLANICI YÖNETİMİ 
# -----------------------------------------------------

def init_users_db():
    """SQLite veritabanını ve kullanıcılar tablosunu oluşturur.
    Eğer sistemde hiç kullanıcı yoksa varsayılan Yönetici hesabını ekler."""
    
    # personel_sistemi.db adında bir dosya oluşturur (veya varsa bağlanır)
    conn = sqlite3.connect('personel_sistemi.db')
    c = conn.cursor()
    
    # Kullanıcılar tablosunu oluştur
    c.execute('''CREATE TABLE IF NOT EXISTS kullanicilar
                 (kullanici_adi TEXT PRIMARY KEY, sifre TEXT, rol TEXT)''')
    
    # Tabloda hiç kayıt var mı diye kontrol et
    c.execute('SELECT * FROM kullanicilar')
    if not c.fetchall():
        # Sistem boşsa ilk Kurucu/Yönetici hesabını oluştur
        varsayilan_kullanici = "admin"
        varsayilan_sifre = make_hashes("123456") # Şifre: 123456 olarak kriptolanır
        varsayilan_rol = "Yönetici"
        
        c.execute('INSERT INTO kullanicilar (kullanici_adi, sifre, rol) VALUES (?, ?, ?)', 
                  (varsayilan_kullanici, varsayilan_sifre, varsayilan_rol))
    
    conn.commit()
    conn.close()

def login_user(kullanici_adi, sifre):
    """Giriş ekranında bilgileri doğrular. Başarılıysa kullanıcının rolünü döndürür."""
    conn = sqlite3.connect('personel_sistemi.db')
    c = conn.cursor()
    
    # Veritabanından kullanıcıyı bul
    c.execute('SELECT sifre, rol FROM kullanicilar WHERE kullanici_adi = ?', (kullanici_adi,))
    data = c.fetchone()
    conn.close()
    
    if data:
        hashed_sifre = data[0]
        rol = data[1]
        
        # Şifreler eşleşiyorsa rolü sisteme bildir
        if check_hashes(sifre, hashed_sifre):
            return rol
            
    # Kullanıcı yoksa veya şifre yanlışsa False döndür
    return False
