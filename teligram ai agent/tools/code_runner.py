import subprocess
import sys
import tempfile
import os

class CodeRunnerTool:
    """Executes code snippets safely in an isolated process and captures output."""
    
    @staticmethod
    def run_python(code: str, timeout: int = 10) -> str:
        # Prevent dangerous OS calls
        dangerous = ["rm -rf", "shutil.rmtree", "os.system('rm", "mkfs", ":(){ :|:& };:"]
        for d in dangerous:
            if d in code:
                return f"⛔ নিরাপত্তা সতর্কতা: ক্ষতিকর কমান্ড ব্লক করা হয়েছে ({d})।"
                
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False) as f:
            f.write(code)
            temp_name = f.name
            
        try:
            res = subprocess.run(
                [sys.executable, temp_name],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace"
            )
            output = res.stdout
            if res.stderr:
                output += ("\n[STDERR]\n" + res.stderr)
            return output.strip() if output.strip() else "[কোড সফলভাবে সম্পন্ন হয়েছে, কোনো আউটপুট প্রিন্ট হয়নি]"
        except subprocess.TimeoutExpired:
            return f"⏱️ সময় উত্তীর্ণ (Timeout): কোড চালাতে {timeout} সেকেন্ডের বেশি সময় লেগেছে।"
        except Exception as e:
            return f"❌ কোড এক্সিকিউশন ত্রুটি: {str(e)}"
        finally:
            try:
                os.remove(temp_name)
            except Exception:
                pass
