"""EEG ICA Preprocessing Workbench (Tkinter + MNE)
pip install mne numpy scipy matplotlib scikit-learn
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import mne
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

mne.set_log_level("ERROR")
EXTS = (".set", ".edf", ".bdf", ".fif", ".vhdr", ".cnt")


def read_any(path):
    e = os.path.splitext(path)[1].lower()
    if e == ".set":
        return mne.io.read_raw_eeglab(path, preload=True)
    if e == ".edf":
        return mne.io.read_raw_edf(path, preload=True)
    if e == ".bdf":
        return mne.io.read_raw_bdf(path, preload=True)
    if e == ".vhdr":
        return mne.io.read_raw_brainvision(path, preload=True)
    if e == ".cnt":
        return mne.io.read_raw_cnt(path, preload=True)
    return mne.io.read_raw_fif(path, preload=True)


def parse_channels(txt, n):
    """'1-8' or '1,3,5-8' (1-based) -> 0-based index list"""
    idx = []
    for part in txt.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-")
            idx += list(range(int(a) - 1, int(b)))
        else:
            idx.append(int(part) - 1)
    return [i for i in idx if 0 <= i < n] or list(range(min(n, 8)))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EEG ICA Workbench | Python")
        self.geometry("1250x850")
        self.raw = self.filt = self.ica = self.cleaned = None
        self.files = {}
        self._build()

    # ---------------------------------------------------------- UI
    def _build(self):
        v = {}
        self.v = v
        for k, d in dict(folder="", hp="0.5", lp="45.0", notch="50.0", start="0.0",
                         dur="10.0", chans="1-8", gap="auto", order="4", taps="auto",
                         ncomp="15", excl="").items():
            v[k] = tk.StringVar(value=d)
        for k, d in dict(hp_on=True, lp_on=True, nt_on=True, dc=True,
                         ev=True, evtxt=True).items():
            v[k] = tk.BooleanVar(value=d)
        v["model"] = tk.StringVar(value="IIR Butterworth")
        v["method"] = tk.StringVar(value="fastica")
        v["file"] = tk.StringVar()
        v["status"] = tk.StringVar(value="No recording loaded")

        P = dict(padx=3, pady=2)
        r1 = ttk.Frame(self); r1.pack(fill="x", **P)
        ttk.Label(r1, text="Subject folder:").pack(side="left")
        ttk.Entry(r1, textvariable=v["folder"], width=70).pack(side="left", padx=4)
        ttk.Button(r1, text="Browse", command=self.browse).pack(side="left")
        ttk.Button(r1, text="Scan folder", command=self.scan).pack(side="left", padx=4)

        r2 = ttk.Frame(self); r2.pack(fill="x", **P)
        self.cmb = ttk.Combobox(r2, textvariable=v["file"], width=70, state="readonly")
        self.cmb.pack(side="left", padx=4)
        ttk.Button(r2, text="Load recording", command=self.load).pack(side="left")

        r3 = ttk.LabelFrame(self, text="Filters (Hz) - offline zero-phase")
        r3.pack(fill="x", **P)
        for txt, on, val in (("High-pass", "hp_on", "hp"), ("Low-pass", "lp_on", "lp"),
                             ("Notch centers", "nt_on", "notch")):
            ttk.Checkbutton(r3, text=txt, variable=v[on]).pack(side="left")
            ttk.Entry(r3, textvariable=v[val], width=8).pack(side="left", padx=(2, 10))
        ttk.Label(r3, text="Model").pack(side="left")
        ttk.Combobox(r3, textvariable=v["model"], width=16, state="readonly",
                     values=["IIR Butterworth", "FIR"]).pack(side="left", padx=4)
        ttk.Label(r3, text="IIR order").pack(side="left")
        ttk.Entry(r3, textvariable=v["order"], width=4).pack(side="left", padx=4)
        ttk.Label(r3, text="FIR taps").pack(side="left")
        ttk.Entry(r3, textvariable=v["taps"], width=6).pack(side="left", padx=4)
        ttk.Button(r3, text="Apply filters + redraw", command=self.apply_filters).pack(side="left", padx=8)

        r4 = ttk.Frame(self); r4.pack(fill="x", **P)
        for lbl, k, w in (("Start (s)", "start", 6), ("Duration (s)", "dur", 6),
                          ("Channels (1-based)", "chans", 14), ("Channel gap (uV)", "gap", 8)):
            ttk.Label(r4, text=lbl).pack(side="left")
            ttk.Entry(r4, textvariable=v[k], width=w).pack(side="left", padx=(2, 10))
        ttk.Button(r4, text="Update display", command=self.redraw).pack(side="left")
        for txt, k in (("Hide DC offset", "dc"), ("Event lines", "ev"), ("Event text", "evtxt")):
            ttk.Checkbutton(r4, text=txt, variable=v[k], command=self.redraw).pack(side="left", padx=6)

        r5 = ttk.Frame(self); r5.pack(fill="x", **P)
        ttk.Button(r5, text="|< Start", command=lambda: self.jump(0)).pack(side="left")
        ttk.Button(r5, text="< Previous", command=lambda: self.shift(-1)).pack(side="left", padx=3)
        ttk.Button(r5, text="Next >", command=lambda: self.shift(1)).pack(side="left")
        self.scale = ttk.Scale(r5, from_=0, to=1, command=self.on_slider)
        self.scale.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Label(r5, textvariable=v["status"]).pack(side="left")

        self.nb = ttk.Notebook(self); self.nb.pack(fill="both", expand=True, **P)
        self.tabs = {}
        for name in ("Raw", "Filtered", "Spectrum", "Events", "ICA"):
            f = ttk.Frame(self.nb); self.nb.add(f, text=name); self.tabs[name] = f
        self.nb.bind("<<NotebookTabChanged>>", lambda e: self.redraw())

        self.figs = {}
        for name in ("Raw", "Filtered", "Spectrum"):
            self.figs[name] = self._canvas(self.tabs[name])
        self.txt = tk.Text(self.tabs["Events"]); self.txt.pack(fill="both", expand=True)

        ib = ttk.Frame(self.tabs["ICA"]); ib.pack(fill="x", **P)
        ttk.Label(ib, text="Components").pack(side="left")
        ttk.Entry(ib, textvariable=v["ncomp"], width=5).pack(side="left", padx=4)
        ttk.Label(ib, text="Method").pack(side="left")
        ttk.Combobox(ib, textvariable=v["method"], width=9, state="readonly",
                     values=["fastica", "infomax", "picard"]).pack(side="left", padx=4)
        ttk.Button(ib, text="Run ICA", command=self.run_ica).pack(side="left", padx=4)
        ttk.Button(ib, text="Topomaps", command=self.topomaps).pack(side="left")
        ttk.Label(ib, text="Exclude (0-based, e.g. 0,2)").pack(side="left", padx=(12, 2))
        ttk.Entry(ib, textvariable=v["excl"], width=12).pack(side="left")
        ttk.Button(ib, text="Apply ICA + Save .fif", command=self.apply_ica).pack(side="left", padx=6)
        ttk.Button(ib, text="Save filtered .fif", command=self.save_filtered).pack(side="left")
        self.figs["ICA"] = self._canvas(self.tabs["ICA"])

        for c in self.figs.values():
            c[1].get_tk_widget().bind("<MouseWheel>", lambda e: self.shift(-1 if e.delta > 0 else 1, 0.25))

    def _canvas(self, parent):
        fig = Figure(figsize=(10, 5), dpi=100)
        cv = FigureCanvasTkAgg(fig, master=parent)
        cv.get_tk_widget().pack(fill="both", expand=True)
        return fig, cv

    # ------------------------------------------------------- file ops
    def browse(self):
        d = filedialog.askdirectory()
        if d:
            self.v["folder"].set(d); self.scan()

    def scan(self):
        root = self.v["folder"].get()
        self.files = {}
        for dp, _, fn in os.walk(root):
            for f in sorted(fn):
                if f.lower().endswith(EXTS):
                    self.files[os.path.relpath(os.path.join(dp, f), root)] = os.path.join(dp, f)
        self.cmb["values"] = list(self.files)
        if self.files:
            self.cmb.current(0)
        else:
            messagebox.showinfo("Scan", "No EEG files found.")

    def load(self):
        p = self.files.get(self.v["file"].get())
        if not p:
            return
        try:
            self.raw = read_any(p)
        except Exception as e:
            messagebox.showerror("Load error", str(e)); return
        self.filt = self.raw.copy(); self.ica = self.cleaned = None
        self.scale.configure(to=max(self.raw.times[-1] - 1, 1))
        self.v["status"].set(f"{len(self.raw.ch_names)} ch | {self.raw.info['sfreq']:.0f} Hz | "
                             f"{self.raw.times[-1]:.1f} s")
        self.show_events(); self.redraw()

    # -------------------------------------------------------- filtering
    def apply_filters(self):
        if self.raw is None:
            return
        v = self.v
        try:
            l = float(v["hp"].get()) if v["hp_on"].get() else None
            h = float(v["lp"].get()) if v["lp_on"].get() else None
            f = self.raw.copy()
            picks = mne.pick_types(f.info, eeg=True, eog=True, misc=False)
            if l is not None or h is not None:
                if v["model"].get().startswith("IIR"):
                    f.filter(l, h, picks=picks, method="iir", phase="zero",
                             iir_params=dict(order=int(v["order"].get()), ftype="butter"))
                else:
                    t = v["taps"].get()
                    f.filter(l, h, picks=picks, method="fir", phase="zero",
                             filter_length="auto" if t == "auto" else int(t))
            if v["nt_on"].get():
                fr = [float(x) for x in v["notch"].get().split(",") if x.strip()]
                f.notch_filter(fr, picks=picks)
            self.filt = f
        except Exception as e:
            messagebox.showerror("Filter error", str(e)); return
        self.nb.select(self.tabs["Filtered"]); self.redraw()

    # ---------------------------------------------------------- plots
    def shift(self, d, frac=None):
        if self.raw is None:
            return
        dur = float(self.v["dur"].get())
        s = float(self.v["start"].get()) + d * dur * (frac or 1)
        self.jump(s)

    def jump(self, s):
        if self.raw is None:
            return
        s = min(max(0, s), max(self.raw.times[-1] - 1, 0))
        self.v["start"].set(f"{s:.2f}"); self.scale.set(s); self.redraw()

    def on_slider(self, val):
        if self.raw is not None and abs(float(val) - float(self.v["start"].get())) > 0.05:
            self.v["start"].set(f"{float(val):.2f}"); self.redraw()

    def redraw(self):
        if self.raw is None:
            return
        tab = self.nb.tab(self.nb.select(), "text")
        if tab in ("Raw", "Filtered"):
            self.plot_traces(tab, self.raw if tab == "Raw" else self.filt)
        elif tab == "Spectrum":
            self.plot_psd()
        elif tab == "ICA" and self.ica is not None:
            self.plot_sources()

    def window(self, raw):
        sf = raw.info["sfreq"]
        s = float(self.v["start"].get()); d = float(self.v["dur"].get())
        a, b = int(s * sf), int(min(s + d, raw.times[-1]) * sf)
        return a, b, s

    def plot_traces(self, tab, raw):
        fig, cv = self.figs[tab]; fig.clear(); ax = fig.add_subplot(111)
        idx = parse_channels(self.v["chans"].get(), len(raw.ch_names))
        a, b, s = self.window(raw)
        data = raw.get_data(picks=idx, start=a, stop=b) * 1e6
        if self.v["dc"].get():
            data = data - data.mean(axis=1, keepdims=True)
        g = self.v["gap"].get()
        gap = float(g) if g != "auto" else max(3 * np.median(data.std(axis=1)), 1)
        t = np.arange(a, b) / raw.info["sfreq"]
        for i, row in enumerate(data):
            ax.plot(t, row - i * gap, lw=0.6, color="k")
        ax.set_yticks([-i * gap for i in range(len(idx))])
        ax.set_yticklabels([raw.ch_names[i] for i in idx], fontsize=8)
        ax.set_xlabel("Time (s)"); ax.set_xlim(t[0], t[-1])
        if self.v["ev"].get():
            try:
                ev, eid = mne.events_from_annotations(raw)
                inv = {v: k for k, v in eid.items()}
                for smp, _, c in ev:
                    ts = smp / raw.info["sfreq"]
                    if t[0] <= ts <= t[-1]:
                        ax.axvline(ts, color="r", lw=0.7)
                        if self.v["evtxt"].get():
                            ax.text(ts, 0.5 * gap, inv[c], color="r", fontsize=7, rotation=90)
            except Exception:
                pass
        fig.tight_layout(); cv.draw()

    def plot_psd(self):
        fig, cv = self.figs["Spectrum"]; fig.clear(); ax = fig.add_subplot(111)
        for r, lab in ((self.raw, "raw"), (self.filt, "filtered")):
            p, f = r.compute_psd(fmax=80, picks="eeg").get_data(return_freqs=True)
            ax.semilogy(f, p.mean(0), label=lab)
        ax.set_xlabel("Hz"); ax.set_ylabel("PSD (V²/Hz)"); ax.legend(); ax.grid(alpha=.3)
        fig.tight_layout(); cv.draw()

    def show_events(self):
        self.txt.delete("1.0", "end")
        try:
            ev, eid = mne.events_from_annotations(self.raw)
            for k, c in eid.items():
                self.txt.insert("end", f"{k}: {int((ev[:, 2] == c).sum())} events\n")
        except Exception:
            self.txt.insert("end", "No events/annotations found.")

    # -------------------------------------------------------------- ICA
    def run_ica(self):
        if self.filt is None:
            return
        try:
            n = int(self.v["ncomp"].get())
            src = self.filt.copy().pick("eeg")
            if float(self.v["hp"].get() or 0) < 1.0:
                src.filter(1.0, None, phase="zero")  # ICA fits best on >=1 Hz data
            self.config(cursor="watch"); self.update()
            kw = dict(max_iter=500) if self.v["method"].get() != "infomax" else dict(fit_params=dict(extended=True))
            self.ica = mne.preprocessing.ICA(n_components=min(n, len(src.ch_names) - 1),
                                              method=self.v["method"].get(),
                                              random_state=97, **kw)
            self.ica.fit(src)
            self.src = src
        except Exception as e:
            messagebox.showerror("ICA error", str(e))
        finally:
            self.config(cursor="")
        self.plot_sources()

    def plot_sources(self):
        fig, cv = self.figs["ICA"]; fig.clear(); ax = fig.add_subplot(111)
        a, b, s = self.window(self.src)
        S = self.ica.get_sources(self.src).get_data(start=a, stop=b)
        gap = max(3 * np.median(S.std(axis=1)), 1e-9)
        t = np.arange(a, b) / self.src.info["sfreq"]
        for i, row in enumerate(S):
            ax.plot(t, row - i * gap, lw=0.6)
        ax.set_yticks([-i * gap for i in range(len(S))])
        ax.set_yticklabels([f"IC{i}" for i in range(len(S))], fontsize=8)
        fig.tight_layout(); cv.draw()

    def topomaps(self):
        if self.ica is None:
            return
        try:
            self.ica.plot_components()
            import matplotlib.pyplot as plt; plt.show(block=False)
        except Exception as e:
            messagebox.showwarning("Topomap", f"Needs channel positions (montage).\n{e}")

    def apply_ica(self):
        if self.ica is None:
            return
        ex = [int(x) for x in self.v["excl"].get().split(",") if x.strip()]
        self.ica.exclude = ex
        self.cleaned = self.ica.apply(self.filt.copy(), exclude=ex)
        p = filedialog.asksaveasfilename(defaultextension=".fif", initialfile="cleaned_ica-raw.fif")
        if p:
            self.cleaned.save(p, overwrite=True)
            messagebox.showinfo("Saved", p)

    def save_filtered(self):
        if self.filt is None:
            return
        p = filedialog.asksaveasfilename(defaultextension=".fif", initialfile="filtered-raw.fif")
        if p:
            self.filt.save(p, overwrite=True)


if __name__ == "__main__":
    App().mainloop()
