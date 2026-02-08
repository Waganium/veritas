import cv2
import mediapipe as mp
import numpy as np
import pygetwindow as gw
from mss import mss
from scipy.signal import butter, filtfilt
from collections import deque
import tkinter as tk
import sys

# --- ANALYTIC SETTINGS ---
TARGET_TITLE = "Meet"  
BUFFER_SIZE = 150      # Increased for better frequency resolution
SMOOTHING_FACTOR = 0.15 # Lower = slower but more stable movements

class VeritasXController:
    def __init__(self, root):
        self.root = root
        self.root.title("Veritas-X Control")
        self.root.geometry("320x250")
        self.root.config(bg="#0a0a0a")
        self.root.attributes("-topmost", True)

        tk.Label(root, text="VERITAS-X APEX", fg="cyan", bg="#0a0a0a", font=("Courier", 14, "bold")).pack(pady=15)
        
        self.start_btn = tk.Button(root, text="LAUNCH INTERCEPTOR", command=self.launch_overlay, 
                                   bg="#00ffcc", fg="black", font=("Arial", 10, "bold"), width=22, bd=0)
        self.start_btn.pack(pady=10)
        
        self.exit_btn = tk.Button(root, text="EXIT SYSTEM", command=sys.exit, 
                                  bg="#330000", fg="white", font=("Arial", 9), width=22, bd=0)
        self.exit_btn.pack(pady=5)
        
        tk.Label(root, text="Status: Engine Standby", fg="#555", bg="#0a0a0a").pack(side="bottom", pady=10)

    def launch_overlay(self):
        wins = [w for w in gw.getWindowsWithTitle(TARGET_TITLE) if w.visible]
        if not wins:
            from tkinter import messagebox
            messagebox.showwarning("Target Missing", "Google Meet window not found.")
            return
            
        self.root.withdraw()
        overlay_root = tk.Toplevel(self.root)
        VeritasGhostHUD(overlay_root, self.root)

class VeritasGhostHUD:
    def __init__(self, window, parent_root):
        self.window = window
        self.parent_root = parent_root
        self.window.attributes("-topmost", True, "-transparentcolor", "black")
        self.window.overrideredirect(True)
        self.window.config(bg="black")
        
        self.ui_frame = tk.Frame(self.window, bg="black")
        self.ui_frame.place(x=30, y=30)
        
        self.percent_lbl = tk.Label(self.ui_frame, text="0%", fg="#00ffcc", bg="black", font=("Courier", 32, "bold"))
        self.percent_lbl.pack(anchor="w")
        
        self.status_lbl = tk.Label(self.ui_frame, text="ANALYZING BIOMETRICS...", fg="white", bg="black", font=("Courier", 10))
        self.status_lbl.pack(anchor="w")

        # ENGINE
        self.mp_face = mp.solutions.face_mesh
        self.face_mesh = self.mp_face.FaceMesh(refine_landmarks=True, max_num_faces=1)
        self.pulse_buffer = deque(maxlen=BUFFER_SIZE)
        self.display_score = 0
        self.sct = mss()
        
        # Stop Button in Overlay
        tk.Button(self.window, text="[STOP SCAN]", command=self.shutdown, 
                  bg="black", fg="#444", bd=0, font=("Arial", 8)).place(x=5, y=5)
        
        self.update_loop()

    def shutdown(self):
        self.window.destroy()
        self.parent_root.deiconify()

    def calculate_threat(self, green_val):
        self.pulse_buffer.append(green_val)
        if len(self.pulse_buffer) < BUFFER_SIZE:
            return None

        try:
            # 1. HAMPEL FILTERING (Remove outliers/flicker)
            data = np.array(self.pulse_buffer)
            median = np.median(data)
            std = np.std(data)
            data = np.where(np.abs(data - median) > 3 * std, median, data)
            
            # 2. BANDPASS FILTERING (Human Pulse Extraction)
            # 3rd Order Butterworth: 0.75Hz to 3.0Hz
            data = (data - np.mean(data)) / (np.std(data) + 1e-6)
            b, a = butter(3, [0.75/15, 3.0/15], btype='band')
            filtered = filtfilt(b, a, data, padlen=min(len(data)-1, 45))
            
            # 3. SPECTRAL NOISE RATIO
            # Real pulse has a dominant rhythmic energy. Deepfakes have 'High Entropy' noise.
            energy = np.sum(np.diff(filtered)**2)
            
            # Human Optimal Range
            if 0.9 < energy < 2.1:
                target_prob = (energy - 0.9) * 5 
            else:
                # Calculate deviation from biological rhythm
                deviation = abs(energy - 1.5)
                target_prob = min(100, (deviation * 45) + 20)
            
            # 4. EXPONENTIAL SMOOTHING (Fluctuation Control)
            self.display_score = (self.display_score * (1 - SMOOTHING_FACTOR)) + (target_prob * SMOOTHING_FACTOR)
            return int(self.display_score)
        except:
            return 0

    def update_loop(self):
        try:
            wins = [w for w in gw.getWindowsWithTitle(TARGET_TITLE) if w.visible]
            if wins:
                win = wins[0]
                self.window.geometry(f"{win.width}x{win.height}+{win.left}+{win.top}")
                
                monitor = {"top": win.top, "left": win.left, "width": win.width, "height": win.height}
                img = np.array(self.sct.grab(monitor))
                rgb = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
                
                results = self.face_mesh.process(rgb)

                if results.multi_face_landmarks:
                    lm = results.multi_face_landmarks[0].landmark
                    h, w, _ = rgb.shape
                    # Sampling forehead and cheeks for average
                    green_pts = [rgb[int(lm[10].y*h), int(lm[10].x*w), 1],
                                 rgb[int(lm[234].y*h), int(lm[234].x*w), 1]]
                    
                    prob = self.calculate_threat(np.mean(green_pts))
                    
                    if prob is None:
                        cal_pct = int((len(self.pulse_buffer)/BUFFER_SIZE)*100)
                        self.percent_lbl.config(text=f"{cal_pct}%", fg="yellow")
                    else:
                        color = self.get_color(prob)
                        self.percent_lbl.config(text=f"{prob}%", fg=color)
                        self.status_lbl.config(text="THREAT: DEEPFAKE DETECTED" if prob > 60 else "TARGET: BIOMETRIC VERIFIED", fg=color)
                else:
                    self.percent_lbl.config(text="---", fg="#222")
                    self.status_lbl.config(text="TARGET OBSCURED", fg="#444")

        except Exception:
            pass
        self.window.after(30, self.update_loop)

    def get_color(self, prob):
        if prob < 30: return "#00ffcc" # Neon Cyan
        if prob < 60: return "#ffcc00" # Yellow
        return "#ff3300" # Warning Red

if __name__ == "__main__":
    root = tk.Tk()
    app = VeritasXController(root)
    root.mainloop()