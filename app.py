import os
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import recorder


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio Recorder")
        self.geometry("480x470")
        self.resizable(False, False)
        self.rec = None

        try:
            self.loops, self.mics, self.def_loop, self.def_mic = recorder.list_devices()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lister les périphériques audio :\n{e}")
            self.loops, self.mics, self.def_loop, self.def_mic = [], [], None, None

        self.mode = tk.StringVar(value="both")
        self.out_dir = tk.StringVar(
            value=os.path.join(os.path.expanduser("~"), "Music", "Enregistrements")
        )
        self._build()
        self._tick()

    # ---------- UI ----------
    def _build(self):
        pad = {"padx": 16, "pady": 4}

        src = ttk.LabelFrame(self, text="Source")
        src.pack(fill="x", **pad)
        for text, val in (("Son du PC", "pc"), ("Micro", "mic"), ("Les deux", "both")):
            ttk.Radiobutton(src, text=text, value=val, variable=self.mode).pack(side="left", padx=12, pady=6)

        dev = ttk.LabelFrame(self, text="Périphériques")
        dev.pack(fill="x", **pad)
        ttk.Label(dev, text="Sortie PC :").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.cb_loop = ttk.Combobox(dev, state="readonly", width=44,
                                    values=[d["name"] for d in self.loops])
        self.cb_loop.grid(row=0, column=1, padx=8)
        ttk.Label(dev, text="Micro :").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.cb_mic = ttk.Combobox(dev, state="readonly", width=44,
                                   values=[d["name"] for d in self.mics])
        self.cb_mic.grid(row=1, column=1, padx=8)
        self._select_default(self.cb_loop, self.loops, self.def_loop)
        self._select_default(self.cb_mic, self.mics, self.def_mic)

        out = ttk.LabelFrame(self, text="Dossier de sortie")
        out.pack(fill="x", **pad)
        ttk.Entry(out, textvariable=self.out_dir, state="readonly", width=44).pack(side="left", padx=8, pady=6)
        ttk.Button(out, text="Choisir…", command=self._choose_dir).pack(side="left")

        lv = ttk.LabelFrame(self, text="Niveaux")
        lv.pack(fill="x", **pad)
        ttk.Label(lv, text="PC").grid(row=0, column=0, padx=8, pady=2)
        self.bar_loop = ttk.Progressbar(lv, maximum=100, length=370)
        self.bar_loop.grid(row=0, column=1, pady=2)
        ttk.Label(lv, text="Micro").grid(row=1, column=0, padx=8, pady=2)
        self.bar_mic = ttk.Progressbar(lv, maximum=100, length=370)
        self.bar_mic.grid(row=1, column=1, pady=2)

        self.lbl_time = ttk.Label(self, text="00:00:00", font=("Segoe UI", 28, "bold"))
        self.lbl_time.pack(pady=(10, 2))
        self.btn = ttk.Button(self, text="● Démarrer", command=self.toggle)
        self.btn.pack(ipadx=30, ipady=8, pady=6)
        self.lbl_status = ttk.Label(self, text="Prêt", foreground="gray")
        self.lbl_status.pack()
        self.btn_open = ttk.Button(self, text="Ouvrir le dossier", command=self._open_dir)
        self.btn_open.pack(pady=4)

    @staticmethod
    def _select_default(combo, devs, default):
        if not devs:
            return
        idx = next((i for i, d in enumerate(devs) if default and d["index"] == default["index"]), 0)
        combo.current(idx)

    def _choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.out_dir.get())
        if d:
            self.out_dir.set(d)

    def _open_dir(self):
        os.makedirs(self.out_dir.get(), exist_ok=True)
        os.startfile(self.out_dir.get())

    # ---------- Enregistrement ----------
    def toggle(self):
        if self.rec is None:
            self.start()
        else:
            self.stop()

    def start(self):
        mode = self.mode.get()
        loop_dev = mic_dev = None
        if mode in ("pc", "both"):
            if not self.loops:
                return messagebox.showwarning("Source", "Aucune sortie audio détectée.")
            loop_dev = self.loops[self.cb_loop.current()]
        if mode in ("mic", "both"):
            if not self.mics:
                return messagebox.showwarning("Source", "Aucun micro détecté.")
            mic_dev = self.mics[self.cb_mic.current()]

        os.makedirs(self.out_dir.get(), exist_ok=True)
        name = datetime.now().strftime("enregistrement_%Y%m%d_%H%M%S.wav")
        path = os.path.join(self.out_dir.get(), name)
        try:
            self.rec = recorder.Recorder(loop_dev, mic_dev, path)
            self.rec.start()
        except Exception as e:
            self.rec = None
            return messagebox.showerror("Erreur", f"Démarrage impossible :\n{e}")
        self.btn.config(text="■ Arrêter")
        self.lbl_status.config(text="Enregistrement en cours…", foreground="red")

    def stop(self):
        rec, self.rec = self.rec, None
        self.btn.config(state="disabled")
        self.lbl_status.config(text="Finalisation…", foreground="gray")

        def work():
            try:
                path = rec.stop()
                self.after(0, lambda: self._done(f"Enregistré : {os.path.basename(path)}"))
            except Exception as e:
                self.after(0, lambda: self._done(f"Erreur : {e}"))

        threading.Thread(target=work, daemon=True).start()

    def _done(self, msg):
        self.btn.config(text="● Démarrer", state="normal")
        self.lbl_status.config(text=msg, foreground="green" if msg.startswith("Enregistré") else "red")
        self.bar_loop["value"] = 0
        self.bar_mic["value"] = 0

    def _tick(self):
        if self.rec:
            s = int(time.time() - self.rec.started_at)
            self.lbl_time.config(text=f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}")
            lo, mi = self.rec.levels
            self.bar_loop["value"] = min(100, lo * 100)
            self.bar_mic["value"] = min(100, mi * 100)
        self.after(100, self._tick)


if __name__ == "__main__":
    App().mainloop()
