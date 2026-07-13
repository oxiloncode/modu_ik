import sqlite3
import hashlib
import os
import streamlit as st

DB_PATH = "modu_ik/personel_sistemi.db"

# Şifreleri SHA-256 ile şifreleyen fonksiyon (Geri döndürülemez güvenlik)
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# Girilen şifre ile veritabanındaki şifrelenmiş kaydı karşılaştıran fonksiyon
def check_hashes(password, hashed_password):
    if make_hashes(password) == hashed_password:
        return True
    return False

# Kullanıcılar tablosunu ve ilk varsayılan kullanıcıyı oluşturan fonksiyon
def init_users_db():
    if not os.path.exists("modu_ik"): 
        os.makedirs("modu_ik")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Kullanıcılar tablosunu oluştur (Eğer yoksa)
    cursor.execute('''CREATE TABLE IF NOT EXISTS kullanicilar (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        kullanici_adi TEXT UNIQUE,
                        sifre TEXT,
                        rol TEXT)''')
    
    # Eğer veritabanında hiç kullanıcı yoksa varsayılan admin (Yönetici) hesabını yarat
    cursor.execute("SELECT * FROM kullanicilar")
    if not cursor.fetchone():
        hashed_pw = make_hashes("admin123")  # Varsayılan şifre: admin123
        cursor.execute("INSERT INTO kullanicilar (kullanici_adi, sifre, rol) VALUES (?, ?, ?)", 
                       ("admin", hashed_pw, "Yönetici"))
        conn.commit()
        
    conn.close()

# Kullanıcı giriş denemesini kontrol eden fonksiyon
def login_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT sifre, rol FROM kullanicilar WHERE kullanici_adi = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        hashed_password, rol = result
        if check_hashes(password, hashed_password):
            return {"kullanici_adi": username, "rol": rol}
    return None

# Oturum durumlarını başlatan fonksiyon
def init_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "role" not in st.session_state:
        st.session_state.role = ""
