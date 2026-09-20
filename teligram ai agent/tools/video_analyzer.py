import cv2
import tempfile
import os

class VideoAnalyzerTool:
    """Extracts key frames from video files for multimodal visual reasoning."""
    
    @staticmethod
    def extract_key_frames(video_bytes: bytes, max_frames: int = 4) -> list[bytes]:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(video_bytes)
            temp_path = f.name
            
        frames = []
        try:
            cap = cv2.VideoCapture(temp_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames <= 0:
                return []
                
            step = max(1, total_frames // (max_frames + 1))
            
            for i in range(1, max_frames + 1):
                frame_idx = min(i * step, total_frames - 1)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Resize to max 640px width for fast AI token processing
                    h, w = frame.shape[:2]
                    if w > 640:
                        new_h = int(h * (640 / w))
                        frame = cv2.resize(frame, (640, new_h))
                        
                    # Encode to JPEG
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    frames.append(buffer.tobytes())
                    
            cap.release()
        except Exception:
            pass
        finally:
            try:
                os.remove(temp_path)
            except Exception:
                pass
                
        return frames
