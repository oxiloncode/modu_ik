import streamlit as st
import pandas as pd
import sqlite3

from utils import init_session
init_session()
if not st.session_state.logged_in:
    st.warning("⚠️ Lütfen önce Ana Menü'den giriş yapın!")
    st.stop()

# Sayfa ayarları
st.set_page_config(layout="wide")
DB_PATH = "modu_ik/personel_sistemi.db"

# --- VERİTABANI GÜNCELLEMESİ (Çıkış Tarihi sütununu otomatik ekler) ---
def veritabani_kontrol_ve_guncelle():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(personel)")
        sutunlar = [row[1] for row in cursor.fetchall()]
        if 'cikis_tarihi' not in sutunlar:
            cursor.execute("ALTER TABLE personel ADD COLUMN cikis_tarihi TEXT")
        conn.commit()
        conn.close()
    except Exception as e:
        pass

veritabani_kontrol_ve_guncelle()

# Sayfayı ortalayan ve sabitleyen çerçeve yapısı
def page_wrapper():
    left_spacer, main_content, right_spacer = st.columns([1, 4, 1])
    return main_content

content = page_wrapper()

with content:
    st.title("👥 Personel Sicil Kartları")
    
    # --- ÜST BUTONLAR ---
    col_menu, col_ekle = st.columns([1, 4])
    with col_menu:
        if st.button("🏠 Ana Menü", use_container_width=True):
            st.switch_page("0_Ana_Menu.py") 
    with col_ekle:
        if st.button("➕ Yeni Personel Ekle", use_container_width=True):
            st.switch_page("pages/z_Yeni_Kayit.py")

    st.write("---")
    
    # --- ARAMA KUTULARI (Durum Filtresi + TC + Ad Soyad) ---
    st.markdown("### 🔍 Personel Ara")
    col_durum, col_ara1, col_ara2 = st.columns([1, 2, 2])
    with col_durum:
        durum_filtre = st.selectbox("Durum Filtresi", options=["Tümü", "Aktif", "Pasif"])
    with col_ara1:
        tc_ara = st.text_input("TC Kimlik ile Ara (Enter'a bas)", placeholder="Örn: 12345678901")
    with col_ara2:
        ad_ara = st.text_input("Ad Soyad ile Ara (Enter'a bas)", placeholder="Örn: Ahmet Yılmaz")

    st.divider()

    # --- VERİYİ ÇEKME ---
    try:
        conn = sqlite3.connect(DB_PATH)
        # Giriş ve Çıkış tarihlerini de SQL'den çekiyoruz
        df = pd.read_sql_query("SELECT tc_kimlik, ad_soyad, bolum, sirket, ise_giris, cikis_tarihi FROM personel", conn)
        conn.close()
    except Exception as e:
        df = pd.DataFrame() 

    if not df.empty:
        # --- DURUM SÜTUNUNU HESAPLA (Aktif / Pasif) ---
        def durum_hesapla(cikis_tarihi):
            cikis_var_mi = pd.notna(cikis_tarihi) and str(cikis_tarihi).strip() != "" and str(cikis_tarihi).strip() != "None"
            return "Pasif" if cikis_var_mi else "Aktif"

        df['durum'] = df['cikis_tarihi'].apply(durum_hesapla)

        # --- FİLTRELEME MANTIĞI ---
        if durum_filtre != "Tümü":
            df = df[df['durum'] == durum_filtre]
        if tc_ara:
            df = df[df['tc_kimlik'].astype(str).str.contains(tc_ara, case=False, na=False)]
        if ad_ara:
            df = df[df['ad_soyad'].astype(str).str.contains(ad_ara, case=False, na=False)]

        # --- LİSTELEME VE KART TASARIMI ---
        if df.empty:
            st.warning("Aradığınız kriterlere uygun personel bulunamadı.")
        else:
            st.success(f"Sistemde kriterlere uygun **{len(df)}** personel listeleniyor.")
            
            # Tablo Başlıkları (6 Sütuna ayırdık - Durum eklendi)
            st.markdown("---")
            c1, c2, c3, c4, c5, c6 = st.columns([1.5, 2.5, 2, 2.5, 1, 1.5])
            c1.write("**TC Kimlik**")
            c2.write("**Ad Soyad**")
            c3.write("**Bölüm / Şirket**")
            c4.write("**Giriş & Çıkış Tarihi**")
            c5.write("**Durum**")
            c6.write("**İşlem**")
            st.markdown("---")
            
            # Personel Döngüsü
            for index, row in df.iterrows():
                # Çıkış tarihi var mı kontrolü
                cikis_var_mi = row['durum'] == "Pasif"
                
                # Her satırı özel bir çerçeve (kutu) içine alıyoruz
                with st.container(border=True):
                    col1, col2, col3, col4, col5, col6 = st.columns([1.5, 2.5, 2, 2.5, 1, 1.5])
                    
                    # Eğer personel işten çıkmışsa (cikis_var_mi = True) metinler KIRMIZI olacak
                    if cikis_var_mi:
                        col1.markdown(f"<span style='color:#ff4b4b; font-weight:bold;'>{row['tc_kimlik']}</span>", unsafe_allow_html=True)
                        col2.markdown(f"<span style='color:#ff4b4b; font-weight:bold;'>{row['ad_soyad']}</span>", unsafe_allow_html=True)
                        col3.markdown(f"<span style='color:#ff4b4b;'>{row['bolum']}<br>{row['sirket']}</span>", unsafe_allow_html=True)
                        col4.markdown(f"<span style='color:#ff4b4b;'><b>Giriş:</b> {row['ise_giris']}<br><b>Çıkış:</b> {row['cikis_tarihi']}</span>", unsafe_allow_html=True)
                        col5.markdown("<span style='color:#ff4b4b; font-weight:bold;'>🔴 Pasif</span>", unsafe_allow_html=True)
                    
                    # Eğer çalışmaya devam ediyorsa normal görünecek
                    else:
                        g_tarih = row['ise_giris'] if pd.notna(row['ise_giris']) else "-"
                        
                        col1.write(str(row['tc_kimlik']))
                        col2.write(str(row['ad_soyad']))
                        col3.markdown(f"{row['bolum']}<br>{row['sirket']}", unsafe_allow_html=True)
                        col4.markdown(f"<b>Giriş:</b> {g_tarih}<br><b>Çıkış:</b> -", unsafe_allow_html=True)
                        col5.markdown("<span style='color:#21c354; font-weight:bold;'>🟢 Aktif</span>", unsafe_allow_html=True)
                    
                    # Detay Butonu
                    with col6:
                        # Butonu dikeyde ortalamak için küçük bir boşluk
                        st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
                        if st.button("👁️ Detay", key=f"detay_{row['tc_kimlik']}", use_container_width=True):
                            st.session_state.secili_tc = row['tc_kimlik']
                            st.switch_page("pages/personel_detay.py")
    else:
        st.info("Sistemde henüz kayıtlı personel bulunmamaktadır. Lütfen yeni kayıt oluşturun.")
