import streamlit as st
import sqlite3
import os
import psycopg2
from urllib.parse import urlparse
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

# --- PENGATURAN HALAMAN ---
st.set_page_config(
    page_title="SPPG Monitoring & Checklist",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- KONEKSI DATABASE (SUPABASE / POSTGRESQL & SQLITE) ---
def get_db_connection():
    if "DATABASE_URL" in st.secrets:
        # Coba langsung connect pakai string URI rahasia dari Secrets
        try:
            return psycopg2.connect(st.secrets["DATABASE_URL"])
        except Exception:
            # Fallback jika format URL terpisah
            url = urlparse(st.secrets["DATABASE_URL"])
            return psycopg2.connect(
                database=url.path[1:],
                user=url.username,
                password=url.password,
                host=url.hostname,
                port=url.port or 5432
            )
    else:
        return sqlite3.connect('sppg_streamlit.db', check_same_thread=False)
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    is_postgres = "DATABASE_URL" in st.secrets
    
    if is_postgres:
        # Tabel Users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
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
        # Tabel Checklist / Laporan Harian
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS laporan (
                id SERIAL PRIMARY KEY,
                username TEXT,
                tanggal TEXT,
                sesi TEXT,
                menu_makanan TEXT,
                porsi_rencana INTEGER,
                porsi_terdistribusi INTEGER,
                sisa_makanan_kg REAL,
                catatan TEXT
            )
        ''')
    else:
        # Tabel Users SQLite
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
        # Tabel Laporan SQLite
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS laporan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                tanggal TEXT,
                sesi TEXT,
                menu_makanan TEXT,
                porsi_rencana INTEGER,
                porsi_terdistribusi INTEGER,
                sisa_makanan_kg REAL,
                catatan TEXT
            )
        ''')
    conn.commit()
    conn.close()

init_db()

# --- MANAJEMEN SESI LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""

# --- HALAMAN AUTENTIKASI (LOGIN & REGISTER) ---
if not st.session_state["logged_in"]:
    st.title("🍳 SPPG Monitoring - Badan Gizi Nasional")
    st.subheader("Silakan Login atau Daftar Akun Dapur SPPG")
    
    tab_login, tab_register = st.tabs(["Login", "Daftar Akun Baru"])
    
    with tab_login:
        st.markdown("### Masuk Aplikasi")
        l_user = st.text_input("Username", key="login_user")
        l_pass = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login", type="primary"):
            if l_user and l_pass:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s" if "DATABASE_URL" in st.secrets else "SELECT * FROM users WHERE username = ? AND password = ?", (l_user, l_pass))
                user = cursor.fetchone()
                conn.close()
                
                if user:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = l_user
                    st.success("Login Berhasil! Memuat aplikasi...")
                    st.rerun()
                else:
                    st.error("Username atau Password salah!")
            else:
                st.warning("Mohon isi username dan password.")
                
    with tab_register:
        st.markdown("### Pendaftaran Akun Dapur SPPG Baru")
        r_user = st.text_input("Buat Username", key="reg_user")
        r_pass = st.text_input("Buat Password", type="password", key="reg_pass")
        
        st.markdown("---")
        st.markdown("**Profil Dapur & Petugas SPPG (Badan Gizi Nasional):**")
        r_nama_sppg = st.text_input("Nama SPPG (Contoh: SPPG Paseh Cigentur)")
        r_id_sppg = st.text_input("ID SPPG")
        r_nama_kasppg = st.text_input("Nama Kepala SPPG")
        r_nama_plok = st.text_input("Nama PLOK")
        r_nama_plog = st.text_input("Nama PLOG")
        r_asist = st.text_input("Asisten Lapangan")
        r_admin = st.text_input("Admin Gudang")
        r_chef = st.text_input("Chef / Kepala Dapur")
        
        if st.button("Daftar Sekarang", type="primary"):
            if r_user and r_pass and r_nama_sppg:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    if "DATABASE_URL" in st.secrets:
                        cursor.execute('''
                            INSERT INTO users (username, password, nama_sppg, id_sppg, nama_kasppg, nama_plok, nama_plog, asisten_lapangan, admin_gudang, chef)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ''', (r_user, r_pass, r_nama_sppg, r_id_sppg, r_nama_kasppg, r_nama_plok, r_nama_plog, r_asist, r_admin, r_chef))
                    else:
                        cursor.execute('''
                            INSERT INTO users (username, password, nama_sppg, id_sppg, nama_kasppg, nama_plok, nama_plog, asisten_lapangan, admin_gudang, chef)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (r_user, r_pass, r_nama_sppg, r_id_sppg, r_nama_kasppg, r_nama_plok, r_nama_plog, r_asist, r_admin, r_chef))
                    conn.commit()
                    conn.close()
                    st.success("Akun berhasil didaftarkan! Silakan pindah ke tab Login.")
                except Exception as e:
                    st.error(f"Pendaftaran gagal (Username mungkin sudah terpakai): {e}")
            else:
                st.warning("Mohon lengkapi Minimal Username, Password, dan Nama SPPG.")

else:
    # --- AMBIL DATA PROFIL USER YANG SEDANG LOGIN ---
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nama_sppg, id_sppg, nama_kasppg, nama_plok, nama_plog, asisten_lapangan, admin_gudang, chef FROM users WHERE username = %s" if "DATABASE_URL" in st.secrets else "SELECT nama_sppg, id_sppg, nama_kasppg, nama_plok, nama_plog, asisten_lapangan, admin_gudang, chef FROM users WHERE username = ?", (st.session_state["username"],))
    user_data = cursor.fetchone()
    conn.close()
    
    profil = {
        "nama_sppg": user_data[0] if user_data and user_data[0] else "SPPG Badan Gizi Nasional",
        "id_sppg": user_data[1] if user_data and user_data[1] else "-",
        "nama_kasppg": user_data[2] if user_data and user_data[2] else "-",
        "nama_plok": user_data[3] if user_data and user_data[3] else "-",
        "nama_plog": user_data[4] if user_data and user_data[4] else "-",
        "asisten_lapangan": user_data[5] if user_data and user_data[5] else "-",
        "admin_gudang": user_data[6] if user_data and user_data[6] else "-",
        "chef": user_data[7] if user_data and user_data[7] else "-"
    }

    # --- SIDEBAR NAVIGASI & INFO ---
    st.sidebar.title("Panel SPPG 🍳")
    st.sidebar.write(f"Login sebagai: **{st.session_state['username']}**")
    st.sidebar.info(f"📍 **{profil['nama_sppg']}**\n\nID: {profil['id_sppg']}")
    
    menu = st.sidebar.radio("Menu Navigasi", ["Form Checklist & Operasional", "Riwayat & Cetak PDF"])
    
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.rerun()

    # --- HALAMAN 1: FORM CHECKLIST & OPERASIONAL ---
    if menu == "Form Checklist & Operasional":
        st.title("📋 Daily Checklist & Monitoring Dapur SPPG")
        st.write("Badan Gizi Nasional - Program Pemenuhan Gizi Masyarakat")
        
        with st.form("form_checklist"):
            col1, col2 = st.columns(2)
            with col1:
                tanggal = st.date_input("Tanggal Operasional", datetime.today())
                sesi = st.selectbox("Sesi Distribusi Makanan", ["Sesi 1 (Pagi)", "Sesi 2 (Siang)", "Sesi 3 (Sore)"])
            with col2:
                menu_makanan = st.text_input("Menu Makanan Hari Ini", placeholder="Contoh: Nasi, Ayam Goreng, Sayur Sop, Buah Pisang")
            
            st.markdown("---")
            st.subheader("📊 Statistik Distribusi & Food Waste (Sisa Makanan)")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                porsi_rencana = st.number_input("Rencana Jumlah Porsi", min_value=0, value=500)
            with c2:
                porsi_terdistribusi = st.number_input("Porsi Berhasil Didistribusikan", min_value=0, value=490)
            with c3:
                sisa_makanan_kg = st.number_input("Total Sisa Makanan / Food Waste (Kg)", min_value=0.0, format="%.2f", value=2.5)
                
            st.markdown("---")
            catatan = st.text_area("Catatan Evaluasi / Kendala Dapur", placeholder="Tuliskan catatan kebersihan, kendala logistik, atau hal penting lainnya...")
            
            submitted = st.form_submit_button("Simpan Laporan Harian", type="primary")
            
            if submitted:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    if "DATABASE_URL" in st.secrets:
                        cursor.execute('''
                            INSERT INTO laporan (username, tanggal, sesi, menu_makanan, porsi_rencana, porsi_terdistribusi, sisa_makanan_kg, catatan)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ''', (st.session_state["username"], str(tanggal), sesi, menu_makanan, porsi_rencana, porsi_terdistribusi, sisa_makanan_kg, catatan))
                    else:
                        cursor.execute('''
                            INSERT INTO laporan (username, tanggal, sesi, menu_makanan, porsi_rencana, porsi_terdistribusi, sisa_makanan_kg, catatan)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (st.session_state["username"], str(tanggal), sesi, menu_makanan, porsi_rencana, porsi_terdistribusi, sisa_makanan_kg, catatan))
                    conn.commit()
                    conn.close()
                    st.success("Laporan operasional SPPG berhasil disimpan ke database!")
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat menyimpan: {e}")

    # --- HALAMAN 2: RIWAYAT & CETAK PDF ---
    elif menu == "Riwayat & Cetak PDF":
        st.title("📁 Riwayat Laporan & Cetak Laporan PDF")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, tanggal, sesi, menu_makanan, porsi_rencana, porsi_terdistribusi, sisa_makanan_kg, catatan FROM laporan WHERE username = %s ORDER BY id DESC" if "DATABASE_URL" in st.secrets else "SELECT id, tanggal, sesi, menu_makanan, porsi_rencana, porsi_terdistribusi, sisa_makanan_kg, catatan FROM laporan WHERE username = ? ORDER BY id DESC", (st.session_state["username"],))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            st.info("Belum ada data laporan yang tersimpan. Silakan isi form di menu sebelah terlebih dahulu.")
        else:
            for row in rows:
                rep_id, r_tgl, r_sesi, r_menu, r_rencana, r_dist, r_sisa, r_cat = row
                
                with st.expander(f"📅 [{r_tgl}] - {r_sesi} | Menu: {r_menu}"):
                    st.write(f"**Rencana Porsi:** {r_rencana} | **Terdistribusi:** {r_dist} | **Sisa Makanan:** {r_sisa} Kg")
                    st.write(f"**Catatan:** {r_cat if r_cat else '-'}")
                    
                    # Tombol Generate PDF untuk laporan tertentu
                    if st.button(f"📥 Unduh Laporan PDF (ID: {rep_id})", key=f"pdf_{rep_id}"):
                        buffer = io.BytesIO()
                        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
                        story = []
                        styles = getSampleStyleSheet()
                        
                        title_style = ParagraphStyle(
                            'TitleStyle',
                            parent=styles['Heading1'],
                            fontSize=16,
                            alignment=1,
                            textColor=colors.HexColor("#1b4332")
                        )
                        subtitle_style = ParagraphStyle(
                            'SubTitleStyle',
                            parent=styles['Normal'],
                            fontSize=10,
                            alignment=1,
                            textColor=colors.HexColor("#555555")
                        )
                        
                        story.append(Paragraph("LAPORAN HARIAN OPERASIONAL SPPG", title_style))
                        story.append(Paragraph("BADAN GIZI NASIONAL", subtitle_style))
                        story.append(Spacer(1, 15))
                        
                        # Info Dapur
                        info_data = [
                            [Paragraph(f"<b>Nama SPPG:</b> {profil['nama_sppg']}"), Paragraph(f"<b>ID SPPG:</b> {profil['id_sppg']}")],
                            [Paragraph(f"<b>Tanggal:</b> {r_tgl}"), Paragraph(f"<b>Sesi:</b> {r_sesi}")],
                            [Paragraph(f"<b>Kepala SPPG:</b> {profil['nama_kasppg']}"), Paragraph(f"<b>Chef/Kordapur:</b> {profil['chef']}")]
                        ]
                        t_info = Table(info_data, colWidths=[250, 250])
                        t_info.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8f9fa")),
                            ('PADDING', (0,0), (-1,-1), 6),
                            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#dcdcdc")),
                        ]))
                        story.append(t_info)
                        story.append(Spacer(1, 15))
                        
                        # Detail Menu & Distribusi
                        story.append(Paragraph("<b>Detail Menu & Distribusi Makanan</b>", styles['Heading3']))
                        menu_data = [
                            ["Menu Makanan", r_menu],
                            ["Rencana Porsi", str(r_rencana)],
                            ["Porsi Terdistribusi", str(r_dist)],
                            ["Sisa Makanan (Food Waste)", f"{r_sisa} Kg"],
                            ["Catatan Evaluasi", r_cat if r_cat else "-"]
                        ]
                        t_menu = Table(menu_data, colWidths=[150, 350])
                        t_menu.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#e9ecef")),
                            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
                            ('PADDING', (0,0), (-1,-1), 6),
                        ]))
                        story.append(t_menu)
                        story.append(Spacer(1, 20))
                        
                        # Tanda Tangan
                        story.append(Paragraph("<b>Tim Penanggung Jawab SPPG:</b>", styles['Heading3']))
                        ttd_data = [
                            ["Kepala SPPG", "PLOK", "PLOG"],
                            [profil['nama_kasppg'], profil['nama_plok'], profil['nama_plog']],
                            ["\n\n( .................................... )", "\n\n( .................................... )", "\n\n( .................................... )"]
                        ]
                        t_ttd = Table(ttd_data, colWidths=[165, 165, 165])
                        t_ttd.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e9ecef")),
                            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cccccc")),
                            ('PADDING', (0,0), (-1,-1), 5),
                        ]))
                        story.append(t_ttd)
                        
                        doc.build(story)
                        pdf_data = buffer.getvalue()
                        buffer.close()
                        
                        st.download_button(
                            label=f"📥 Download PDF Sekarang (ID: {rep_id})",
                            data=pdf_data,
                            file_name=f"Laporan_SPPG_{r_tgl}_{r_sesi.replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            key=f"dl_btn_{rep_id}"
                        )
