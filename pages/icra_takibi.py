import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import math
import locale

# Türkçe ay isimleri için (sunucuda hata vermemesi adına try-except içinde)
try:
    locale.setlocale(locale.LC_TIME, 'tr_TR.UTF-8')
except:
    pass

st.set_page_config(layout="wide", page_title="İcra Takip Ekranı")

DB_PATH = "modu_ik/personel_sistemi.db"

# --- TASARIM (CSS) ---
st.markdown("""
    <style>
    label { color: #2E86C1 !important; font-weight: 600 !important; }
    div[data-baseweb="input"], div[data-baseweb="datepicker"], div[data-baseweb="select"] {
        border: 1px solid #2E86C1 !important; border-radius: 8px !important; background-color: #f0f7ff !important;
    }
    input { background-color: transparent !important; }
    .kutu-baslik { font-size: 16px; font-weight: bold; color: #333; margin-bottom: 10px; text-align: center; border-bottom: 1px solid #ccc; padding-bottom: 5px; }
    .bilgi-satiri { margin-bottom: 5px; font-size: 14px; }
    
    /* Logo için CSS */
    .logo-container { display: flex; justify-content: center; margin-bottom: 20px; margin-top: 10px; }
    .logo-box { border: 2px solid #333; padding: 10px 30px; border-radius: 10px; background-color: #f8f9fa; font-size: 24px; font-weight: bold; color: #333; }
    </style>
""", unsafe_allow_html=True)

# --- VERİTABANI GÜNCELLEMESİ ---
def init_icra_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(personel)")
    sutunlar = [row[1] for row in cursor.fetchall()]
    if 'maas' not in sutunlar:
        cursor.execute("ALTER TABLE personel ADD COLUMN maas REAL DEFAULT 0")
        
    cursor.execute('''CREATE TABLE IF NOT EXISTS icra_dosyalari (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tc_kimlik TEXT, turu TEXT, dosya_no TEXT, sira_no INTEGER,
                        islem_tarihi TEXT, dosya_tarihi TEXT, icra_mudurlugu TEXT,
                        banka_adi TEXT, hesap_no TEXT, alacakli_adi TEXT, alacakli_iban TEXT,
                        aciklama TEXT, dosya_tutari REAL, taksit_tutari REAL, taksit_sayisi INTEGER,
                        durum TEXT DEFAULT 'AKTİF')''')
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS icra_taksitleri (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dosya_id INTEGER, bordro_donemi TEXT, taksit_tutari REAL,
                        kesilen_tutar REAL DEFAULT 0, kalan_tutar REAL)''')
    conn.commit()
    conn.close()

init_icra_db()

# --- VERİ ÇEKME VE GÜNCELLEME FONKSİYONLARI ---
def personelleri_getir():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT tc_kimlik, ad_soyad, bolum, ise_giris, maas FROM personel WHERE cikis_yapildi_mi != '1' OR cikis_yapildi_mi IS NULL", conn)
    conn.close()
    return df

def icra_dosyalarini_getir(tc_kimlik):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM icra_dosyalari WHERE tc_kimlik = ? ORDER BY sira_no ASC", conn, params=(tc_kimlik,))
    conn.close()
    return df

def taksitleri_getir(dosya_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM icra_taksitleri WHERE dosya_id = ? ORDER BY id ASC", conn, params=(int(dosya_id),))
    conn.close()
    # Satır açılışında kalan tutarı tablodaki verilere göre otomatik eşitle
    df['kalan_tutar'] = df['taksit_tutari'] - df['kesilen_tutar']
    return df

def taksit_tablosunu_guncelle(df):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for _, row in df.iterrows():
        # Veritabanına yazarken "Kalan Tutar" o ayın hesaplaması olarak güncellenir
        hesaplanan_kalan = float(row['taksit_tutari']) - float(row['kesilen_tutar'])
        cursor.execute('''UPDATE icra_taksitleri 
                          SET bordro_donemi=?, taksit_tutari=?, kesilen_tutar=?, kalan_tutar=? 
                          WHERE id=?''', 
                       (row['bordro_donemi'], row['taksit_tutari'], row['kesilen_tutar'], hesaplanan_kalan, row['id']))
    conn.commit()
    conn.close()

def page_wrapper():
    left, main, right = st.columns([0.5, 5, 0.5])
    return main

content = page_wrapper()

with content:
    # --- LOGO VE BAŞLIK ALANI (ANA MENÜ BUTONLU) ---
    col_baslik, col_btn = st.columns([6, 1])
    with col_baslik:
        st.markdown("""
            <div class="logo-container">
                <div class="logo-box">Modu İK</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<h3 style='text-align:center;'>⚖️ İCRA KAYDI OLUŞTURMA VE TAKİP EKRANI</h3>", unsafe_allow_html=True)
    with col_btn:
        st.write("") 
        st.write("") 
        if st.button("🏠 Ana Menüye Dön", use_container_width=True):
            st.switch_page("0_Ana_Menu.py")

    st.write("---")
    
    p_df = personelleri_getir()
    p_liste = ["Seçiniz..."] + [f"{row['tc_kimlik']} - {row['ad_soyad']}" for _, row in p_df.iterrows()]
    
    if 'secili_icra_tc' not in st.session_state: st.session_state.secili_icra_tc = None
    if 'secili_dosya_id' not in st.session_state: st.session_state.secili_dosya_id = None

    # --- ÜST FORM ALANI ---
    with st.container(border=True):
        col_form, col_butonlar = st.columns([4, 1])
        
        with col_form:
            f1, f2, f3 = st.columns(3)
            with f1:
                turu = st.selectbox("Türü", ["İcra", "Nafaka", "Haciz", "Diğer"])
                islem_tarihi = st.date_input("İşlem Tarihi")
                icra_mudurlugu = st.text_input("İcra Müdürlüğü")
                alacakli_adi = st.text_input("Alacaklı Adı")
            with f2:
                dosya_no = st.text_input("Dosya No")
                dosya_tarihi = st.date_input("Dosya Tarihi")
                banka_adi = st.text_input("Banka Adı")
                alacakli_iban = st.text_input("Alacaklı IBAN")
            with f3:
                sira_no = st.number_input("Sıra No", min_value=1, step=1)
                hesap_no = st.text_input("Hesap No")
                aciklama = st.text_input("Açıklama")
                
            st.markdown("---")
            t1, t2, t3 = st.columns(3)
            with t1:
                dosya_tutari = st.number_input("Dosya Tutarı (TL)", min_value=0.0, step=100.0)
            with t2:
                aylik_taksit = st.number_input("Aylık Taksit Tutarı (TL)", min_value=0.0, step=100.0)
            with t3:
                hesaplanan_taksit = math.ceil(dosya_tutari / aylik_taksit) if aylik_taksit > 0 else 0
                st.info(f"**Taksit Sayısı:** {hesaplanan_taksit} Taksit")

        with col_butonlar:
            st.markdown("<br>", unsafe_allow_html=True)
            secilen_personel = st.selectbox("PERSONEL SEÇ", p_liste)
            if secilen_personel != "Seçiniz...":
                st.session_state.secili_icra_tc = secilen_personel.split(" - ")[0]
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("DOSYAYI TAKSİTLENDİR", use_container_width=True, type="primary"):
                if st.session_state.secili_icra_tc and dosya_tutari > 0 and aylik_taksit > 0:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute('''INSERT INTO icra_dosyalari 
                                      (tc_kimlik, turu, dosya_no, sira_no, islem_tarihi, dosya_tarihi, 
                                      icra_mudurlugu, banka_adi, hesap_no, alacakli_adi, alacakli_iban, 
                                      aciklama, dosya_tutari, taksit_tutari, taksit_sayisi) 
                                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                                   (st.session_state.secili_icra_tc, turu, dosya_no, sira_no, str(islem_tarihi),
                                    str(dosya_tarihi), icra_mudurlugu, banka_adi, hesap_no, alacakli_adi,
                                    alacakli_iban, aciklama, dosya_tutari, aylik_taksit, hesaplanan_taksit))
                    yeni_dosya_id = cursor.lastrowid
                    
                    kalan_ana_para = dosya_tutari
                    for i in range(hesaplanan_taksit):
                        donem_tarih = islem_tarihi + relativedelta(months=i)
                        bordro_donemi = f"{donem_tarih.strftime('%B')} {donem_tarih.year}"
                        kesilecek = aylik_taksit if kalan_ana_para >= aylik_taksit else kalan_ana_para
                        kalan_ana_para -= kesilecek
                        
                        # Kalan Tutar: İlk etapta hiç kesinti girilmediği için o ayki taksit tutarına eşittir.
                        kalan_tutar_aylik = kesilecek 
                        
                        cursor.execute('''INSERT INTO icra_taksitleri (dosya_id, bordro_donemi, taksit_tutari, kesilen_tutar, kalan_tutar) 
                                          VALUES (?, ?, ?, ?, ?)''', (yeni_dosya_id, bordro_donemi, kesilecek, 0, kalan_tutar_aylik))
                    conn.commit()
                    conn.close()
                    st.success("İcra dosyası ve taksitleri başarıyla oluşturuldu!")
                    st.rerun()
                else:
                    st.warning("Lütfen bir personel seçin ve tutarları eksiksiz girin.")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("DOSYAYI KAPAT", use_container_width=True):
                if st.session_state.secili_dosya_id:
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("UPDATE icra_dosyalari SET durum='KAPALI' WHERE id=?", (st.session_state.secili_dosya_id,))
                    conn.commit()
                    conn.close()
                    st.success("İcra dosyası kapalı duruma getirildi!")
                    st.rerun()
                else:
                    st.warning("Kapatmak için önce aşağıdan bir dosya seçmelisiniz.")

    st.write("---")
    
    # --- ALT DETAY ALANI ---
    if st.session_state.secili_icra_tc:
        secili_p_data = p_df[p_df['tc_kimlik'] == st.session_state.secili_icra_tc].iloc[0]
        dosyalar_df = icra_dosyalarini_getir(st.session_state.secili_icra_tc)
        
        alt_sol, alt_sag = st.columns([1.5, 3.5])
        
        with alt_sol:
            with st.container(border=True):
                st.markdown("<div class='kutu-baslik'>PERSONEL BİLGİLERİ</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='bilgi-satiri'><b>Ad Soyad:</b> {secili_p_data['ad_soyad']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='bilgi-satiri'><b>TC Kimlik:</b> {secili_p_data['tc_kimlik']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='bilgi-satiri'><b>Bölüm:</b> {secili_p_data['bolum']}</div>", unsafe_allow_html=True)
                
                giris_str = str(secili_p_data['ise_giris'])
                try:
                    formatli_giris = datetime.strptime(giris_str, "%Y-%m-%d").strftime("%d/%m/%Y")
                except:
                    formatli_giris = giris_str
                st.markdown(f"<div class='bilgi-satiri'><b>İşe Giriş:</b> {formatli_giris}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='bilgi-satiri'><b>Maaş Bilgisi:</b> ₺{secili_p_data['maas']:,.2f}</div>", unsafe_allow_html=True)
            
            with st.container(border=True):
                st.markdown("<div class='kutu-baslik'>İCRA DOSYALARI</div>", unsafe_allow_html=True)
                if dosyalar_df.empty:
                    st.info("Kayıtlı icra dosyası yok.")
                else:
                    for _, d_row in dosyalar_df.iterrows():
                        # Kapalı olanları kırmızı daire ile işaretliyoruz
                        durum_etiketi = f"🔴 (KAPALI)" if d_row['durum'] == "KAPALI" else "(AKTİF)"
                        
                        if st.button(f"{d_row['sira_no']}.SIRADA - {d_row['dosya_no']} {durum_etiketi}", key=f"btn_dosya_{d_row['id']}", use_container_width=True):
                            st.session_state.secili_dosya_id = d_row['id']
                            st.rerun()

        with alt_sag:
            with st.container(border=True):
                if st.session_state.secili_dosya_id:
                    aktif_dosya = dosyalar_df[dosyalar_df['id'] == st.session_state.secili_dosya_id].iloc[0]
                    st.markdown(f"<div style='text-align:center; font-weight:bold; font-size:18px; margin-bottom:5px;'>{aktif_dosya['dosya_no']} Nolu Dosya Detayı</div>", unsafe_allow_html=True)
                    st.caption("Aşağıdaki tabloda Kesilen Tutar hücrelerine çift tıklayarak Excel gibi düzenleme yapabilirsiniz. (Kaydettiğinizde 'Kalan Tutar' otomatik hesaplanacaktır)")
                    
                    taksit_df = taksitleri_getir(st.session_state.secili_dosya_id)
                    
                    # --- EXCEL GİBİ DÜZENLENEBİLİR TABLO ---
                    edited_df = st.data_editor(
                        taksit_df,
                        column_config={
                            "id": None, 
                            "dosya_id": None,
                            "bordro_donemi": "Bordro Dönemi",
                            "taksit_tutari": st.column_config.NumberColumn("Taksit Tutarı", format="%.2f"),
                            "kesilen_tutar": st.column_config.NumberColumn("Kesilen Tutar", format="%.2f"),
                            "kalan_tutar": st.column_config.NumberColumn("Kalan Tutar (Aylık)", format="%.2f", disabled=True)
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # --- BUTONLAR ALANI: KAYDET VE SİL ---
                    st.markdown("<br>", unsafe_allow_html=True)
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("💾 Tablodaki Değişiklikleri Kaydet", use_container_width=True):
                            taksit_tablosunu_guncelle(edited_df)
                            st.success("Taksitler başarıyla güncellendi!")
                            st.rerun()
                    with btn_col2:
                        if st.button("🗑️ Dosyayı Sil", use_container_width=True, type="primary"):
                            conn = sqlite3.connect(DB_PATH)
                            conn.execute("DELETE FROM icra_dosyalari WHERE id=?", (st.session_state.secili_dosya_id,))
                            conn.execute("DELETE FROM icra_taksitleri WHERE dosya_id=?", (st.session_state.secili_dosya_id,))
                            conn.commit()
                            conn.close()
                            st.session_state.secili_dosya_id = None
                            st.success("İcra dosyası ve taksitleri kalıcı olarak silindi!")
                            st.rerun()
                    
                    # Alt Toplamlar
                    toplam_kesilen = edited_df['kesilen_tutar'].sum()
                    toplam_kalan_genel = aktif_dosya['dosya_tutari'] - toplam_kesilen
                    
                    st.markdown("---")
                    d1, d2, d3 = st.columns(3)
                    d1.metric("TOPLAM DOSYA TUTARI", f"₺{aktif_dosya['dosya_tutari']:,.2f}")
                    d2.metric("TOPLAM KESİLEN", f"₺{toplam_kesilen:,.2f}")
                    d3.metric("TOPLAM KALAN TUTAR", f"₺{toplam_kalan_genel:,.2f}")
                else:
                    st.info("Detaylarını görmek için sol taraftan bir icra dosyası seçiniz.")