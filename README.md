# EEG-ICA-Workbench

A simple desktop GUI (Python + Tkinter + [MNE-Python](https://mne.tools)) for **EEG preprocessing before ICA**: load a recording, filter it, inspect it, run ICA, remove artifact components, and save the cleaned data.

> فارسی: یک نرم‌افزار دسکتاپ ساده برای پیش‌پردازش سیگنال EEG قبل از ICA؛ شامل فیلتر، مشاهده‌ی سیگنال، اجرای ICA، حذف کامپوننت‌های artifact و ذخیره‌ی خروجی. توضیح فارسی در انتهای همین فایل آمده است.

## Features

- **Load recordings**: `.set` (EEGLAB), `.edf`, `.bdf`, `.fif`, `.vhdr` (BrainVision), `.cnt`
- **Folder scan**: finds all EEG files inside a subject folder
- **Filters** (offline, zero-phase): high-pass, low-pass, notch (one or several frequencies, e.g. `50,100`)
  - IIR Butterworth (adjustable order) or FIR (adjustable taps)
- **Signal viewer**: start/duration, channel selection (`1-8`, `1,3,5-8`), channel gap, DC-offset removal, event lines and labels
- **Navigation**: previous/next window, slider, mouse wheel
- **Tabs**: Raw, Filtered, Spectrum (PSD before vs. after), Events, ICA
- **ICA**: FastICA / Infomax / Picard, component time courses, topomaps, exclude components, save cleaned `.fif`

## Installation

Requires Python 3.9+.

```bash
pip install -r requirements.txt
python eeg_ica_workbench.py
```

(Optional, for the Picard method: `pip install python-picard`)

## Usage

1. Click **Browse** and choose a subject folder, then **Scan folder**.
2. Select a file from the list and click **Load recording**.
3. Set the filter values (e.g. high-pass 0.5 Hz, low-pass 45 Hz, notch 50 Hz) and click **Apply filters + redraw**.
4. Check the **Raw**, **Filtered** and **Spectrum** tabs.
5. In the **ICA** tab choose the number of components and method, then click **Run ICA**.
6. Type the artifact component numbers (0-based, e.g. `0,2`) in *Exclude* and click **Apply ICA + Save .fif**.

Note: ICA works best on data high-passed at 1 Hz or above. If your high-pass is below 1 Hz, the app automatically uses a 1 Hz copy to fit ICA.

## Build a Windows executable

```bash
pip install pyinstaller
pyinstaller --noconsole --onedir --name EEG_ICA_Workbench --collect-data mne --collect-submodules sklearn eeg_ica_workbench.py
```

The app will be in `dist/EEG_ICA_Workbench/`. Distribute the **whole folder** (zip it), not only the `.exe`.
Use `--onefile` for a single file (slower startup). Remove `--noconsole` to see error messages while debugging.

## Project structure

```
EEG-ICA-Workbench/
├── eeg_ica_workbench.py
├── requirements.txt
└── README.md
```

## Roadmap

- ICLabel for automatic artifact classification
- Bad channel detection and interpolation
- Re-referencing and montage selection
- Batch processing of multiple subjects

## Acknowledgements

Built on [MNE-Python](https://mne.tools), NumPy, SciPy, Matplotlib and scikit-learn.

## License

MIT (add a `LICENSE` file to your repository).

---

## توضیح فارسی

این برنامه برای پیش‌پردازش سیگنال‌های EEG قبل از ICA ساخته شده است.

**نصب و اجرا:**
۱. پایتون را نصب کن (حتماً تیک Add Python to PATH را بزن).
۲. در پوشه‌ی پروژه یک Command Prompt باز کن و بزن: `pip install -r requirements.txt`
۳. برنامه را اجرا کن: `python eeg_ica_workbench.py`

**روش کار:** پوشه‌ی سوژه را انتخاب کن، Scan folder بزن، فایل را Load کن، فیلترها را تنظیم و اعمال کن، در تب ICA گزینه‌ی Run ICA را بزن، شماره‌ی کامپوننت‌های artifact را وارد کن و خروجی را ذخیره کن.

**ساخت exe:** دستور PyInstaller بالا را اجرا کن و کل پوشه‌ی `dist/EEG_ICA_Workbench` را به‌صورت Zip توزیع کن.
