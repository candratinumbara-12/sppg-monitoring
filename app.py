import os
from datetime import datetime
import streamlit as st
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Checklist SPPG Monitoring - BGN",
    page_icon="🍲",
    layout="centered"
)

# --- KONFIGURASI DATABASE SQLITE ---
def init_db():
    conn = sqlite3.connect('sppg_streamlit.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            nama_sppg TEXT,
            id_sppg TEXT,
            nama_kasppg TEXT,
            nama_plok TEXT,
            nama_plog TEXT,
            asisten_lapangan TEXT,
            admin_gudang TEXT,
            chef TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect('sppg_streamlit.db', check_same_thread=False)

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''
    st.session_state['user_id'] = None

if 'pdf_ready' not in st.session_state:
    st.session_state['pdf_ready'] = False
    st.session_state['pdf_filename'] = ""

# --- HALAMAN LOGIN & REGISTER ---
if not st.session_state['logged_in']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>🍲 SPPG MONITORING</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Badan Gizi Nasional</p>", unsafe_allow_html=True)
        
        menu = st.radio("Pilih Mode", ["Login", "Register Akun"], horizontal=True, label_visibility="collapsed")
        
        if menu == "Login":
            st.markdown("### Silakan Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Masuk Aplikasi", type="primary", use_container_width=True):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id, username FROM users WHERE username = ? AND password = ?", (username, password))
                user = cursor.fetchone()
                conn.close()
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['user_id'] = user[0]
                    st.session_state['username'] = user[1]
                    st.rerun()
                else:
                    st.error("Username atau password salah!")
        else:
            st.markdown("### Pendaftaran Akun Baru")
            new_user = st.text_input("Username Baru")
            new_pass = st.text_input("Password Baru", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Daftar Sekarang", use_container_width=True):
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (new_user, new_pass))
                    conn.commit()
                    conn.close()
                    st.success("Akun berhasil dibuat! Silakan pindah ke tab Login.")
                except:
                    st.error("Username sudah terdaftar.")

else:
    # --- AMBIL DATA USER ---
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nama_sppg, id_sppg, nama_kasppg, nama_plok, nama_plog, asisten_lapangan, admin_gudang, chef FROM users WHERE id = ?", (st.session_state['user_id'],))
    user_data = cursor.fetchone()
    conn.close()
    
    if not user_data[0]:
        st.warning("⚠️ Silakan lengkapi Setup Awal Profil SPPG terlebih dahulu.")
        st.markdown("### Setup Awal Profil SPPG")
        with st.form("setup_form"):
            nama_sppg = st.text_input("Nama SPPG (Contoh: SPPG Paseh Cigentur)")
            id_sppg = st.text_input("ID SPPG")
            nama_kasppg = st.text_input("Nama KASPPG (Kepala SPPG)")
            nama_plok = st.text_input("Nama PLOK")
            nama_plog = st.text_input("Nama PLOG")
            asisten_lapangan = st.text_input("Asisten Lapangan")
            admin_gudang = st.text_input("Admin Gudang")
            chef = st.text_input("Chef")
            
            if st.form_submit_button("Simpan Profil Setup", type="primary", use_container_width=True):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET nama_sppg=?, id_sppg=?, nama_kasppg=?, nama_plok=?, nama_plog=?, asisten_lapangan=?, admin_gudang=?, chef=?
                    WHERE id=?
                """, (nama_sppg, id_sppg, nama_kasppg, nama_plok, nama_plog, asisten_lapangan, admin_gudang, chef, st.session_state['user_id']))
                conn.commit()
                conn.close()
                st.success("Setup berhasil disimpan!")
                st.rerun()
    else:
        # Sidebar
        st.sidebar.markdown(f"### 👤 {st.session_state['username']}")
        st.sidebar.info(f"**SPPG:** {user_data[0]}\n\n**ID:** {user_data[1]}\n\n**Chef:** {user_data[7]}")
        if st.sidebar.button("Keluar (Logout)", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()

        st.markdown("<h1 style='text-align: center; color: #1f4e78;'>CHECKLIST HARIAN SPPG</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Sistem Koordinasi Zoom & Monitoring Badan Gizi Nasional</p>", unsafe_allow_html=True)
        st.markdown("---")

        with st.form("checklist_form"):
            
            # --- BAGIAN HEADER & INFO UMUM ---
            st.markdown("### 📌 INFORMASI UMUM & KOORDINASI ZOOM")
            col1, col2 = st.columns(2)
            with col1:
                tanggal = st.date_input("Tanggal Pelaksanaan", datetime.now())
                jam_zoom = st.text_input("Jam Mulai Zoom", "08:00")
            with col2:
                pengawas_keuangan = st.text_input("Pengawas Keuangan")
                pengawas_gizi = st.text_input("Pengawas Gizi")

            # --- BAGIAN I. DATA UMUM ---
            st.markdown("### 🏢 I. DATA UMUM & SERTIFIKASI")
            st.markdown("##### 1. Jumlah Penerima Manfaat & Sertifikasi")
            col1, col2 = st.columns(2)
            with col1:
                pm_didik_potensi = st.text_input("PM Peserta Didik (Potensi PM)")
                pm_3b_potensi = st.text_input("PM 3B (Potensi PM)")
                total_pm_potensi = st.text_input("Total Penerima Manfaat (Potensi)")
            with col2:
                pm_didik_layani = st.text_input("PM Peserta Didik (Dilayani Hari Ini)")
                pm_3b_layani = st.text_input("PM 3B (Dilayani Hari Ini)")
                total_pm_layani = st.text_input("Total Penerima Manfaat (Dilayani Hari Ini)")

            st.markdown("##### Status Sertifikasi")
            col1, col2, col3 = st.columns(3)
            with col1:
                sertif_slhs = st.selectbox("Sertifikat SLHS", ["Ya", "Tidak"])
            with col2:
                sertif_halal = st.selectbox("Sertifikat Halal", ["Ya", "Tidak"])
            with col3:
                sertif_bnsp = st.selectbox("Sertifikat BNSP Chef", ["Ya", "Tidak"])

            st.markdown("##### 2. Air Bersih")
            col1, col2 = st.columns(2)
            with col1:
                sumber_air_minum = st.selectbox("Sumber Air Minum", ["RO", "Galon", "PDAM", "Sumur", "Lainnya"])
                ph_air_minum = st.text_input("pH Air Minum", "Diambil tgl ... jam ... (isi NA bila tidak ada alat)")
            with col2:
                sumber_air_masak = st.selectbox("Sumber Air Masak", ["RO", "Galon", "PDAM", "Sumur", "Lainnya"])
                ph_air_masak = st.text_input("pH Air Masak", "Diambil tgl ... jam ... (isi NA bila tidak ada alat)")

            st.markdown("##### 3. Kondisi Ruangan")
            termometer_ok = st.selectbox("Semua ruangan memiliki termometer yang berfungsi?", ["Ya", "Tidak"])
            termometer_ket = st.text_input("Keterangan Termometer (Jika tidak, sebutkan di ruangan apa)")
            
            suhu_ruang_ok = st.selectbox("Suhu di seluruh ruangan sesuai standar (25°C - 30°C)?", ["Ya", "Tidak"])
            suhu_ruang_val = st.text_input("Suhu ruangan terkini (°C)", "28°C")
            
            ruang_bersih_ok = st.selectbox("Ruangan dalam keadaan bersih sesuai standar?", ["Ya", "Tidak"])
            ruang_bersih_ket = st.text_input("Catatan kebersihan ruangan")
            
            insect_ok = st.selectbox("Insect killer berfungsi baik di ruang persiapan, pengolahan & pemorsian?", ["Ya", "Tidak"])
            insect_jml = st.text_input("Jumlah unit berfungsi", "1 unit")

            # --- BAGIAN II. PENERIMAAN & PENYIMPANAN BAHAN BAKU ---
            st.markdown("### 📦 II. PENERIMAAN & PENYIMPANAN BAHAN BAKU")
            st.markdown("##### 1. Spesifikasi Bahan Baku")
            
            st.markdown("**Karbohidrat**")
            k_karbo_jml = st.selectbox("Jumlah Karbohidrat", ["Sesuai", "Kurang", "Lebih"], key="k1")
            k_karbo_kual = st.selectbox("Kualitas Karbohidrat", ["Sesuai", "Baik", "Kurang Baik"], key="k2")
            k_karbo_jam = st.text_input("Waktu Karbohidrat (Jam)", "07:00", key="k3")
            k_karbo_nama = st.text_input("Penerima & TTD Karbohidrat", "Nama / Paraf", key="k4")

            st.markdown("**Protein Hewani**")
            k_hewani_jml = st.selectbox("Jumlah Protein Hewani", ["Sesuai", "Kurang", "Lebih"], key="h1")
            k_hewani_kual = st.selectbox("Kualitas Protein Hewani", ["Sesuai", "Baik", "Kurang Baik"], key="h2")
            k_hewani_jam = st.text_input("Waktu Hewani (Jam)", "07:15", key="h3")
            k_hewani_nama = st.text_input("Penerima & TTD Hewani", "Nama / Paraf", key="h4")

            st.markdown("**Protein Nabati**")
            k_nabati_jml = st.selectbox("Jumlah Protein Nabati", ["Sesuai", "Kurang", "Lebih"], key="n1")
            k_nabati_kual = st.selectbox("Kualitas Protein Nabati", ["Sesuai", "Baik", "Kurang Baik"], key="n2")
            k_nabati_jam = st.text_input("Waktu Nabati (Jam)", "07:30", key="n3")
            k_nabati_nama = st.text_input("Penerima & TTD Nabati", "Nama / Paraf", key="n4")

            st.markdown("**Buah**")
            k_buah_jml = st.selectbox("Jumlah Buah", ["Sesuai", "Kurang", "Lebih"], key="b1")
            k_buah_kual = st.selectbox("Kualitas Buah", ["Sesuai", "Baik", "Kurang Baik"], key="b2")
            k_buah_jam = st.text_input("Waktu Buah (Jam)", "07:45", key="b3")
            k_buah_nama = st.text_input("Penerima & TTD Buah", "Nama / Paraf", key="b4")

            st.markdown("**Sayur**")
            k_sayur_jml = st.selectbox("Jumlah Sayur", ["Sesuai", "Kurang", "Lebih"], key="s1")
            k_sayur_kual = st.selectbox("Kualitas Sayur", ["Sesuai", "Baik", "Kurang Baik"], key="s2")
            k_sayur_jam = st.text_input("Waktu Sayur (Jam)", "08:00", key="s3")
            k_sayur_nama = st.text_input("Penerima & TTD Sayur", "Nama / Paraf", key="s4")

            st.markdown("##### 2. Suhu Bahan Baku & Ruang Penyimpanan")
            suhu_beku_1 = st.text_input("Suhu bahan baku beku (1) (°C & Jam)", "-18°C, jam ...")
            nama_bahan_beku_1 = st.text_input("Nama bahan baku beku (1)")
            suhu_beku_2 = st.text_input("Suhu bahan baku beku (2) (°C & Jam)", "-18°C, jam ...")
            nama_bahan_beku_2 = st.text_input("Nama bahan baku beku (2)")
            suhu_chiller_bb = st.text_input("Suhu chiller bahan baku (< 5°C)", "4°C")
            suhu_freezer_bb = st.text_input("Suhu freezer bahan baku (< -18°C)", "-20°C")

            st.markdown("##### 3. Bahan Makanan")
            pencucian_air = st.selectbox("Semua bahan dicuci pakai air dari sumber di atas?", ["Ya", "Tidak"])
            sumber_pencucian = st.text_input("Sumber air pencucian", "PDAM / RO")
            tahu_chiller = st.selectbox("Apakah tahu disimpan di dalam chiller?", ["Ya", "Tidak"])
            suhu_chiller_tahu = st.text_input("Suhu chiller penyimpanan tahu (°C)", "4°C")
            fifo_ok = st.selectbox("Bahan dipakai lebih dulu sesuai FIFO / FEFO?", ["Ya", "Tidak"])
            rotasi_ket = st.text_input("Keterangan rotasi bahan")

            # --- BAGIAN III. PERSIAPAN, PENGOLAHAN DAN PENDINGINAN ---
            st.markdown("### 🍳 III. PERSIAPAN, PENGOLAHAN DAN PENDINGINAN")
            st.markdown("##### 1. Personal Hygiene Tim Persiapan")
            persiapan_sakit = st.selectbox("Tim Persiapan: Ada yang demam, batuk, diare, luka terbuka?", ["Ya", "Tidak"])
            persiapan_sakit_ket = st.text_input("Kalau Ya, sebutkan nama & keluhan (Persiapan)")
            persiapan_apd = st.selectbox("Tim Persiapan: Memakai APD lengkap?", ["Ya", "Tidak"])
            persiapan_ctps = st.selectbox("Tim Persiapan: Cuci tangan pakai sabun (CTPS)?", ["Ya", "Tidak"])

            st.markdown("##### 2. Persiapan")
            persiapan_sop = st.selectbox("Protein hewani ditata laksana sesuai SOP?", ["Ya", "Tidak"])
            persiapan_bau = st.selectbox("Terdapat bahan baku berbau tidak sedap / berlendir?", ["Ya", "Tidak"])
            persiapan_bau_ket = st.text_input("Kalau Ya, sebutkan bahan baku")
            persiapan_kendala = st.selectbox("Kendala dalam tahapan persiapan?", ["Ya", "Tidak"])
            persiapan_kendala_ket = st.text_input("Sebutkan kendala persiapan")

            st.markdown("##### 3. Menu Rawan Hari Ini")
            menu_ikan = st.selectbox("Ikan / seafood aman & tidak berbau amis?", ["Ya", "Tidak"])
            menu_ayam = st.selectbox("Ayam bersantan tidak didiamkan > 2 jam suhu ruang?", ["Ya", "Tidak"])
            menu_suwir = st.selectbox("Ayam diolah ulang pakai sarung tangan bersih?", ["Ya", "Tidak"])
            menu_telur = st.selectbox("Telur / telur dadar matang sempurna?", ["Ya", "Tidak"])
            menu_susu = st.selectbox("Susu / olahan susu sudah dipasteurisasi?", ["Ya", "Tidak"])

            st.markdown("##### 4. Personal Hygiene Tim Pengolahan")
            olah_sakit = st.selectbox("Tim Pengolahan: Ada yang demam, batuk, diare, luka?", ["Ya", "Tidak"])
            olah_sakit_ket = st.text_input("Kalau Ya, sebutkan nama & keluhan (Pengolahan)")
            olah_apd = st.selectbox("Tim Pengolahan: Memakai APD lengkap?", ["Ya", "Tidak"])
            olah_ctps = st.selectbox("Tim Pengolahan: Cuci tangan pakai sabun (CTPS)?", ["Ya", "Tidak"])

            st.markdown("##### 5. Proses Pengolahan Makanan")
            olah_matang = st.selectbox("Daging, ayam, ikan, telur dicek matang sempurna (tidak merah muda)?", ["Ya", "Tidak"])
            suhu_matang_val = st.text_input("Suhu matang (°C) & Jam", "75°C, jam ...")
            olah_sop = st.selectbox("Tata laksana pengolahan sesuai SOP?", ["Ya", "Tidak"])
            olah_kendala = st.selectbox("Kendala dalam tahapan pengolahan?", ["Ya", "Tidak"])
            olah_kendala_ket = st.text_input("Sebutkan kendala pengolahan")

            st.markdown("##### 6. Proses Pendinginan Makanan")
            pendinginan_ruang = st.selectbox("Ada area / ruang khusus steril untuk pendinginan makanan?", ["Ya", "Tidak"])
            pendinginan_ruang_ket = st.text_input("Kondisi ruang pendinginan")
            pendinginan_suhu = st.selectbox("Suhu makanan jadi sudah diukur (Panas >60°C, Dingin <-5°C)?", ["Ya", "Tidak"])
            suhu_ukur_val = st.text_input("Suhu makanan diukur (°C)", "65°C")
            nasi_suhu_ruang = st.selectbox("Nasi berada pada suhu ruang > 2 jam?", ["Ya", "Tidak"])
            durasi_nasi = st.text_input("Durasi suhu ruang nasi (jam)", "1 jam")
            pendinginan_kendala = st.selectbox("Kendala dalam tahapan pendinginan?", ["Ya", "Tidak"])

            # --- BAGIAN IV. PEMORSIAN DAN DISTRIBUSI ---
            st.markdown("### 🚚 IV. PEMORSIAN DAN DISTRIBUSI")
            st.markdown("##### 1. Proses Pemorsian")
            porsi_gizi = st.selectbox("Memenuhi standar gizi dan URT?", ["Ya", "Tidak"])
            porsi_gizi_ket = st.text_input("Kesesuaian porsi & URT")
            porsi_suhu = st.selectbox("Suhu makanan saat pemorsian diukur?", ["Ya", "Tidak"])
            suhu_porsi_val = st.text_input("Suhu saat pemorsian (°C)", "62°C")
            porsi_qc = st.selectbox("Quality control uji organoleptik sederhana?", ["Ya", "Tidak"])
            qc_oleh = st.text_input("Dilakukan oleh (Nama & Jam)", "Nama ... jam ...")
            qc_hasil = st.text_input("Hasil organoleptik")
            porsi_kendala = st.selectbox("Kendala dalam tahapan pemorsian?", ["Ya", "Tidak"])
            
            sampel_menu_simpan = st.selectbox("Penyimpanan 2 sampel menu hari ini (chiller & freezer)?", ["Ya", "Tidak"])
            
            st.markdown("##### Rincian Sisa Makanan Setelah Pemorsian")
            sisa_makanan_ada = st.selectbox("Terdapat sisa makanan setelah pemorsian?", ["Ya", "Tidak"])
            sisa_karbo = st.text_input("Sisa Karbohidrat (kg)", "0")
            sisa_hewani = st.text_input("Sisa Protein Hewani (kg)", "0")
            sisa_nabati = st.text_input("Sisa Protein Nabati (kg)", "0")
            sisa_sayur = st.text_input("Sisa Sayur (kg)", "0")
            sisa_buah = st.text_input("Sisa Buah (kg)", "0")

            st.markdown("##### 2. Alat & Tempat")
            alat_pisah = st.selectbox("Peralatan pengolahan dipakai terpisah (talenan, panci, pisau)?", ["Ya", "Tidak"])
            alat_bersih = st.selectbox("Meja pengolahan & alat masak bersih dan kering?", ["Ya", "Tidak"])
            sanitasi_fisik = st.selectbox("Lantai, saluran air, dan pipa tidak ada yang bocor/tergenang?", ["Ya", "Tidak"])

            st.markdown("##### 3. Proses Distribusi")
            jam_selesai_masak = st.text_input("Jam selesai masak", "10:00")
            jam_berangkat_dist = st.text_input("Jam pendistribusian (berangkat dari SPPG)", "10:30")
            jam_sampai_sekolah = st.text_input("Jam sampai di sekolah / posyandu", "11:15")
            jam_konsumsi = st.text_input("Jam konsumsi makanan (maksimal 4 jam)", "11:30")
            label_segel = st.selectbox("Label di ompreng terpasang & berfungsi sebagai segel?", ["Ya", "Tidak"])
            
            suhu_panas_dist = st.text_input("Suhu makanan panas saat dibagikan (>60°C)", "62°C")
            suhu_dingin_dist = st.text_input("Suhu makanan dingin saat dibagikan (<5°C)", "4°C")
            dist_kulkas = st.selectbox("Dipindah ke tempat/kulkas dingin jika tidak langsung dibagikan?", ["Ya", "Tidak"])
            dist_kendala = st.selectbox("Kendala dalam proses distribusi?", ["Ya", "Tidak"])
            dist_kendala_ket = st.text_input("Sebutkan kendala distribusi")

            # --- BAGIAN V. TEMUAN & KEPUTUSAN ---
            st.markdown("### 📝 V. TEMUAN & KEPUTUSAN")
            temuan = st.text_area("Temuan (Apabila ada)", placeholder="Tuliskan catatan khusus temuan...")
            keputusan_final = st.selectbox("Keputusan Final", [
                "GO — produksi dapat dimulai / dilanjutkan",
                "GO dengan catatan — lanjut, perbaikan segera (isi Temuan Khusus)",
                "NO-GO — eskalasi ke Dinkes / BGN sebelum masak / distribusi dilanjutkan"
            ])

            st.markdown("<br>", unsafe_allow_html=True)
            submitted_form = st.form_submit_button("🚀 Proses & Generate Laporan PDF Lengkap & Rinci", type="primary", use_container_width=True)

            if submitted_form:
                tgl_str = str(tanggal)
                sppg_clean = user_data[0].replace(" ", "_")
                filename = f"{sppg_clean}_cheklis_harian_{tgl_str}.pdf"
                
                doc = SimpleDocTemplate(filename, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
                styles = getSampleStyleSheet()
                
                title_style = ParagraphStyle(
                    'TitleStyle', parent=styles['Heading1'], fontSize=13, textColor=colors.whitesmoke, alignment=1, spaceAfter=4
                )
                section_style = ParagraphStyle(
                    'SectionStyle', parent=styles['Heading2'], fontSize=10, textColor=colors.whitesmoke, spaceBefore=4, spaceAfter=2, leftIndent=4
                )
                cell_style = ParagraphStyle(
                    'CellStyle', parent=styles['Normal'], fontSize=8.5, leading=10
                )
                cell_bold = ParagraphStyle(
                    'CellBold', parent=styles['Normal'], fontSize=8.5, leading=10, fontName='Helvetica-Bold'
                )

                story = []
                
                # Judul Utama Dokumen
                header_title_data = [[Paragraph("<b>CHECKLIST HARIAN — KOORDINASI ZOOM & MONITORING SPPG</b>", title_style)]]
                t_title = Table(header_title_data, colWidths=[550])
                t_title.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1f4e78')),
                    ('PADDING', (0,0), (-1,-1), 6),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ]))
                story.append(t_title)
                story.append(Spacer(1, 4))

                # Header Identitas SPPG & Tim
                meta_data = [
                    [Paragraph("<b>Nama SPPG:</b>", cell_bold), Paragraph(f"{user_data[0]}", cell_style), Paragraph("<b>Pengawas Keuangan:</b>", cell_bold), Paragraph(f"{pengawas_keuangan}", cell_style)],
                    [Paragraph("<b>Kepala SPPG:</b>", cell_bold), Paragraph(f"{user_data[2]}", cell_style), Paragraph("<b>Pengawas Gizi:</b>", cell_bold), Paragraph(f"{pengawas_gizi}", cell_style)],
                    [Paragraph("<b>Tanggal:</b>", cell_bold), Paragraph(f"{tgl_str}", cell_style), Paragraph("<b>Asisten Lapangan:</b>", cell_bold), Paragraph(f"{user_data[5]}", cell_style)],
                    [Paragraph("<b>Jam Mulai Zoom:</b>", cell_bold), Paragraph(f"{jam_zoom}", cell_style), Paragraph("<b>Chef:</b>", cell_bold), Paragraph(f"{user_data[7]}", cell_style)]
                ]
                t_meta = Table(meta_data, colWidths=[110, 165, 110, 165])
                t_meta.setStyle(TableStyle([
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('PADDING', (0,0), (-1,-1), 3),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ]))
                story.append(t_meta)
                story.append(Spacer(1, 6))

                def create_section_table(section_title, rows_data):
                    sec_header = [[Paragraph(f"<b>{section_title}</b>", section_style), ""]]
                    t_sec = Table(sec_header, colWidths=[550])
                    t_sec.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#2c3e50')),
                        ('PADDING', (0,0), (-1,-1), 3),
                    ]))
                    story.append(t_sec)
                    
                    formatted_rows = []
                    for r in rows_data:
                        formatted_rows.append([Paragraph(str(r[0]), cell_bold), Paragraph(str(r[1]), cell_style)])
                        
                    t_body = Table(formatted_rows, colWidths=[250, 300])
                    t_body.setStyle(TableStyle([
                        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                        ('PADDING', (0,0), (-1,-1), 3),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ]))
                    story.append(t_body)
                    story.append(Spacer(1, 6))

                # I. DATA UMUM
                data_umum_rows = [
                    ("PM Peserta Didik (Potensi vs Dilayani)", f"Potensi: {pm_didik_potensi} | Dilayani: {pm_didik_layani}"),
                    ("PM 3B (Potensi vs Dilayani)", f"Potensi: {pm_3b_potensi} | Dilayani: {pm_3b_layani}"),
                    ("Total Penerima Manfaat", f"Potensi: {total_pm_potensi} | Dilayani: {total_pm_layani}"),
                    ("Status Sertifikasi (SLHS | Halal | BNSP)", f"SLHS: {sertif_slhs} | Halal: {sertif_halal} | BNSP Chef: {sertif_bnsp}"),
                    ("Sumber Air Minum & Masak", f"Minum: {sumber_air_minum} | Masak: {sumber_air_masak}"),
                    ("pH Air Minum & Masak", f"Minum: {ph_air_minum} | Masak: {ph_air_masak}"),
                    ("Termometer Ruangan Berfungsi", f"Hasil: {termometer_ok} ({termometer_ket})"),
                    ("Suhu Ruangan & Kebersihan", f"Suhu: {suhu_ruang_val} | Bersih: {ruang_bersih_ok} - {ruang_bersih_ket}"),
                    ("Insect Killer Berfungsi", f"Hasil: {insect_ok} (Jumlah: {insect_jml})")
                ]
                create_section_table("I. DATA UMUM & AIR BERSIH", data_umum_rows)

                # II. PENERIMAAN & PENYIMPANAN BAHAN BAKU
                bahan_baku_rows = [
                    ("Karbohidrat (Jumlah | Kualitas | Jam | Penerima)", f"Jml: {k_karbo_jml} | Kual: {k_karbo_kual} | Jam: {k_karbo_jam} | Oleh: {k_karbo_nama}"),
                    ("Protein Hewani (Jumlah | Kualitas | Jam | Penerima)", f"Jml: {k_hewani_jml} | Kual: {k_hewani_kual} | Jam: {k_hewani_jam} | Oleh: {k_hewani_nama}"),
                    ("Protein Nabati (Jumlah | Kualitas | Jam | Penerima)", f"Jml: {k_nabati_jml} | Kual: {k_nabati_kual} | Jam: {k_nabati_jam} | Oleh: {k_nabati_nama}"),
                    ("Buah (Jumlah | Kualitas | Jam | Penerima)", f"Jml: {k_buah_jml} | Kual: {k_buah_kual} | Jam: {k_buah_jam} | Oleh: {k_buah_nama}"),
                    ("Sayur (Jumlah | Kualitas | Jam | Penerima)", f"Jml: {k_sayur_jml} | Kual: {k_sayur_kual} | Jam: {k_sayur_jam} | Oleh: {k_sayur_nama}"),
                    ("Suhu Bahan Baku Beku", f"Beku 1: {suhu_beku_1} ({nama_bahan_beku_1}) | Beku 2: {suhu_beku_2} ({nama_bahan_beku_2})"),
                    ("Suhu Chiller & Freezer Bahan Baku", f"Chiller: {suhu_chiller_bb} | Freezer: {suhu_freezer_bb}"),
                    ("Pencucian & Penyimpanan Tahu", f"Cuci Air Bersih: {pencucian_air} ({sumber_pencucian}) | Tahu di Chiller: {tahu_chiller} ({suhu_chiller_tahu})"),
                    ("Penerapan FIFO / FEFO", f"Sesuai FIFO/FEFO: {fifo_ok} - {rotasi_ket}")
                ]
                create_section_table("II. PENERIMAAN DAN PENYIMPANAN BAHAN BAKU", bahan_baku_rows)

                # III. PERSIAPAN, PENGOLAHAN DAN PENDINGINAN
                pengolahan_rows = [
                    ("Personal Hygiene Tim Persiapan", f"Sakit/Luka: {persiapan_sakit} ({persiapan_sakit_ket}) | APD: {persiapan_apd} | CTPS: {persiapan_ctps}"),
                    ("Tahapan Persiapan & Bahan Baku", f"SOP Hewani: {persiapan_sop} | Bau/Lendir: {persiapan_bau} ({persiapan_bau_ket}) | Kendala: {persiapan_kendala} ({persiapan_kendala_ket})"),
                    ("Menu Rawan Hari Ini", f"Ikan: {menu_ikan} | Ayam Santan: {menu_ayam} | Suwir: {menu_suwir} | Telur: {menu_telur} | Susu: {menu_susu}"),
                    ("Personal Hygiene Tim Pengolahan", f"Sakit/Luka: {olah_sakit} ({olah_sakit_ket}) | APD: {olah_apd} | CTPS: {olah_ctps}"),
                    ("Proses Pengolahan Makanan", f"Matang Sempurna: {olah_matang} | Suhu Matang: {suhu_matang_val} | SOP: {olah_sop} | Kendala: {olah_kendala} ({olah_kendala_ket})"),
                    ("Proses Pendinginan Makanan", f"Ruang Steril: {pendinginan_ruang} ({pendinginan_ruang_ket}) | Suhu Pendinginan: {suhu_ukur_val} | Nasi >2 Jam: {nasi_suhu_ruang} ({durasi_nasi})")
                ]
                create_section_table("III. PERSIAPAN, PENGOLAHAN DAN PENDINGINAN", pengolahan_rows)

                # IV. PEMORSIAN DAN DISTRIBUSI (DENGAN RINCIAN SISA MAKANAN LENGKAP)
                distribusi_rows = [
                    ("Standar Gizi & URT Pemorsian", f"Memenuhi: {porsi_gizi} ({porsi_gizi_ket}) | Suhu: {suhu_porsi_val}"),
                    ("Quality Control Pemorsian", f"Organoleptik: {porsi_qc} oleh {qc_oleh} ({qc_hasil}) | Kendala: {porsi_kendala}"),
                    ("Penyimpanan Sampel Menu Harian", f"Simpan 2 Sampel (Chiller & Freezer): {sampel_menu_simpan}"),
                    ("Status Terdapat Sisa Makanan", f"Ada Sisa Makanan: {sisa_makanan_ada}"),
                    ("➡️ Rincian Sisa Karbohidrat", f"{sisa_karbo} kg"),
                    ("➡️ Rincian Sisa Protein Hewani", f"{sisa_hewani} kg"),
                    ("➡️ Rincian Sisa Protein Nabati", f"{sisa_nabati} kg"),
                    ("➡️ Rincian Sisa Sayur", f"{sisa_sayur} kg"),
                    ("➡️ Rincian Sisa Buah", f"{sisa_buah} kg"),
                    ("Alat, Tempat & Sanitasi", f"Peralatan Pisah: {alat_pisah} | Meja Bersih: {alat_bersih} | Sanitasi Air: {sanitasi_fisik}"),
                    ("Waktu Distribusi", f"Selesai Masak: {jam_selesai_masak} | Berangkat SPPG: {jam_berangkat_dist} | Sampai Sekolah: {jam_sampai_sekolah} | Konsumsi: {jam_konsumsi}"),
                    ("Suhu & Segel Distribusi", f"Label Segel: {label_segel} | Suhu Panas: {suhu_panas_dist} | Suhu Dingin: {suhu_dingin_dist} | Pindah Kulkas: {dist_kulkas} | Kendala: {dist_kendala} ({dist_kendala_ket})")
                ]
                create_section_table("IV. PEMORSIAN DAN DISTRIBUSI", distribusi_rows)

                # V. TEMUAN & KEPUTUSAN FINAL
                keputusan_rows = [
                    ("Temuan Khusus", f"{temuan if temuan else 'Tidak ada temuan khusus.'}"),
                    ("Keputusan Final", f"<b>{keputusan_final}</b>")
                ]
                create_section_table("V. TEMUAN & KEPUTUSAN FINAL", keputusan_rows)

                doc.build(story)
                
                st.session_state['pdf_ready'] = True
                st.session_state['pdf_filename'] = filename

        # --- TOMBOL DOWNLOAD DI LUAR FORM ---
        if st.session_state['pdf_ready']:
            st.success("PDF Lengkap & Rinci (Termasuk Sisa Makanan) berhasil digenerate!")
            if os.path.exists(st.session_state['pdf_filename']):
                with open(st.session_state['pdf_filename'], "rb") as pdf_file:
                    st.download_button(
                        label="📥 Unduh File PDF SPPG Sempurna",
                        data=pdf_file,
                        file_name=st.session_state['pdf_filename'],
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )
