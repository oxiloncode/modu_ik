import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os

# Sayfa Ayarları (Hata vermemesi için en üstte ve tek bir yerde)
st.set_page_config(layout="wide")

# --- TARİH SINIRLARI (Tüm date_input alanları için ortak 100 yıllık aralık) ---
MIN_TARIH = datetime.today().date() - relativedelta(years=100)
MAX_TARIH = datetime.today().date() + relativedelta(years=100)

# --- CSS TASARIMLARI (Mavi Kurumsal Tema Yapısı) ---
st.markdown("""
    <style>
    /* Tüm giriş bileşenlerinin etiket (label) rengi */
    label {
        color: #2E86C1 !important; 
        font-weight: 600 !important;
    }
    /* text_input, number_input, date_input ve selectbox kutularının stili */
    div[data-baseweb="input"], div[data-baseweb="datepicker"], div[data-baseweb="select"], div[data-baseweb="base-input"] {
        border: 1px solid #2E86C1 !important;
        border-radius: 8px !important;
        background-color: #f0f7ff !important;
    }
    /* Giriş alanlarının iç arka plan temizliği */
    input {
        background-color: transparent !important;
    }
    </style>
""", unsafe_allow_html=True)

DB_PATH = "modu_ik/personel_sistemi.db"
FOTO_DIR = "modu_ik/fotograflar"

if not os.path.exists(FOTO_DIR):
    os.makedirs(FOTO_DIR)

# --- VERİTABANI GÜNCELLEYİCİ VE PARAMETRE FONKSİYONLARI ---
def veritabani_kontrol_ve_guncelle():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(personel)")
    p_sutunlar = [row[1] for row in cursor.fetchall()]
    
    # Maaş ve Maaş Tipi sütunları da dinamik kontrol listesine eklendi
    yeni_p_sutunlar = [
        'yillik_izin_baz', 'sgk_giris', 'banka_sube_kodu', 'banka_sube_adi', 'cikis_tarihi',
        'is_arama_izni_gun', 'fiili_cikis_tarihi', 'cikis_evrak_istifa', 'cikis_evrak_onay',
        'cikis_evrak_teblig', 'cikis_evrak_ibraname', 'cikis_evrak_bordro', 'cikis_evrak_mutabakat',
        'cikis_aciklama', 'cikis_kodu', 'ihbar_baslatildi_mi', 'ihbar_islem_tarihi',
        'cikis_yapildi_mi', 'cikis_islem_tarihi', 'ihbar_sure_baslangici', 'meslek_kodu',
        'maas', 'maas_tipi'
    ]
    
    for sutun in yeni_p_sutunlar:
        if sutun not in p_sutunlar:
            if sutun == 'maas':
                cursor.execute(f"ALTER TABLE personel ADD COLUMN {sutun} REAL DEFAULT 0")
            elif sutun == 'maas_tipi':
                cursor.execute(f"ALTER TABLE personel ADD COLUMN {sutun} TEXT DEFAULT 'Net'")
            else:
                cursor.execute(f"ALTER TABLE personel ADD COLUMN {sutun} TEXT")
            
    cursor.execute("PRAGMA table_info(evraklar)")
    e_sutunlar = [row[1] for row in cursor.fetchall()]
    if 'evrak7_onay' not in e_sutunlar:
        cursor.execute("ALTER TABLE evraklar ADD COLUMN evrak7_onay INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE evraklar ADD COLUMN evrak7_tarih TEXT")
        
    conn.commit()
    conn.close()

veritabani_kontrol_ve_guncelle()

# --- PARAMETRELERİ DİNAMİK GETİRME FONKSİYONLARI ---
def dinamik_meslek_kodlari_getir():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT kod, tanim FROM meslek_kodlari ORDER BY kod ASC", conn)
        conn.close()
        if df.empty:
            return [""]
        return [f"{row['kod']} - {row['tanim']}" for idx, row in df.iterrows()]
    except Exception:
        return [""]

def dinamik_cikis_kodlari_getir():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT kod, tanim FROM cikis_kodlari ORDER BY kod ASC", conn)
        conn.close()
        if df.empty:
            return [""]
        return [f"{row['kod']} - {row['tanim']}" for idx, row in df.iterrows()]
    except Exception:
        return [""]

# --- VERİ İŞLEMLERİ ---
def verileri_getir(tc):
    conn = sqlite3.connect(DB_PATH)
    p_df = pd.read_sql_query("SELECT * FROM personel WHERE tc_kimlik = ?", conn, params=(tc,))
    e_df = pd.read_sql_query("SELECT * FROM evraklar WHERE tc_kimlik = ?", conn, params=(tc,))
    conn.close()
    return (p_df.iloc[0].to_dict() if not p_df.empty else {}, 
            e_df.iloc[0].to_dict() if not e_df.empty else {})

def verileri_guncelle(eski_tc, yeni_tc, p_data, e_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if eski_tc != yeni_tc:
        cursor.execute("UPDATE personel SET tc_kimlik=? WHERE tc_kimlik=?", (yeni_tc, eski_tc))
        cursor.execute("UPDATE evraklar SET tc_kimlik=? WHERE tc_kimlik=?", (yeni_tc, eski_tc))
        cursor.execute("UPDATE izinler SET tc_kimlik=? WHERE tc_kimlik=?", (yeni_tc, eski_tc))
        
    cursor.execute('''UPDATE personel SET 
                      ad_soyad=?, bolum=?, ise_giris=?, dogum_tarihi=?, dogum_yeri=?, 
                      baba_adi=?, anne_adi=?, telefon=?, mail=?, adres=?, askerlik=?, 
                      medeni_durum=?, mezuniyet=?, sirket=?, fiili_birim=?, iban=?, banka=?,
                      yillik_izin_baz=?, sgk_giris=?, banka_sube_kodu=?, banka_sube_adi=?,
                      cikis_tarihi=?, is_arama_izni_gun=?, fiili_cikis_tarihi=?, 
                      cikis_evrak_istifa=?, cikis_evrak_onay=?, cikis_evrak_teblig=?, 
                      cikis_evrak_ibraname=?, cikis_evrak_bordro=?, cikis_evrak_mutabakat=?,
                      cikis_aciklama=?, cikis_kodu=?, ihbar_baslatildi_mi=?, ihbar_islem_tarihi=?,
                      cikis_yapildi_mi=?, cikis_islem_tarihi=?, ihbar_sure_baslangici=?, meslek_kodu=?,
                      maas=?, maas_tipi=?
                      WHERE tc_kimlik=?''', p_data)
                      
    cursor.execute('''UPDATE evraklar SET 
                      evrak1_onay=?, evrak1_tarih=?, evrak2_onay=?, evrak2_tarih=?, 
                      evrak3_onay=?, evrak3_tarih=?, evrak4_onay=?, evrak4_tarih=?, 
                      evrak5_onay=?, evrak5_tarih=?, evrak6_onay=?, evrak6_tarih=?,
                      evrak7_onay=?, evrak7_tarih=?
                      WHERE tc_kimlik=?''', e_data)
    conn.commit()
    conn.close()

# Zorunlu tarihler için (doğum, işe giriş vs.) boş kalamaz
def parse_date(date_str):
    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d").date()
    except:
        return datetime.today().date()

# Opsiyonel tarihler için (çıkış işlemleri vb.) boş kalabilir
def parse_opt_date(date_str):
    if not date_str or str(date_str).strip() in ['None', '']:
        return None
    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d").date()
    except:
        return None

def kidem_ve_ihbar_hesapla(ise_giris_tarihi):
    bugun = datetime.today().date()
    fark = relativedelta(bugun, ise_giris_tarihi)
    toplam_gun = (bugun - ise_giris_tarihi).days
    
    if fark.years == 0 and fark.months < 6: ihbar_gun = 14
    elif fark.years == 0 or (fark.years == 1 and fark.months < 6): ihbar_gun = 28
    elif fark.years < 3: ihbar_gun = 42
    else: ihbar_gun = 56
        
    return fark, toplam_gun, ihbar_gun

def page_wrapper():
    left_spacer, main_content, right_spacer = st.columns([1, 4, 1])
    return main_content

# --- SAYFA BAŞLANGICI ---
content = page_wrapper()

with content:
    if 'secili_tc' not in st.session_state:
        st.warning("Lütfen önce listeden bir personel seçin.")
        if st.button("⬅️ Listeye Dön"): st.switch_page("pages/1_Personel_Sicil_Kartlari.py")
        st.stop()

    p, e = verileri_getir(st.session_state.secili_tc)

    if 'duzenle' not in st.session_state:
        st.session_state.duzenle = False

    # --- ÜST AKSİYON BARI ---
    col_baslik, col_butonlar = st.columns([3, 1])
    with col_baslik:
        cikis_durumu = "🔴 (İŞTEN AYRILDI)" if p.get('cikis_yapildi_mi') == '1' else ""
        st.title(f"📄 {p.get('ad_soyad', 'Personel Detayı')} {cikis_durumu}")
    with col_butonlar:
        st.write("") 
        if not st.session_state.duzenle:
            if st.button("✏️ Bilgileri Düzenle", use_container_width=True):
                st.session_state.duzenle = True
                st.rerun()
            if st.button("⬅️ Listeye Dön", use_container_width=True):
                st.switch_page("pages/1_Personel_Sicil_Kartlari.py")
        else:
            st.info("Düzenleme Modu Aktif")
            if st.button("❌ İptal Et", use_container_width=True):
                st.session_state.duzenle = False
                st.rerun()

    st.divider()

    # --- SİSTEMİK KIDEM HESAPLAMALARI ---
    ise_giris_tarihi = parse_date(p.get('ise_giris', datetime.today().date()))
    kidem_fark, toplam_kidem_gun, ihbar_gun = kidem_ve_ihbar_hesapla(ise_giris_tarihi)
    kidem_metni = f"{kidem_fark.years} Yıl {kidem_fark.months} Ay {kidem_fark.days} Gün ({toplam_kidem_gun} Gün)"

    # --- ANA FORM ALANI ---
    with st.form("tam_detay_formu"):
        t1, t2, t3, t4, t5 = st.tabs(["Kişisel Bilgiler", "İletişim & Eğitim", "Şirket & Banka", "Özlük Evrakları", "Çıkış İşlemleri"])
        
        # 1. SEKME: KİŞİSEL BİLGİLER
        with t1:
            col_sol, col_sag, col_foto = st.columns([2, 2, 1])
            with col_sol:
                y_ad = st.text_input("Ad Soyad", p.get('ad_soyad', ''), disabled=not st.session_state.duzenle)
                y_tc = st.text_input("TC Kimlik Numarası", p.get('tc_kimlik', ''), disabled=not st.session_state.duzenle)
                y_dogum_t = st.date_input("Doğum Tarihi", parse_date(p.get('dogum_tarihi', '')), format="DD/MM/YYYY", min_value=MIN_TARIH, max_value=MAX_TARIH, disabled=not st.session_state.duzenle)
                y_dogum_y = st.text_input("Doğum Yeri", p.get('dogum_yeri', ''), disabled=not st.session_state.duzenle)
            with col_sag:
                y_anne = st.text_input("Anne Adı", p.get('anne_adi', ''), disabled=not st.session_state.duzenle)
                y_baba = st.text_input("Baba Adı", p.get('baba_adi', ''), disabled=not st.session_state.duzenle)
                medeni_liste = ["Bekar", "Evli"]
                m_index = medeni_liste.index(p.get('medeni_durum', 'Bekar')) if p.get('medeni_durum', 'Bekar') in medeni_liste else 0
                y_medeni = st.selectbox("Medeni Durum", medeni_liste, index=m_index, disabled=not st.session_state.duzenle)
                askerlik_liste = ["Yapıldı", "Muaf", "Tecilli", "Yapılmadı"]
                a_index = askerlik_liste.index(p.get('askerlik', 'Yapıldı')) if p.get('askerlik', 'Yapıldı') in askerlik_liste else 0
                y_askerlik = st.selectbox("Askerlik Durumu", askerlik_liste, index=a_index, disabled=not st.session_state.duzenle)
            
            with col_foto:
                st.markdown(f"""
                <div style="background-color: #f0f7ff; padding: 10px; border-radius: 8px; border: 1px solid #2E86C1; margin-bottom: 15px; text-align: center;">
                    <span style="font-size: 12px; color: #555;">⏳ <b>Genel Kıdem Durumu</b></span><br>
                    <span style="font-weight: bold; color: #2E86C1; font-size: 14px;">{kidem_metni}</span>
                </div>
                """, unsafe_allow_html=True)
                
                st.write("**Fotoğraf**")
                foto_yolu = os.path.join(FOTO_DIR, f"{st.session_state.secili_tc}.png")
                if os.path.exists(foto_yolu): 
                    st.image(foto_yolu, width=150)
                else: 
                    st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=150)
                yeni_foto = None
                if st.session_state.duzenle:
                    yeni_foto = st.file_uploader("Değiştir", type=["png", "jpg", "jpeg"])

        # 2. SEKME: İLETİŞİM & EĞİTİM
        with t2:
            c1, c2 = st.columns(2)
            with c1:
                y_tel = st.text_input("Telefon Numarası", p.get('telefon', ''), disabled=not st.session_state.duzenle)
                y_mail = st.text_input("E-Posta Adresi", p.get('mail', ''), disabled=not st.session_state.duzenle)
            with c2:
                mezun_liste = ["İlkokul", "Ortaokul", "Lise", "Önlisans", "Lisans", "Yüksek Lisans"]
                mez_index = mezun_liste.index(p.get('mezuniyet', 'Lisans')) if p.get('mezuniyet', 'Lisans') in mezun_liste else 4
                y_mezuniyet = st.selectbox("Eğitim Durumu", mezun_liste, index=mez_index, disabled=not st.session_state.duzenle)
            y_adres = st.text_area("Açık Adres", p.get('adres', ''), height=100, disabled=not st.session_state.duzenle)

        # 3. SEKME: ŞİRKET & BANKA BİLGİLERİ
        with t3:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("### İş Bilgileri")
                y_sirket = st.text_input("Şirket", p.get('sirket', ''), disabled=not st.session_state.duzenle)
                y_bolum = st.text_input("Departman / Bölüm", p.get('bolum', ''), disabled=not st.session_state.duzenle)
                y_birim = st.text_input("Fiili Birim", p.get('fiili_birim', ''), disabled=not st.session_state.duzenle)
                
                meslek_listesi = dinamik_meslek_kodlari_getir()
                mevcut_meslek = p.get('meslek_kodu', '')
                try:
                    m_idx = meslek_listesi.index(mevcut_meslek) if mevcut_meslek in meslek_listesi else 0
                except ValueError:
                    m_idx = 0
                y_meslek_kodu = st.selectbox("SGK Meslek Kodu", meslek_listesi, index=m_idx, disabled=not st.session_state.duzenle)

            with c2:
                st.markdown("### Tarihler")
                y_ise_giris = st.date_input("İşe Giriş Tarihi", parse_date(p.get('ise_giris', '')), format="DD/MM/YYYY", min_value=MIN_TARIH, max_value=MAX_TARIH, disabled=not st.session_state.duzenle)
                y_sgk = st.date_input("SGK Giriş Tarihi", parse_date(p.get('sgk_giris', '')), format="DD/MM/YYYY", min_value=MIN_TARIH, max_value=MAX_TARIH, disabled=not st.session_state.duzenle)
                y_izin_baz = st.date_input("Yıllık İzin Baz Tarihi", parse_date(p.get('yillik_izin_baz', '')), format="DD/MM/YYYY", min_value=MIN_TARIH, max_value=MAX_TARIH, disabled=not st.session_state.duzenle)
                
                # --- YENİ EKLENEN: MAAŞ BİLGİLERİ ---
                st.markdown("### Maaş Bilgileri")
                varsayilan_maas = float(p.get('maas', 0.0)) if p.get('maas') else 0.0
                y_maas_tutari = st.number_input("Maaş Tutarı (TL)", min_value=0.0, step=1000.0, value=varsayilan_maas, format="%.2f", disabled=not st.session_state.duzenle)
                
                maas_tipleri = ["Net", "Brüt"]
                mevcut_tip = p.get('maas_tipi', 'Net') if p.get('maas_tipi') else 'Net'
                tip_idx = maas_tipleri.index(mevcut_tip) if mevcut_tip in maas_tipleri else 0
                y_maas_tipi = st.selectbox("Maaş Türü", maas_tipleri, index=tip_idx, disabled=not st.session_state.duzenle)

            with c3:
                st.markdown("### Banka Bilgileri")
                y_banka = st.text_input("Banka Adı", p.get('banka', ''), disabled=not st.session_state.duzenle)
                y_sube_adi = st.text_input("Şube Adı", p.get('banka_sube_adi', ''), disabled=not st.session_state.duzenle)
                y_sube_kodu = st.text_input("Şube Kodu", p.get('banka_sube_kodu', ''), disabled=not st.session_state.duzenle)
                y_iban = st.text_input("IBAN", p.get('iban', ''), disabled=not st.session_state.duzenle)

        # 4. SEKME: ÖZLÜK EVRAKLARI
        with t4:
            st.write("Evrakların teslim durumunu ve tarihlerini yönetin.")
            evrak_isimleri = ["1. Nüfus Cüzdanı", "2. İkametgah", "3. Sabıka Kaydı", "4. Diploma", "5. 2 Adet Fotoğraf", "6. Nüfus Kayıt Örneği", "7. Adli Sicil Kaydı"]
            y_evrak_onay = []
            y_evrak_tarih = []
            for i in range(1, 8):
                ec1, ec2 = st.columns([1, 2])
                with ec1:
                    mevcut_onay = True if str(e.get(f'evrak{i}_onay', '0')) == '1' else False
                    onay = st.checkbox(evrak_isimleri[i-1], value=mevcut_onay, disabled=not st.session_state.duzenle)
                    y_evrak_onay.append(1 if onay else 0)
                with ec2:
                    varsayilan_tarih = parse_opt_date(e.get(f'evrak{i}_tarih', ''))
                    # Evrak tarihi boş bırakılabilir yapıya geçirildi
                    tarih = st.date_input(f"Teslim Tarihi {i}", value=varsayilan_tarih, format="DD/MM/YYYY", min_value=MIN_TARIH, max_value=MAX_TARIH, disabled=not st.session_state.duzenle, key=f"e_tarih_{i}")
                    y_evrak_tarih.append(str(tarih) if tarih else "")

        # 5. SEKME: ÇIKIŞ İŞLEMLERİ
        with t5:
            st.markdown("<h4 style='text-align: center; border-bottom: 2px solid #ccc; padding-bottom: 10px; margin-bottom: 20px;'>ÇIKIŞ İŞLEMLERİ</h4>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; background-color: #f8f9fa; border: 1px solid #d1d5db; border-radius: 10px; padding: 15px 25px; margin-bottom: 25px;">
                <div style="text-align: center; flex: 1; border-right: 1px solid #d1d5db;">
                    <span style="font-size: 14px; color: #6b7280; font-weight: 600;">Kıdem Süresi</span><br>
                    <span style="font-size: 16px; color: #1f2937; font-weight: 700;">{kidem_fark.years} Yıl, {kidem_fark.months} Ay, {kidem_fark.days} Gün</span>
                </div>
                <div style="text-align: center; flex: 1;">
                    <span style="font-size: 14px; color: #6b7280; font-weight: 600;">Yasal İhbar Süresi</span><br>
                    <span style="font-size: 16px; color: #dc2626; font-weight: 700;">{ihbar_gun} Gün</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                ihbar_bas_db = parse_opt_date(p.get('ihbar_sure_baslangici', ''))
                y_ihbar_baslangic = st.date_input("İhbar Süresi Başlangıç Tarihi", value=ihbar_bas_db, format="DD/MM/YYYY", min_value=MIN_TARIH, max_value=MAX_TARIH, disabled=not st.session_state.duzenle)
                
                varsayilan_izin = int(p.get('is_arama_izni_gun', 0)) if p.get('is_arama_izni_gun') else 0
                y_is_arama_izni = st.number_input("İş Arama İzni (Gün - Toplu Kullanım)", min_value=0, value=varsayilan_izin, disabled=not st.session_state.duzenle)
                
            with c2:
                if y_ihbar_baslangic:
                    hesaplanan_sgk = y_ihbar_baslangic + timedelta(days=ihbar_gun)
                    hesaplanan_fiili = hesaplanan_sgk - timedelta(days=y_is_arama_izni)
                else:
                    hesaplanan_sgk = parse_opt_date(p.get('cikis_tarihi', ''))
                    hesaplanan_fiili = parse_opt_date(p.get('fiili_cikis_tarihi', ''))
                
                y_sgk_cikis = st.date_input("SGK Çıkış Tarihi (Son İş Günü)", value=hesaplanan_sgk, format="DD/MM/YYYY", min_value=MIN_TARIH, max_value=MAX_TARIH, disabled=not st.session_state.duzenle)
                y_fiili_cikis = st.date_input("Fiili Çalışma Bitiş Tarihi", value=hesaplanan_fiili, format="DD/MM/YYYY", min_value=MIN_TARIH, max_value=MAX_TARIH, disabled=not st.session_state.duzenle)

            st.write("---")
            
            cikis_listesi = dinamik_cikis_kodlari_getir()
            mevcut_cikis = p.get('cikis_kodu', '')
            try:
                c_idx = cikis_listesi.index(mevcut_cikis) if mevcut_cikis in cikis_listesi else 0
            except ValueError:
                c_idx = 0
            
            y_cikis_kodu = st.selectbox("SGK Çıkış Kodu", cikis_listesi, index=c_idx, disabled=not st.session_state.duzenle)
            y_cikis_aciklama = st.text_area("Açıklama / Notlar", value=p.get('cikis_aciklama', ''), disabled=not st.session_state.duzenle)
            
            st.markdown("##### Çıkış Evrakları Checklist")
            e_col1, e_col2 = st.columns(2)
            with e_col1:
                y_c_istifa = st.checkbox("İstifa Dilekçesi", value=bool(int(p.get('cikis_evrak_istifa', 0) or 0)), disabled=not st.session_state.duzenle)
                y_c_onay = st.checkbox("İstifa Onay Dilekçesi", value=bool(int(p.get('cikis_evrak_onay', 0) or 0)), disabled=not st.session_state.duzenle)
                y_c_teblig = st.checkbox("İşveren Çıkarıyorsa Tebliğ Dilekçesi", value=bool(int(p.get('cikis_evrak_teblig', 0) or 0)), disabled=not st.session_state.duzenle)
            with e_col2:
                y_c_ibraname = st.checkbox("İbraname", value=bool(int(p.get('cikis_evrak_ibraname', 0) or 0)), disabled=not st.session_state.duzenle)
                y_c_bordro = st.checkbox("Çıkış Yapılacağı Takvim Tarihinin Ay Bordrosu", value=bool(int(p.get('cikis_evrak_bordro', 0) or 0)), disabled=not st.session_state.duzenle)
                y_c_mutabakat = st.checkbox("Yıllık İzin Mutabakat Formu", value=bool(int(p.get('cikis_evrak_mutabakat', 0) or 0)), disabled=not st.session_state.duzenle)

            st.write("---")
            
            st.markdown("##### Çıkış İşlemi Onayı")
            i_col1, i_col2 = st.columns(2)
            with i_col1:
                y_ihbar_baslat = st.checkbox("İhbar Sürecini Başlat", value=bool(int(p.get('ihbar_baslatildi_mi', 0) or 0)), disabled=not st.session_state.duzenle)
                if y_ihbar_baslat:
                    ihbar_islem_db = parse_opt_date(p.get('ihbar_islem_tarihi', ''))
                    y_ihbar_islem_t = st.date_input("İhbar Başlatma İşlem Tarihi", value=ihbar_islem_db, format="DD/MM/YYYY", min_value=MIN_TARIH, max_value=MAX_TARIH, disabled=not st.session_state.duzenle)
                else: 
                    y_ihbar_islem_t = None
            with i_col2:
                y_cikis_yap = st.checkbox("Çıkışı Tamamla (Sistemden Düşür)", value=bool(int(p.get('cikis_yapildi_mi', 0) or 0)), disabled=not st.session_state.duzenle)
                if y_cikis_yap:
                    cikis_islem_db = parse_opt_date(p.get('cikis_islem_tarihi', ''))
                    y_cikis_islem_t = st.date_input("Çıkış İşlemi Onay Tarihi", value=cikis_islem_db, format="DD/MM/YYYY", min_value=MIN_TARIH, max_value=MAX_TARIH, disabled=not st.session_state.duzenle)
                else: 
                    y_cikis_islem_t = None

        # FORMU KAYDETME TETİKLEYİCİSİ
        st.write("---")
        submit_buton = st.form_submit_button("💾 Tüm Değişiklikleri Kaydet", disabled=not st.session_state.duzenle)
        
        if submit_buton:
            eski_tc = st.session_state.secili_tc
            yeni_foto_yolu = os.path.join(FOTO_DIR, f"{y_tc}.png")
            if eski_tc != y_tc and os.path.exists(os.path.join(FOTO_DIR, f"{eski_tc}.png")):
                os.rename(os.path.join(FOTO_DIR, f"{eski_tc}.png"), yeni_foto_yolu)
            if yeni_foto is not None:
                with open(yeni_foto_yolu, "wb") as f: 
                    f.write(yeni_foto.getbuffer())

            # Kayıt anında seçilmeyen boş tarihleri ("None") boş string "" olarak gönder
            p_yeni_data = (
                y_ad, y_bolum, str(y_ise_giris), str(y_dogum_t), y_dogum_y, 
                y_baba, y_anne, y_tel, y_mail, y_adres, y_askerlik, 
                y_medeni, y_mezuniyet, y_sirket, y_birim, y_iban, y_banka, 
                str(y_izin_baz), str(y_sgk), y_sube_kodu, y_sube_adi,
                str(y_sgk_cikis) if y_sgk_cikis else "", 
                str(y_is_arama_izni), 
                str(y_fiili_cikis) if y_fiili_cikis else "",
                1 if y_c_istifa else 0, 1 if y_c_onay else 0, 1 if y_c_teblig else 0,
                1 if y_c_ibraname else 0, 1 if y_c_bordro else 0, 1 if y_c_mutabakat else 0,
                y_cikis_aciklama, y_cikis_kodu, 
                1 if y_ihbar_baslat else 0, 
                str(y_ihbar_islem_t) if y_ihbar_islem_t else "",
                1 if y_cikis_yap else 0, 
                str(y_cikis_islem_t) if y_cikis_islem_t else "", 
                str(y_ihbar_baslangic) if y_ihbar_baslangic else "",
                y_meslek_kodu,
                float(y_maas_tutari),
                y_maas_tipi,
                y_tc 
            )
            
            e_yeni_data = (
                y_evrak_onay[0], y_evrak_tarih[0], y_evrak_onay[1], y_evrak_tarih[1],
                y_evrak_onay[2], y_evrak_tarih[2], y_evrak_onay[3], y_evrak_tarih[3],
                y_evrak_onay[4], y_evrak_tarih[4], y_evrak_onay[5], y_evrak_tarih[5],
                y_evrak_onay[6], y_evrak_tarih[6], y_tc
            )
            
            verileri_guncelle(eski_tc, y_tc, p_yeni_data, e_yeni_data)
            st.session_state.secili_tc = y_tc
            st.success("Tüm veriler, meslek, maaş bilgisi ve çıkış kodları dahil başarıyla güncellendi!")
            st.session_state.duzenle = False
            st.rerun()