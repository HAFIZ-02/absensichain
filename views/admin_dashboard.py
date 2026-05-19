import queue
import streamlit as st
import pandas as pd
from database.connection import SessionLocal
from database.models import User, Student, Session, Attendance, QRCode
from qr.generator import generate_student_qr
from attendance.session_manager import close_session
from components.blockchain_viewer import render_blockchain
from streamlit_webrtc import webrtc_streamer
from qr.scanner import QRScannerTransformer
from attendance.recorder import record_attendance
from qr.validator import decrypt_qr


def _color_status(val: str) -> str:
    """Kembalikan CSS warna sesuai status kehadiran."""
    if val == "HADIR":
        return "background-color: #d4edda; color: #155724; font-weight:bold"
    elif val == "TERLAMBAT":
        return "background-color: #fff3cd; color: #856404; font-weight:bold"
    else:
        return "background-color: #f8d7da; color: #721c24; font-weight:bold"


def _render_rekap_sesi(db, session_obj):
    """Render tabel rekap kehadiran untuk satu sesi dari database."""
    attendances = (
        db.query(Attendance)
        .filter(Attendance.session_id == session_obj.id)
        .all()
    )
    if not attendances:
        st.info("Tidak ada data kehadiran untuk sesi ini.")
        return

    total = len(attendances)
    hadir_n = sum(1 for a in attendances if a.status == "hadir")
    terlambat_n = sum(1 for a in attendances if a.status == "terlambat")
    absen_n = sum(1 for a in attendances if a.status == "absen")

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("👥 Total Siswa", total)
    mc2.metric("✅ Hadir", hadir_n)
    mc3.metric("🕐 Terlambat", terlambat_n)
    mc4.metric("❌ Absen", absen_n)

    rows = []
    for a in attendances:
        student = db.query(Student).filter_by(id=a.student_id).first()
        rows.append({
            "Nama": student.nama_lengkap if student else "-",
            "NIS": student.nis if student else "-",
            "Kelas": student.kelas if student else "-",
            "Status": a.status.upper(),
            "Waktu Scan": a.scan_time.strftime("%H:%M:%S") if a.scan_time else "-",
            "Block #": str(a.block_index) if a.block_index else "-",
        })

    df = pd.DataFrame(rows).sort_values("Status")
    styled = df.style.applymap(_color_status, subset=["Status"])
    st.dataframe(styled, use_container_width=True, hide_index=True)


def render():
    """Render halaman dashboard admin dengan manajemen sesi dan live scan QR."""
    st.title("🛡️ Admin Dashboard - AbsenChain")
    db = SessionLocal()
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "✅ Konfirmasi Akun",
        "📡 Live Sesi & Kamera",
        "📊 Rekap Absensi",
        "🧑‍🎓 Data Siswa",
        "🔗 Validasi Ledger",
    ])

    # ─── TAB 1: Konfirmasi akun siswa ─────────────────────────────────────
    with tab1:
        st.subheader("Persetujuan Akun Siswa Baru")
        pendings = db.query(User).filter(
            User.status.ilike('pending'), User.role == 'siswa'
        ).all()
        if not pendings:
            st.info("Tidak ada siswa yang menunggu persetujuan.")
        for p in pendings:
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(
                f"**{p.student.nama_lengkap}** "
                f"(NIS: {p.student.nis} — Kelas {p.student.kelas})"
            )
            if col2.button("Setujui & Generate QR", key=f"app_{p.id}"):
                p.status = 'active'
                enc_payload, qr_b64 = generate_student_qr(
                    p.student.id, p.student.nis, p.student.nama_lengkap
                )
                db.add(QRCode(
                    student_id=p.student.id,
                    payload_encrypted=enc_payload,
                    qr_image_b64=qr_b64
                ))
                db.commit()
                st.rerun()
            if col3.button("Tolak", key=f"rej_{p.id}"):
                p.status = 'rejected'
                db.commit()
                st.rerun()

    # ─── TAB 2: Live Sesi & Kamera ────────────────────────────────────────
    with tab2:
        colA, colB = st.columns([1, 1])

        with colA:
            st.subheader("Buat Sesi Baru")
            with st.form("new_session"):
                mapel = st.text_input("Mata Pelajaran")
                kelas = st.selectbox("Kelas", ["10A", "10B", "11A", "11B", "12A", "12B"])
                tgl = st.date_input("Tanggal")
                jm = st.time_input("Jam Mulai").strftime("%H:%M")
                js = st.time_input("Jam Selesai").strftime("%H:%M")
                btm = st.number_input("Batas Toleransi Terlambat (Menit)", value=15, min_value=0)
                if st.form_submit_button("🚀 Mulai Sesi Absensi"):
                    sess = Session(
                        mapel=mapel, kelas=kelas, tanggal=tgl,
                        jam_mulai=jm, jam_selesai=js,
                        batas_terlambat_menit=int(btm),
                        created_by=st.session_state.user_id
                    )
                    db.add(sess)
                    db.commit()
                    st.success(f"✅ Sesi **{mapel}** kelas {kelas} berhasil dibuat!")
                    st.rerun()

        with colB:
            st.subheader("Sesi Berjalan (Live Scan)")
            active_sessions = db.query(Session).filter_by(status='open').all()

            if not active_sessions:
                st.info("Tidak ada sesi yang sedang berlangsung.")

            for s in active_sessions:
                with st.container(border=True):
                    st.warning(f"📋 **{s.mapel}** — Kelas {s.kelas}")
                    st.caption(f"⏰ {s.jam_mulai} — {s.jam_selesai} | Toleransi: {s.batas_terlambat_menit} menit")

                    import functools
                    import streamlit.components.v1 as components

                    # ── Kamera WebRTC ──────────────────────────────────────
                    ctx = webrtc_streamer(
                        key=f"qr_cam_{s.id}",
                        video_processor_factory=functools.partial(QRScannerTransformer, session_id=s.id),
                        media_stream_constraints={"video": True, "audio": False},
                        async_processing=True,
                    )

                    log_key = f"scan_log_{s.id}"
                    if log_key not in st.session_state:
                        st.session_state[log_key] = []

                    # 1. BACA QUEUE (Otomatis ter-refresh oleh script di bawah)
                    if ctx.video_processor:
                        try:
                            while True:
                                qr_raw, success, msg = ctx.video_processor.result_queue.get_nowait()
                                
                                from qr.validator import decrypt_qr
                                payload = decrypt_qr(qr_raw)
                                nama = payload.get("nama", "Tidak dikenal") if payload else "Tidak dikenal"
                                
                                st.session_state[log_key].insert(0, {
                                    "nama": nama, "success": success, "msg": msg
                                })
                                # Popup notifikasi instan
                                if success:
                                    st.toast(f"✅ {nama} — HADIR/TERLAMBAT", icon="✅")
                                else:
                                    st.toast(f"❌ {nama} — {msg[:60]}", icon="❌")
                        except queue.Empty:
                            pass

                    # 2. AUTO-REFRESH HACK (Menggantikan Tombol Sinkronisasi)
                    # Tombol ini akan disembunyikan dan ditekan otomatis oleh Javascript setiap 2 detik
                    st.button("♻️Sync", key=f"auto_sync_{s.id}")
                    components.html(
                        f"""
                        <script>
                        var doc = window.parent.document;
                        var btns = doc.querySelectorAll('button');
                        for(var i=0; i<btns.length; i++) {{
                            if(btns[i].innerText.includes('♻️Sync')) {{
                                btns[i].style.display = 'none'; // Sembunyikan tombol
                                // Auto-klik setiap 2 detik agar Streamlit me-refresh antrean (queue) UI
                                setInterval((function(btn) {{ return function() {{ btn.click(); }} }})(btns[i]), 2000);
                            }}
                        }}
                        </script>
                        """, height=0, width=0
                    )

                    # 3. Tombol Tutup Sesi
                    if st.button("🔒 Tutup Sesi & Rekap Absen", key=f"close_{s.id}",
                                 type="primary", use_container_width=True):
                        close_session(db, s.id)
                        st.success("✅ Sesi ditutup. Lihat rekap di tab **Rekap Absensi**.")
                        st.rerun()

                    # 4. Tampilkan daftar hadir live
                    attended = db.query(Attendance).filter_by(session_id=s.id).all()
                    if attended:
                        st.markdown(f"**Sudah Scan ({len(attended)} siswa):**")
                        for a in attended:
                            student = db.query(Student).filter_by(id=a.student_id).first()
                            icon = "✅" if a.status == "hadir" else "🕐" if a.status == "terlambat" else "❌"
                            st.write(f"{icon} {student.nama_lengkap} — **{a.status.upper()}**")

    # ─── TAB 3: Rekap Absensi (dari DB) ───────────────────────────────────
    with tab3:
        st.subheader("📊 Rekap Absensi Per Sesi")

        all_sessions = db.query(Session).order_by(Session.id.desc()).all()
        if not all_sessions:
            st.info("Belum ada sesi yang pernah dibuat.")
        else:
            # Selector sesi
            sesi_options = {
                f"[{s.status.upper()}] {s.mapel} — Kelas {s.kelas} ({str(s.tanggal)[:10]})": s
                for s in all_sessions
            }
            selected_label = st.selectbox(
                "Pilih Sesi untuk Melihat Rekap:",
                options=list(sesi_options.keys()),
                key="rekap_selector"
            )
            selected_sess = sesi_options[selected_label]

            st.markdown(
                f"**Mata Pelajaran:** {selected_sess.mapel} &nbsp;|&nbsp; "
                f"**Kelas:** {selected_sess.kelas} &nbsp;|&nbsp; "
                f"**Tanggal:** {str(selected_sess.tanggal)[:10]} &nbsp;|&nbsp; "
                f"**Jam:** {selected_sess.jam_mulai} – {selected_sess.jam_selesai}"
            )

            status_badge = "🟢 BERJALAN" if selected_sess.status == "open" else "🔴 DITUTUP"
            st.markdown(f"**Status Sesi:** {status_badge}")
            st.divider()

            _render_rekap_sesi(db, selected_sess)

    # ─── TAB 4: Data Semua Siswa ──────────────────────────────────────────
    with tab4:
        st.subheader("Daftar Seluruh Siswa")
        stds = db.query(Student).all()
        if stds:
            df = pd.DataFrame([{
                "ID": s.id,
                "Nama": s.nama_lengkap,
                "NIS": s.nis,
                "Kelas": s.kelas,
                "Jenis Kelamin": s.jenis_kelamin,
                "Status Akun": s.user.status.upper(),
            } for s in stds])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data siswa terdaftar.")

    # ─── TAB 5: Validasi Ledger Blockchain ────────────────────────────────
    with tab5:
        render_blockchain(db)

    db.close()
