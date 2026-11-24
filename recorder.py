"""Moteur d'enregistrement : son du PC (WASAPI loopback), micro, ou les deux.

Chaque source est enregistrée dans un WAV temporaire, puis mixée à l'arrêt.
"""
import os
import shutil
import tempfile
import time
import wave

import numpy as np
import pyaudiowpatch as pyaudio

TARGET_RATE = 48000


def list_devices():
    """Retourne (loopbacks, micros, loopback_par_defaut, micro_par_defaut)."""
    p = pyaudio.PyAudio()
    try:
        wasapi = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        loops, mics = [], []
        for i in range(p.get_device_count()):
            d = p.get_device_info_by_index(i)
            if d["hostApi"] != wasapi["index"]:
                continue
            if d.get("isLoopbackDevice"):
                loops.append(d)
            elif d["maxInputChannels"] > 0:
                mics.append(d)
        try:
            def_loop = p.get_default_wasapi_loopback()
        except Exception:
            def_loop = loops[0] if loops else None
        try:
            def_mic = p.get_device_info_by_index(wasapi["defaultInputDevice"])
        except Exception:
            def_mic = mics[0] if mics else None
        return loops, mics, def_loop, def_mic
    finally:
        p.terminate()


class _Capture:
    """Capture d'un périphérique vers un WAV (callback, avec remplissage des silences)."""

    def __init__(self, dev, path):
        self.dev = dev
        self.path = path
        self.rate = int(dev["defaultSampleRate"])
        self.ch = max(1, int(dev["maxInputChannels"]))
        self.level = 0.0
        self.frames = 0
        self.t0 = 0.0

    def _cb(self, in_data, frame_count, time_info, status):
        # Le loopback WASAPI n'envoie rien pendant le silence : on comble avec du silence
        missing = int((time.time() - self.t0) * self.rate) - self.frames - frame_count
        if missing > self.rate * 0.1:
            self.wf.writeframes(b"\x00" * (missing * self.ch * 2))
            self.frames += missing
        self.wf.writeframes(in_data)
        self.frames += frame_count
        a = np.frombuffer(in_data, dtype=np.int16)
        self.level = float(np.abs(a).max()) / 32768 if a.size else 0.0
        return (None, pyaudio.paContinue)

    def start(self):
        self.p = pyaudio.PyAudio()
        self.wf = wave.open(self.path, "wb")
        self.wf.setnchannels(self.ch)
        self.wf.setsampwidth(2)
        self.wf.setframerate(self.rate)
        self.t0 = time.time()
        self.stream = self.p.open(
            format=pyaudio.paInt16, channels=self.ch, rate=self.rate, input=True,
            input_device_index=self.dev["index"], frames_per_buffer=1024,
            stream_callback=self._cb,
        )

    def stop(self):
        self.stream.stop_stream()
        self.stream.close()
        total = int((time.time() - self.t0) * self.rate)
        if total > self.frames:
            self.wf.writeframes(b"\x00" * ((total - self.frames) * self.ch * 2))
        self.wf.close()
        self.p.terminate()


def _load(path):
    with wave.open(path, "rb") as wf:
        ch, rate = wf.getnchannels(), wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    a = np.frombuffer(raw, dtype=np.int16).reshape(-1, ch).astype(np.float32) / 32768
    if ch == 1:
        a = np.repeat(a, 2, axis=1)
    elif ch > 2:
        a = a[:, :2]
    return a, rate


def _resample(a, rate, target):
    if rate == target or len(a) < 2:
        return a
    n = int(len(a) * target / rate)
    x_old = np.linspace(0, 1, len(a))
    x_new = np.linspace(0, 1, n)
    return np.stack([np.interp(x_new, x_old, a[:, c]) for c in range(2)], axis=1).astype(np.float32)


def _write_wav(path, a, rate):
    pcm = (np.clip(a, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm.tobytes())


class Recorder:
    def __init__(self, loop_dev, mic_dev, out_path):
        """loop_dev et/ou mic_dev peuvent être None (source désactivée)."""
        self.out_path = out_path
        self.tmp = tempfile.mkdtemp(prefix="audiorec_")
        self.loop = _Capture(loop_dev, os.path.join(self.tmp, "loop.wav")) if loop_dev else None
        self.mic = _Capture(mic_dev, os.path.join(self.tmp, "mic.wav")) if mic_dev else None
        self.started_at = 0.0

    @property
    def levels(self):
        return (self.loop.level if self.loop else 0.0, self.mic.level if self.mic else 0.0)

    def start(self):
        started = []
        try:
            for c in (self.loop, self.mic):
                if c:
                    c.start()
                    started.append(c)
        except Exception:
            for c in started:
                c.stop()
            shutil.rmtree(self.tmp, ignore_errors=True)
            raise
        self.started_at = time.time()

    def stop(self):
        for c in (self.loop, self.mic):
            if c:
                c.stop()
        try:
            if self.loop and self.mic:
                a, ra = _load(self.loop.path)
                b, rb = _load(self.mic.path)
                a, b = _resample(a, ra, TARGET_RATE), _resample(b, rb, TARGET_RATE)
                n = max(len(a), len(b))
                a = np.pad(a, ((0, n - len(a)), (0, 0)))
                b = np.pad(b, ((0, n - len(b)), (0, 0)))
                _write_wav(self.out_path, (a + b) * 0.7, TARGET_RATE)
            else:
                src = (self.loop or self.mic).path
                shutil.move(src, self.out_path)
        finally:
            shutil.rmtree(self.tmp, ignore_errors=True)
        return self.out_path
