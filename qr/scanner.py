import cv2
import queue
import av
from pyzbar.pyzbar import decode
from streamlit_webrtc import VideoProcessorBase, RTCConfiguration
from database.connection import SessionLocal
from attendance.recorder import record_attendance

# =====================================================================
# 1. KONFIGURASI STUN SERVER (SOLUSI FIX ERROR TURN/STUN TIMEOUT)
# =====================================================================
# Berfungsi sebagai penghubung agar server Streamlit Cloud dan browser
# perangkat (mahasiswa/admin) bisa saling bertukar data video/kamera.
RTC_CONFIGURATION = RTCConfiguration(
    {
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]},
            {"urls": ["stun:stun2.l.google.com:19302"]},
            {"urls": ["stun:stun3.l.google.com:19302"]},
            {"urls": ["stun:stun4.l.google.com:19302"]}
        ]
    }
)

# =====================================================================
# 2. CLASS PROCESSOR KAMERA (BACKGROUND THREAD)
# =====================================================================
class QRScannerTransformer(VideoProcessorBase):
    """Processor video untuk mendeteksi QR Code dari stream kamera WebRTC."""

    def __init__(self, session_id=None):
        # Tempat menampung hasil scan sementara sebelum ditarik ke UI Streamlit
        self.result_queue: queue.Queue = queue.Queue(maxsize=10)
        # Pengaman (Debounce) agar satu QR tidak ter-scan berkali-kali dalam 1 detik
        self._last_decoded: str = None
        self.session_id = session_id

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        """Deteksi QR dari setiap frame video, rekam otomatis ke DB, dan masukkan notifikasi ke queue."""
        # 1. Konversi frame video mentah ke format array gambar OpenCV (BGR)
        img = frame.to_ndarray(format="bgr24")
        
        # 2. Deteksi apakah ada QR Code di dalam frame gambar
        decoded_objs = decode(img)
        
        for obj in decoded_objs:
            data = obj.data.decode("utf-8")
            
            # Jika QR ini adalah QR baru yang discan (bukan QR yang sama di frame sebelumnya)
            if data != self._last_decoded:
                self._last_decoded = data
                
                # Proses absensi LANGSUNG ke database dari thread kamera (Background)
                if self.session_id is not None:
                    db = SessionLocal()
                    try:
                        # Eksekusi fungsi pencatatan blockchain/database absensi
                        success, msg = record_attendance(db, data, self.session_id)
                        
                        # Kirim hasil eksekusi ke antrean (queue) UI Streamlit
                        if not self.result_queue.full():
                            self.result_queue.put_nowait((data, success, msg))
                    except Exception as e:
                        print(f"Error background recording: {e}")
                        import traceback
                        traceback.print_exc()
                        
                        # Jika crash, kirim pesan error sistem agar Admin tahu lewat UI Toast
                        if not self.result_queue.full():
                            self.result_queue.put_nowait((data, False, f"SYSTEM ERROR: {str(e)}"))
                    finally:
                        # Selalu tutup koneksi database database pooler Supabase
                        db.close()

            # 3. Efek Visual: Gambar kotak hijau tepat di sekeliling QR Code yang terdeteksi
            cv2.rectangle(
                img,
                (obj.rect.left, obj.rect.top),
                (obj.rect.left + obj.rect.width, obj.rect.top + obj.rect.height),
                (0, 255, 0), 3
            )
            # Beri tulisan penanda di atas kotak hijau tersebut
            cv2.putText(
                img, "QR TERDETEKSI", (obj.rect.left, obj.rect.top - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
            )
            
        # Kembalikan frame gambar yang sudah dimodifikasi (ada kotak hijau) ke layar browser
        return av.VideoFrame.from_ndarray(img, format="bgr24")
