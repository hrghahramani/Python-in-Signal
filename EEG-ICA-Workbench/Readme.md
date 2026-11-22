# EEG-ICA-Workbench

A desktop application for **EEG preprocessing ahead of Independent Component Analysis (ICA)**. It provides a graphical workflow for loading EEG recordings, applying standard filters, inspecting the signal, decomposing it with ICA, and removing artifact components such as eye blinks, eye movements, muscle activity and line noise.

Built with Python, Tkinter and [MNE-Python](https://mne.tools).

## Purpose

ICA is a common step for cleaning EEG data, but its quality depends heavily on how the data is prepared beforehand. This tool brings the whole preparation and cleaning pipeline into a single interface so that a recording can be filtered, visually checked, decomposed and cleaned without writing code.

## Prerequisites

- Python 3.9 or newer
- [MNE-Python](https://mne.tools) (file reading, filtering, ICA)
- NumPy and SciPy (numerical processing and signal filtering)
- Matplotlib (signal, spectrum and component plots embedded in the GUI)
- scikit-learn (required by MNE for FastICA)
- Tkinter (included with the standard Python distribution)
- Optional: `python-picard` for the Picard ICA algorithm

## What the code does

### 1. Data loading
- Scans a subject folder (including sub-folders) and lists all supported EEG files.
- Supported formats: EEGLAB `.set`, EDF `.edf`, BioSemi `.bdf`, MNE `.fif`, BrainVision `.vhdr`, Neuroscan `.cnt`.
- Loads the selected recording into memory and reads its channels, sampling rate, duration and event annotations.

### 2. Filtering
All filters are applied offline with **zero-phase** processing, so no phase distortion or time shift is introduced.
- **High-pass filter**: removes slow drifts and DC offset.
- **Low-pass filter**: removes high-frequency noise.
- **Notch filter**: removes power-line interference at one or several frequencies (e.g. 50 Hz and its harmonics).
- **Filter model**: IIR Butterworth with adjustable order, or FIR with adjustable number of taps.
- The original and filtered signals are kept separately so they can be compared at any time.

### 3. Signal inspection
- Multi-channel time-series viewer with adjustable start time, window duration and channel selection (e.g. `1-8` or `1,3,5-8`, 1-based).
- Adjustable vertical channel spacing and optional DC-offset removal (display only).
- Event markers and event labels drawn on the signal.
- Window navigation with previous/next buttons, a time slider and the mouse wheel.
- **Spectrum tab**: power spectral density of the raw versus filtered data, to verify the effect of the filters.
- **Events tab**: summary of the event types in the recording and how many times each occurs.

### 4. ICA decomposition
- Fits ICA with a selectable number of components and algorithm: FastICA, Infomax (extended) or Picard.
- Fits on a copy high-passed at 1 Hz when the chosen high-pass cutoff is lower, since ICA decomposes best on data without slow drifts.
- Displays the time course of each independent component.
- Plots component topographies (scalp maps) when channel positions are available.

### 5. Artifact removal and export
- The user lists the components identified as artifacts.
- Those components are removed and the signal is reconstructed from the remaining ones.
- The cleaned data, or the filtered data alone, can be saved as `.fif` files for further analysis.

## Typical applications

- Preparing EEG data for ICA-based artifact removal in research studies
- Removing eye-blink, eye-movement and line-noise artifacts from resting-state or task EEG
- Quick quality control of recordings through visual inspection and spectral comparison
- Preprocessing before downstream analysis such as ERP, time-frequency or connectivity analysis
- Teaching the effect of filter settings and ICA on EEG signals

## Project structure

```
EEG-ICA-Workbench/
├── eeg_ica_workbench.py   # the whole application (GUI + processing)
├── requirements.txt       # Python dependencies
└── README.md
```

## Acknowledgements

Built on [MNE-Python](https://mne.tools), NumPy, SciPy, Matplotlib and scikit-learn.
