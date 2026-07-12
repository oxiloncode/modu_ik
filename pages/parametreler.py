import streamlit as st
import pandas as pd
import sqlite3
import os
import math

# Sayfa Ayarları
st.set_page_config(layout="wide")

DB_PATH = "modu_ik/personel_sistemi.db"

# --- MAVİ KURUMSAL TASARIM CSS ---
st.markdown("""
    <style>
    label {
        color: #2E86C1 !important; 
        font-weight: 600 !important;
    }
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-testid="stFileUploader"] {
        border: 1px solid #2E86C1 !important;
        border-radius: 8px !important;
        background-color: #f0f7ff !important;
        padding: 5px;
    }
    input {
        background-color: transparent !important;
    }
    .sayfa-bilgi {
        text-align: center;
        font-weight: bold;
        color: #555;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- VERİTABANI İNŞA VE SÜTUN KONTROLLERİ ---
def init_parametre_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS meslek_kodlari (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        kod TEXT UNIQUE,
                        tanim TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS cikis_kodlari (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        kod TEXT UNIQUE,
                        tanim TEXT)''')
    
    cursor.execute("PRAGMA table_info(personel)")
    sutunlar = [row[1] for row in cursor.fetchall()]
    if 'meslek_kodu' not in sutunlar:
        cursor.execute("ALTER TABLE personel ADD COLUMN meslek_kodu TEXT")
        
    conn.commit()
    conn.close()

init_parametre_db()

# --- SQL YARDIMCI FONKSİYONLARI ---
def veri_ekle(tablo, kod, tanim):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f"INSERT OR REPLACE INTO {tablo} (kod, tanim) VALUES (?, ?)", (kod, tanim))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def veri_sil(tablo, row_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {tablo} WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()

def verileri_listele(tablo):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(f"SELECT id, kod, tanim FROM {tablo} ORDER BY kod ASC", conn)
    conn.close()
    return df

# Sayfa yapısını ortalayan çerçeve
def page_wrapper():
    left_spacer, main_content, right_spacer = st.columns([1, 4, 1])
    return main_content

# --- SAYFALANDIRMA (PAGINATION) MANTIĞI ---
if 'page_m' not in st.session_state: st.session_state.page_m = 1
if 'page_c' not in st.session_state: st.session_state.page_c = 1
KAYIT_LIMITI = 50

content = page_wrapper()

with content:
    st.title("⚙️ İK Sistem Parametreleri")
    
    col_m, col_s = st.columns([1, 4])
    with col_m:
        if st.button("🏠 Ana Menü", use_container_width=True):
            st.switch_page("0_Ana_Menu.py")
    with col_s:
        if st.button("👥 Personel Listesine Dön", use_container_width=True):
            st.switch_page("pages/1_Personel_Sicil_Kartlari.py")
            
    st.write("---")
    
    p_tab1, p_tab2 = st.tabs(["📋 SGK Meslek Kodları", "🚪 SGK Çıkış Kodları"])
    
    # --- 1. SEKME: MESLEK KODLARI YÖNETİMİ ---
    with p_tab1:
        st.subheader("Excel ile Toplu Meslek Kodu Yükle")
        excel_meslek = st.file_uploader("Meslek Kodları Excel Dosyasını Seç (.xlsx veya .xls)", type=["xlsx", "xls"], key="excel_m")
        
        if excel_meslek is not None:
            try:
                df_excel_m = pd.read_excel(excel_meslek)
                df_excel_m.columns = [str(c).strip().lower() for c in df_excel_m.columns]
                
                if 'kod' in df_excel_m.columns and 'tanım' in df_excel_m.columns:
                    if st.button("🚀 Excel Verilerini Veritabanına Aktar", key="btn_excel_m", type="primary"):
                        basarili_sayisi = 0
                        for idx, row in df_excel_m.iterrows():
                            kod_val = str(row['kod']).strip()
                            tanim_val = str(row['tanım']).strip()
                            if kod_val and tanim_val and kod_val != "nan" and tanim_val != "nan":
                                if veri_ekle("meslek_kodlari", kod_val, tanim_val):
                                    basarili_sayisi += 1
                        st.success(f"🎉 Excel'deki **{basarili_sayisi}** adet meslek kodu başarıyla sisteme yüklendi!")
                        st.session_state.page_m = 1 # Yükleme sonrası ilk sayfaya dön
                        st.rerun()
                else:
                    st.error("Excel dosyasında 'Kod' ve 'Tanım' adında iki sütun bulunmalıdır. Lütfen kontrol edin.")
            except Exception as e:
                st.error(f"Excel okunurken bir hata oluştu: {e}")
                
        st.write("---")
        st.subheader("Mevcut Kayıtlı Meslek Kodları")
        
        meslek_df = verileri_listele("meslek_kodlari")
        toplam_meslek = len(meslek_df)
        
        if toplam_meslek == 0:
            st.info("Sistemde henüz kayıtlı meslek kodu bulunmuyor.")
        else:
            toplam_sayfa_m = math.ceil(toplam_meslek / KAYIT_LIMITI)
            if st.session_state.page_m > toplam_sayfa_m: st.session_state.page_m = toplam_sayfa_m
            
            # --- Üst Sayfalandırma Kontrolü ---
            pg_col1, pg_col2, pg_col3 = st.columns([1, 2, 1])
            with pg_col1:
                if st.button("⬅️ Önceki", key="prev_m_top", disabled=(st.session_state.page_m == 1), use_container_width=True):
                    st.session_state.page_m -= 1
                    st.rerun()
            with pg_col2:
                st.markdown(f"<div class='sayfa-bilgi'>Sayfa {st.session_state.page_m} / {toplam_sayfa_m} <br> (Toplam {toplam_meslek} Kayıt)</div>", unsafe_allow_html=True)
            with pg_col3:
                if st.button("Sonraki ➡️", key="next_m_top", disabled=(st.session_state.page_m == toplam_sayfa_m), use_container_width=True):
                    st.session_state.page_m += 1
                    st.rerun()
            
            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
            
            # --- Verileri Dilimleyerek Gösterme ---
            baslangic_idx = (st.session_state.page_m - 1) * KAYIT_LIMITI
            bitis_idx = baslangic_idx + KAYIT_LIMITI
            gosterilecek_df_m = meslek_df.iloc[baslangic_idx:bitis_idx]
            
            for idx, row in gosterilecek_df_m.iterrows():
                row_col1, row_col2, row_col3 = st.columns([1, 2.5, 0.5])
                row_col1.write(f"**{row['kod']}**")
                row_col2.write(row['tanim'])
                if row_col3.button("🗑️", key=f"sil_m_{row['id']}", help="Bu kodu sil"):
                    veri_sil("meslek_kodlari", row['id'])
                    # Silme işlemi sonrası liste boşalırsa bir önceki sayfaya geçiş yap
                    guncel_toplam = toplam_meslek - 1
                    yeni_toplam_sayfa = math.ceil(guncel_toplam / KAYIT_LIMITI)
                    if st.session_state.page_m > yeni_toplam_sayfa and yeni_toplam_sayfa > 0:
                        st.session_state.page_m = yeni_toplam_sayfa
                    st.rerun()
                st.markdown("<div style='border-bottom: 1px dashed #eee; margin: 3px 0;'></div>", unsafe_allow_html=True)

    # --- 2. SEKME: ÇIKIŞ KODLARI YÖNETİMİ ---
    with p_tab2:
        st.subheader("Excel ile Toplu Çıkış Kodu Yükle")
        excel_cikis = st.file_uploader("Çıkış Kodları Excel Dosyasını Seç (.xlsx veya .xls)", type=["xlsx", "xls"], key="excel_c")
        
        if excel_cikis is not None:
            try:
                df_excel_c = pd.read_excel(excel_cikis)
                df_excel_c.columns = [str(c).strip().lower() for c in df_excel_c.columns]
                
                if 'kod' in df_excel_c.columns and 'tanım' in df_excel_c.columns:
                    if st.button("🚀 Excel Verilerini Veritabanına Aktar", key="btn_excel_c", type="primary"):
                        basarili_sayisi = 0
                        for idx, row in df_excel_c.iterrows():
                            kod_val = str(row['kod']).strip()
                            tanim_val = str(row['tanım']).strip()
                            if kod_val and tanim_val and kod_val != "nan" and tanim_val != "nan":
                                if veri_ekle("cikis_kodlari", kod_val, tanim_val):
                                    basarili_sayisi += 1
                        st.success(f"🎉 Excel'deki **{basarili_sayisi}** adet çıkış kodu başarıyla sisteme yüklendi!")
                        st.session_state.page_c = 1
                        st.rerun()
                else:
                    st.error("Excel dosyasında 'Kod' ve 'Tanım' adında iki sütun bulunmalıdır. Lütfen kontrol edin.")
            except Exception as e:
                st.error(f"Excel okunurken bir hata oluştu: {e}")
                
        st.write("---")
        st.subheader("Mevcut Kayıtlı Çıkış Kodları")
        
        cikis_df = verileri_listele("cikis_kodlari")
        toplam_cikis = len(cikis_df)
        
        if toplam_cikis == 0:
            st.info("Sistemde henüz kayıtlı çıkış kodu bulunmuyor.")
        else:
            toplam_sayfa_c = math.ceil(toplam_cikis / KAYIT_LIMITI)
            if st.session_state.page_c > toplam_sayfa_c: st.session_state.page_c = toplam_sayfa_c
            
            # --- Üst Sayfalandırma Kontrolü ---
            pgc_col1, pgc_col2, pgc_col3 = st.columns([1, 2, 1])
            with pgc_col1:
                if st.button("⬅️ Önceki", key="prev_c_top", disabled=(st.session_state.page_c == 1), use_container_width=True):
                    st.session_state.page_c -= 1
                    st.rerun()
            with pgc_col2:
                st.markdown(f"<div class='sayfa-bilgi'>Sayfa {st.session_state.page_c} / {toplam_sayfa_c} <br> (Toplam {toplam_cikis} Kayıt)</div>", unsafe_allow_html=True)
            with pgc_col3:
                if st.button("Sonraki ➡️", key="next_c_top", disabled=(st.session_state.page_c == toplam_sayfa_c), use_container_width=True):
                    st.session_state.page_c += 1
                    st.rerun()
            
            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
            
            baslangic_idx = (st.session_state.page_c - 1) * KAYIT_LIMITI
            bitis_idx = baslangic_idx + KAYIT_LIMITI
            gosterilecek_df_c = cikis_df.iloc[baslangic_idx:bitis_idx]
            
            for idx, row in gosterilecek_df_c.iterrows():
                row_col1, row_col2, row_col3 = st.columns([1, 2.5, 0.5])
                row_col1.write(f"**{row['kod']}**")
                row_col2.write(row['tanim'])
                if row_col3.button("🗑️", key=f"sil_c_{row['id']}", help="Bu kodu sil"):
                    veri_sil("cikis_kodlari", row['id'])
                    guncel_toplam = toplam_cikis - 1
                    yeni_toplam_sayfa = math.ceil(guncel_toplam / KAYIT_LIMITI)
                    if st.session_state.page_c > yeni_toplam_sayfa and yeni_toplam_sayfa > 0:
                        st.session_state.page_c = yeni_toplam_sayfa
                    st.rerun()
                st.markdown("<div style='border-bottom: 1px dashed #eee; margin: 3px 0;'></div>", unsafe_allow_html=True)