import cv2
import queue
import av
from pyzbar.pyzbar import decode
from streamlit_webrtc import VideoProcessorBase
from database.connection import SessionLocal
from attendance.recorder import record_attendance


class QRScannerTransformer(VideoProcessorBase):
    """Processor video untuk mendeteksi QR Code dari stream kamera WebRTC."""

    def __init__(self, session_id=None):
        self.result_queue: queue.Queue = queue.Queue(maxsize=10)
        self._last_decoded: str = None
        self.session_id = session_id

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        """Deteksi QR dari setiap frame video, rekam otomatis ke DB, dan masukkan notifikasi ke queue."""
        img = frame.to_ndarray(format="bgr24")
        decoded_objs = decode(img)
        for obj in decoded_objs:
            data = obj.data.decode("utf-8")
            
            # Jika QR ini adalah QR baru yang discan
            if data != self._last_decoded:
                self._last_decoded = data
                
                # Proses absensi LANGSUNG ke database dari thread kamera (Background)
                # Sehingga TIDAK perlu menunggu tombol sinkronisasi ditekan
                if self.session_id is not None:
                    db = SessionLocal()
                    try:
                        success, msg = record_attendance(db, data, self.session_id)
                        if not self.result_queue.full():
                            self.result_queue.put_nowait((data, success, msg))
                    except Exception as e:
                        print(f"Error background recording: {e}")
                        import traceback
                        traceback.print_exc()
                        if not self.result_queue.full():
                            # Kirim error ke Streamlit UI agar muncul di Toast!
                            self.result_queue.put_nowait((data, False, f"SYSTEM ERROR: {str(e)}"))
                    finally:
                        db.close()

            # Gambar kotak hijau di sekitar QR untuk visual feedback
            cv2.rectangle(
                img,
                (obj.rect.left, obj.rect.top),
                (obj.rect.left + obj.rect.width, obj.rect.top + obj.rect.height),
                (0, 255, 0), 3
            )
            cv2.putText(
                img, "QR TERDETEKSI", (obj.rect.left, obj.rect.top - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
            )
        return av.VideoFrame.from_ndarray(img, format="bgr24")
