import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
from dateutil.relativedelta import relativedelta

# --- SAYFA AYARLARI ---
st.set_page_config(layout="wide")
DB_PATH = "modu_ik/personel_sistemi.db"
MIN_TARIH = date(1950, 1, 1)

# --- STİL (Diğer sayfalarla tutarlı) ---
st.markdown("""
    <style>
    label { color: #2E86C1 !important; font-weight: 600 !important; }
    div[data-baseweb="input"], div[data-baseweb="datepicker"], div[data-baseweb="select"] {
        border: 1px solid #2E86C1 !important;
        border-radius: 8px !important;
        background-color: #f0f7ff !important;
    }
    input { background-color: transparent !important; }
    </style>
""", unsafe_allow_html=True)

# --- SAYFAYI ORTALAYAN ÇERÇEVE ---
def page_wrapper():
    left_spacer, main_content, right_spacer = st.columns([1, 4, 1])
    return main_content

content = page_wrapper()

# ==================== VERİTABANI FONKSİYONLARI ====================

def personel_bilgisi_getir(tc):
    """TC kimliğe göre personel kaydını getirir."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM personel WHERE tc_kimlik = ?", conn, params=(tc,))
    conn.close()
    if df.empty:
        return None
    return df.iloc[0]

def izin_kayitlarini_getir(tc):
    """TC kimliğe ait tüm izin kayıtlarını getirir (en yeni üstte)."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT id, tur, baslangic, bitis, gun, aciklama FROM izinler WHERE tc_kimlik = ? ORDER BY baslangic DESC",
        conn, params=(tc,)
    )
    conn.close()
    return df

def izin_ekle(tc, tur, baslangic, bitis, gun, aciklama):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO izinler (tc_kimlik, tur, baslangic, bitis, gun, aciklama) VALUES (?, ?, ?, ?, ?, ?)",
        (tc, tur, str(baslangic), str(bitis), gun, aciklama)
    )
    conn.commit()
    conn.close()

def izin_sil(izin_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM izinler WHERE id = ?", (izin_id,))
    conn.commit()
    conn.close()

def tum_personel_listesi():
    """Dropdown'dan seçim yapılabilmesi için TC - Ad Soyad listesi."""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT tc_kimlik, ad_soyad FROM personel ORDER BY ad_soyad ASC", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame(columns=["tc_kimlik", "ad_soyad"])

# ==================== HESAPLAMA FONKSİYONU (4857 Sayılı İş Kanunu Madde 53) ====================

def _kidem_yili_bazli_gun(tamamlanan_kidem_yili):
    """
    Sadece kıdeme göre (yaş istisnası hariç) o kıdem yılına karşılık gelen
    yasal yıllık izin gün sayısını döndürür.

    1 - 5 yıl (5 dahil)                      -> 14 gün
    5 yıldan fazla - 15 yıldan az (6-14 yıl) -> 20 gün
    15 yıl (dahil) ve üzeri                  -> 26 gün
    """
    if tamamlanan_kidem_yili <= 5:
        return 14
    elif tamamlanan_kidem_yili <= 14:
        return 20
    else:
        return 26

def detayli_izin_hesapla(ise_giris, dogum_tarihi):
    """
    Kıdem, yaş ve (kıdem + yaş istisnası birlikte değerlendirilerek)
    birikimli yıllık izin hak edişini hesaplar.

    ÖNEMLİ: Yaş istisnası (18 ve altı veya 50 ve üzeri) her kıdem yılı için
    O YILIN DOLDUĞU TARİHTEKİ yaşa göre ayrı ayrı değerlendirilir; bugünkü
    yaş sadece güncel/son kıdem yılı için geçerlidir. Örneğin işe girişte
    18 yaşında olan biri 1. yılını 18 yaşında doldurup 20 gün kazanır,
    2. yılını 19 yaşında (istisna dışı) doldurup o yıl için 14 gün kazanır
    -- bugün 19 yaşında olması 1. yıldaki 20 günlük hakkı geriye dönük
    olarak değiştirmez.

    Kıdeme göre hesaplanan gün sayısı zaten 20'den yüksekse (örn. 26),
    yaş istisnası bu hakkı DÜŞÜRMEZ; ikisinden yüksek olan uygulanır.
    """
    bugun = date.today()
    kidem = relativedelta(bugun, ise_giris)
    yas = bugun.year - dogum_tarihi.year
    yillar = kidem.years

    # Başlangıçtan bugüne kadar biriken toplam hak ediş
    # (her tamamlanan kıdem yılı, o yılın dolduğu tarihteki yaşa göre hesaplanır)
    toplam_hak = 0
    guncel_yillik_hak = 0
    for tamamlanan_yil in range(1, yillar + 1):
        yil_doldugu_tarih = ise_giris + relativedelta(years=tamamlanan_yil)
        # Yaş hesabı takvim yılı bazlı yapılır (İş Kanunu uygulaması)
        o_anki_yas = yil_doldugu_tarih.year - dogum_tarihi.year
        o_anki_yas_istisnasi = (o_anki_yas <= 18) or (o_anki_yas >= 50)

        kidem_bazli = _kidem_yili_bazli_gun(tamamlanan_yil)
        if o_anki_yas_istisnasi:
            yillik = max(kidem_bazli, 20)
        else:
            yillik = kidem_bazli
        toplam_hak += yillik
        guncel_yillik_hak = yillik  # Son işlenen yıl = bulunulan güncel kıdem yılı

    return kidem, yas, toplam_hak, guncel_yillik_hak

def str_to_date(deger):
    """Veritabanından gelen metin tarihi date objesine çevirir, hatalıysa bugünü döner."""
    try:
        return date.fromisoformat(str(deger))
    except Exception:
        return date.today()

# ==================== ARAYÜZ ====================

with content:
    st.title("🗓️ İzin Takibi")

    col_menu, col_bos = st.columns([1, 4])
    with col_menu:
        if st.button("🏠 Ana Menü", use_container_width=True):
            st.switch_page("0_Ana_Menu.py")

    st.write("---")

    # --- PERSONEL ARAMA ---
    st.markdown("### 🔍 Personel Seç")
    col_tc, col_liste = st.columns([1.5, 2])
    with col_tc:
        tc_girisi = st.text_input("TC Kimlik No (Enter'a bas)", placeholder="Örn: 12345678901", max_chars=11)
    with col_liste:
        personel_df = tum_personel_listesi()
        secenekler = ["-- Listeden Seç --"] + [f"{row['tc_kimlik']} - {row['ad_soyad']}" for _, row in personel_df.iterrows()]
        secim = st.selectbox("veya Listeden Seç", secenekler)

    # Öncelik: manuel TC girişi. Boşsa listeden seçilen kullanılır.
    aktif_tc = tc_girisi.strip() if tc_girisi.strip() else (secim.split(" - ")[0] if secim != "-- Listeden Seç --" else "")

    st.divider()

    if not aktif_tc:
        st.info("Lütfen bir personel arayın veya listeden seçin.")
    else:
        personel = personel_bilgisi_getir(aktif_tc)

        if personel is None:
            st.warning("Bu TC Kimlik numarasına ait bir personel bulunamadı.")
        else:
            ise_giris = str_to_date(personel.get("ise_giris"))
            dogum_tarihi = str_to_date(personel.get("dogum_tarihi"))

            kidem, yas, toplam_hak_edis, guncel_yillik_hak = detayli_izin_hesapla(ise_giris, dogum_tarihi)
            izin_gecmisi = izin_kayitlarini_getir(aktif_tc)

            toplam_kullanilan = 0
            if not izin_gecmisi.empty:
                toplam_kullanilan = int(izin_gecmisi.loc[izin_gecmisi['tur'] == 'Yıllık İzin', 'gun'].sum())

            kalan_bakiye = toplam_hak_edis - toplam_kullanilan

            # --- PERSONEL BİLGİ KARTI ---
            with st.container(border=True):
                st.markdown(f"#### 👤 {personel.get('ad_soyad', '-')}")
                c1, c2, c3 = st.columns(3)
                c1.write(f"**TC Kimlik:** {personel.get('tc_kimlik', '-')}")
                c2.write(f"**Bölüm:** {personel.get('bolum', '-')}")
                c3.write(f"**Şirket:** {personel.get('sirket', '-')}")
                st.write(f"**İşe Giriş Tarihi:** {ise_giris.strftime('%d/%m/%Y')}")

            st.markdown("")

            if kidem.years < 1:
                st.warning("⚠️ Bu personel henüz 1 yıllık kıdemini doldurmadığı için kanunen yıllık izne hak kazanmamıştır.")

            # --- ÖZET METRİKLER ---
            st.markdown("##### 📊 İzin Özeti")
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("Kıdem", f"{kidem.years} Yıl {kidem.months} Ay")
            m2.metric("Yaş", f"{yas}")
            m3.metric("Bu Yılki İzin Hakkı", f"{guncel_yillik_hak} Gün")
            m4.metric("Toplam Hak Ediş", f"{toplam_hak_edis} Gün")
            m5.metric("Kullanılan (Yıllık)", f"{toplam_kullanilan} Gün")
            m6.metric("Kalan Bakiye", f"{kalan_bakiye} Gün",
                       delta=None if kalan_bakiye >= 0 else "Bakiye Aşıldı",
                       delta_color="inverse")

            st.caption("ℹ️ **Bu Yılki İzin Hakkı**: içinde bulunulan kıdem yılına ait yasal izin süresi (14/20/26 gün, yaş istisnası dahil). **Toplam Hak Ediş**: işe giriş tarihinden bugüne kadar biriken toplam izin gününün toplamı.")

            st.divider()

            col_form, col_gecmis = st.columns([1, 2])

            # --- YENİ İZİN KAYDI FORMU ---
            with col_form:
                with st.container(border=True):
                    st.markdown("###### ➕ Yeni İzin Kaydı Oluştur")
                    f_tur = st.selectbox("İzin Türü", ["Yıllık İzin", "Mazeret İzni", "Ücretsiz İzin", "Rapor"], key="yeni_izin_tur")
                    f_bas = st.date_input("İzin Başlangıç", format="DD/MM/YYYY", min_value=MIN_TARIH, key="yeni_izin_bas")
                    f_bitis = st.date_input("İzin Bitiş", format="DD/MM/YYYY", min_value=MIN_TARIH, key="yeni_izin_bitis")

                    f_gun = (f_bitis - f_bas).days + 1
                    if f_gun > 0:
                        st.info(f"Hesaplanan İzin Süresi: **{f_gun} Gün**")
                    else:
                        st.error("Bitiş tarihi, başlangıç tarihinden önce olamaz.")

                    f_isbasi = f_bitis + relativedelta(days=1)
                    st.write(f"Tahmini İş Başı Tarihi: **{f_isbasi.strftime('%d/%m/%Y')}**")

                    f_ack = st.text_area("Açıklama", key="yeni_izin_aciklama")

                    if st.button("💾 İzin Kaydını Oluştur", type="primary", use_container_width=True):
                        if f_gun <= 0:
                            st.error("Geçerli bir tarih aralığı seçiniz.")
                        elif f_tur == "Yıllık İzin" and f_gun > kalan_bakiye:
                            st.error(f"Kalan bakiye ({kalan_bakiye} gün) yetersiz! Yine de kaydetmek isterseniz izin türünü değiştirin.")
                        else:
                            izin_ekle(aktif_tc, f_tur, f_bas, f_bitis, f_gun, f_ack)
                            st.success("İzin kaydı başarıyla oluşturuldu!")
                            st.rerun()

            # --- İZİN GEÇMİŞİ ---
            with col_gecmis:
                with st.container(border=True):
                    st.markdown("###### 📋 İzin Kullanım Geçmişi")
                    if izin_gecmisi.empty:
                        st.info("Bu personele ait kayıtlı izin bulunmamaktadır.")
                    else:
                        for _, kayit in izin_gecmisi.iterrows():
                            with st.container(border=True):
                                kc1, kc2, kc3, kc4 = st.columns([1.5, 2, 1, 0.7])
                                kc1.write(f"**{kayit['tur']}**")
                                kc2.write(f"{kayit['baslangic']} → {kayit['bitis']}")
                                kc3.write(f"**{kayit['gun']} Gün**")
                                if kc4.button("🗑️", key=f"sil_{kayit['id']}", help="Kaydı Sil"):
                                    izin_sil(kayit['id'])
                                    st.rerun()
                                if kayit['aciklama']:
                                    st.caption(f"📝 {kayit['aciklama']}")