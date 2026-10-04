"""
Generează sunetele offroader-ului (OGG Vorbis, mono 44.1 kHz — mono e
obligatoriu pentru poziționare 3D în Minecraft):
  engine.ogg  – buclă motor ~1.05 s (se reia cu pitch variabil după viteză)
  start.ogg   – demaraj (compresie + prindere motor)
  stop.ogg    – oprire (coborâre turație + pocnitură)
  horn.ogg    – claxon dual-ton
  boost.ogg   – suflu + urcare turație
  slosh.ogg   – gâlgâit alimentare

Rulare: python3 gen_sounds.py
"""
import os
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
SND = os.path.join(HERE, "..", "resourcepack", "assets", "offroader", "sounds")
SR = 44100
rng = np.random.default_rng(777)


def fft_filter(x, lo=None, hi=None, order=4.0):
    """Filtru treacă-jos/treacă-sus sau treacă-bandă, cu pante moi (FFT)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if hi is not None:
        g *= 1 / (1 + (f / max(hi, 1)) ** (2 * order))
    if lo is not None:
        g *= 1 - 1 / (1 + (f / max(lo, 1)) ** (2 * order))
    return np.fft.irfft(X * g, n=len(x))


def saw(f0, t, gain=1.0, detune=1.0):
    """Oscalator „dinte de fierăstrău" band-limitat prin armonice."""
    out = np.zeros_like(t)
    f = f0 * detune
    k = 1
    while f * k < SR / 2 - 2000 and k <= 40:
        out += np.sin(2 * np.pi * f * k * t + rng.uniform(0, 6.28)) / k
        k += 1
    return gain * out * (2 / np.pi)


def env_adsr(n, a, d, s_level, r, sr=SR):
    a_n, d_n, r_n = int(a * sr), int(d * sr), int(r * sr)
    e = np.ones(n) * s_level
    if a_n > 0:
        e[:a_n] = np.linspace(0, 1, a_n)
    if d_n > 0 and a_n + d_n < n:
        e[a_n:a_n + d_n] = np.linspace(1, s_level, d_n)
    if r_n > 0:
        e[-r_n:] = np.linspace(e[-r_n - 1] if n > r_n else s_level, 0, r_n)
    return e


def normalize(x, peak=0.85):
    m = np.max(np.abs(x))
    return x * (peak / m) if m > 0 else x


def save(name, x):
    os.makedirs(SND, exist_ok=True)
    x = np.clip(x, -1, 1)
    sf.write(os.path.join(SND, name), x.astype(np.float32), SR,
             format="OGG", subtype="VORBIS")
    print(f"scris: {name}  ({len(x)/SR:.2f}s, peak={np.max(np.abs(x)):.2f})")


# ---------------------------------------------------------------------------
def build_engine():
    # Toate componentele au un număr ÎNTREG de cicluri pe 1.2 s
    # (buclă fără cusătură; replay la 1.0 s => overlap ~0.2 s în fază):
    #   65 Hz (78 cicluri), 70 Hz (84), sub 32.5 Hz (39), LFO 12.5 Hz (15)
    dur = 1.2
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0, f2, fsub, flfo = 65.0, 70.0, 32.5, 12.5
    x = saw(f0, t, 1.0)
    x += saw(f2, t, 0.55)
    x += 0.45 * np.sin(2 * np.pi * fsub * t)
    lfo = 0.72 + 0.28 * np.sin(2 * np.pi * flfo * t + 0.7)
    x *= lfo
    # zgomot de admisie/evacuare, grav (crossfade cap-coadă „in place",
    # păstrăm exact 1.2 s ca și componentele tonale)
    nz = fft_filter(rng.standard_normal(n), hi=420, order=3)
    nz /= np.max(np.abs(nz))
    xf = int(0.06 * SR)
    w = np.linspace(0, 1, xf)
    nz[:xf] = nz[:xf] * w + nz[-xf:] * (1 - w)
    x = x + 0.16 * nz
    # „mufare" + limitare moale
    x = np.tanh(1.6 * x)
    x = fft_filter(x, hi=2600, order=2)
    save("engine.ogg", normalize(x, peak=0.6))


def build_start():
    dur = 0.95
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    # 1) compresie: 8 pulsuri la ~11 Hz, amplitudine crescătoare
    n_crank = int(0.42 * SR)
    tc = t[:n_crank]
    crank = np.zeros(n_crank)
    pulse_f = 46.0
    for i, tt in enumerate(np.arange(0, 0.4, 1 / 11.0)):
        s = int(tt * SR)
        L = int(0.075 * SR)
        if s + L > n_crank:
            L = n_crank - s
        if L <= 0:
            break
        tl = np.arange(L) / SR
        amp = 0.25 + 0.75 * (i / 9)
        crank[s:s + L] += amp * np.sin(2 * np.pi * pulse_f * tl) * np.exp(-tl * 26)
    x[:n_crank] += crank
    x[:n_crank] += 0.08 * fft_filter(rng.standard_normal(n_crank), hi=900)[:n_crank]
    # 2) prinderea motorului: sweep 55 -> 108 Hz cu LFO adânc
    n_run = n - n_crank
    tr = np.arange(n_run) / SR
    f_inst = 55 + (108 - 55) * np.minimum(tr / 0.28, 1.0)
    phase = 2 * np.pi * np.cumsum(f_inst) / SR
    run = np.zeros(n_run)
    k = 1
    while 108 * k < SR / 2 - 2000 and k <= 30:
        run += np.sin(k * phase + rng.uniform(0, 6.28)) / k
        k += 1
    run *= (2 / np.pi)
    run *= 0.7 + 0.3 * np.sin(2 * np.pi * 13 * tr)
    g = np.minimum(tr / 0.1, 1.0)
    x[n_crank:] += run * g
    x = np.tanh(1.5 * x)
    x = fft_filter(x, hi=2800, order=2)
    # fade-out scurt la final (bucla de mers preia)
    xf = int(0.04 * SR)
    x[-xf:] *= np.linspace(1, 0.35, xf)
    save("start.ogg", normalize(x, 0.8))


def build_stop():
    dur = 0.5
    n = int(dur * SR)
    t = np.arange(n) / SR
    f_inst = 100 - 62 * np.minimum(t / 0.38, 1.0)
    phase = 2 * np.pi * np.cumsum(f_inst) / SR
    x = np.zeros(n)
    k = 1
    while 100 * k < SR / 2 - 2000 and k <= 30:
        x += np.sin(k * phase + rng.uniform(0, 6.28)) / k
        k += 1
    x *= (2 / np.pi)
    x *= 0.7 + 0.3 * np.sin(2 * np.pi * 13 * t)
    x *= 1 - 0.55 * np.minimum(t / 0.45, 1.0)
    # pocnitură finală
    s = int(0.43 * SR)
    L = int(0.05 * SR)
    tl = np.arange(L) / SR
    x[s:s + L] += 0.5 * np.sin(2 * np.pi * 150 * tl) * np.exp(-tl * 60)
    x += 0.05 * fft_filter(rng.standard_normal(n), hi=1500) * np.exp(-t * 5)
    x = np.tanh(1.6 * x)
    x = fft_filter(x, hi=2600, order=2)
    save("stop.ogg", normalize(x, 0.75))


def build_horn():
    dur = 0.55
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for f0, g in ((370, 1.0), (466, 0.9), (740, 0.22), (932, 0.18)):
        vib = 1 + 0.006 * np.sin(2 * np.pi * 5.5 * t)
        ph = 2 * np.pi * f0 * vib * t
        # timbre „pătrat" (armonice impare)
        x += g * (np.sin(ph) + 0.30 * np.sin(3 * ph) + 0.12 * np.sin(5 * ph))
    x *= env_adsr(n, a=0.008, d=0.05, s_level=0.85, r=0.09)
    x = fft_filter(x, hi=2800, order=2)
    x = np.tanh(1.3 * x)
    save("horn.ogg", normalize(x, 0.85))


def build_boost():
    dur = 0.7
    n = int(dur * SR)
    t = np.arange(n) / SR
    f_inst = 85 + (230 - 85) * np.minimum(t / 0.45, 1.0) - 50 * np.maximum(t - 0.45, 0) / 0.25
    phase = 2 * np.pi * np.cumsum(f_inst) / SR
    x = np.zeros(n)
    k = 1
    while 230 * k < SR / 2 - 2000 and k <= 30:
        x += np.sin(k * phase + rng.uniform(0, 6.28)) / k
        k += 1
    x *= (2 / np.pi) * 0.8
    # suflu: zgomot cu pasă-bandă urcând
    nz = rng.standard_normal(n)
    hp = fft_filter(nz, lo=300, hi=2400, order=2)
    hp /= np.max(np.abs(hp))
    x += 0.55 * hp * env_adsr(n, 0.03, 0.1, 0.7, 0.25)
    x *= env_adsr(n, 0.02, 0.1, 0.9, 0.2)
    x = np.tanh(1.4 * x)
    save("boost.ogg", normalize(x, 0.8))


def build_slosh():
    dur = 0.65
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for i, tt in enumerate((0.0, 0.22, 0.44)):
        s = int(tt * SR)
        L = int(0.16 * SR)
        tl = np.arange(L) / SR
        f = 700 - 140 * i
        band = fft_filter(rng.standard_normal(L), lo=f - 260, hi=f + 120, order=2)
        band /= np.max(np.abs(band)) if np.max(np.abs(band)) > 0 else 1
        glug = np.sin(2 * np.pi * (190 - 40 * i) * tl) * np.exp(-tl * 18)
        chunk = 0.6 * band * np.exp(-tl * 14) + 0.4 * glug
        e = s + L
        x[s:min(e, n)] += chunk[:max(0, min(e, n) - s)]
    x = fft_filter(x, hi=1800, order=2)
    save("slosh.ogg", normalize(x, 0.7))


if __name__ == "__main__":
    build_engine()
    build_start()
    build_stop()
    build_horn()
    build_boost()
    build_slosh()
    print("Sunete generate în", os.path.relpath(SND, HERE))
