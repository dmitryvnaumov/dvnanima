import configparser
from pathlib import Path

import numpy as np
from scipy.io.wavfile import write


def load_timing(cfg_path: Path) -> dict:
    cfg = configparser.ConfigParser(inline_comment_prefixes=(";",))
    cfg.read(cfg_path)

    def get(key: str, fallback: float) -> float:
        if cfg.has_option("scene", key):
            return float(cfg.get("scene", key))
        return fallback

    create_time = get("create_time", 1.2)
    pre_wait = get("pre_morph_wait", 0.6)
    morph_time = get("morph_time", 1.3)
    post_wait = get("post_wait", 0.8)

    t_create_end = create_time
    t_morph_start = create_time + pre_wait
    t_morph_end = t_morph_start + morph_time
    t_end = t_morph_end + post_wait
    return {
        "create_time": create_time,
        "pre_wait": pre_wait,
        "morph_time": morph_time,
        "post_wait": post_wait,
        "t_create_end": t_create_end,
        "t_morph_start": t_morph_start,
        "t_morph_end": t_morph_end,
        "t_end": t_end,
    }


def smoothstep01(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def segment_env(t: np.ndarray, start: float, end: float, attack: float, release: float) -> np.ndarray:
    up = smoothstep01((t - start) / max(attack, 1e-6))
    down = smoothstep01((end - t) / max(release, 1e-6))
    return up * down * (t >= start) * (t <= end)


def osc_from_freq(f: np.ndarray, sr: int, phase0: float = 0.0) -> np.ndarray:
    phase = phase0 + 2.0 * np.pi * np.cumsum(f) / sr
    return np.sin(phase)


def pulse(t: np.ndarray, center: float, amp: float, width: float = 0.10) -> np.ndarray:
    # Soft "heartbeat" style pulse: low thump + upper click.
    g = np.exp(-0.5 * ((t - center) / width) ** 2)
    thump = np.sin(2 * np.pi * 88.0 * t) * np.exp(-np.clip(t - center, 0, None) / 0.16)
    click = np.sin(2 * np.pi * 420.0 * t) * np.exp(-np.clip(t - center, 0, None) / 0.035)
    return amp * g * (0.85 * thump + 0.25 * click)


def main() -> None:
    sr = 48000
    cfg_path = Path(__file__).with_name("run.cfg")
    timing = load_timing(cfg_path)

    T = timing["t_end"]
    t = np.linspace(0.0, T, int(sr * T), endpoint=False)

    t_create_end = timing["t_create_end"]
    t_morph_start = timing["t_morph_start"]
    t_morph_end = timing["t_morph_end"]

    # Base ambient bed for coherence.
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.17 * t + 0.8)
    pad = (
        0.55 * np.sin(2 * np.pi * 110.0 * t)
        + 0.30 * np.sin(2 * np.pi * 220.0 * t + 0.7)
        + 0.15 * np.sin(2 * np.pi * 330.0 * t + 1.4)
    )
    pad *= (0.08 + 0.05 * lfo) * segment_env(t, 0.0, T, attack=0.25, release=0.35)

    # Intro shimmer during nu draw.
    u_intro = np.clip(t / max(t_create_end, 1e-6), 0.0, 1.0)
    f_intro = 170.0 + 150.0 * (u_intro ** 1.5)
    intro = osc_from_freq(f_intro, sr)
    intro += 0.35 * osc_from_freq(2.0 * f_intro + 1.5, sr, phase0=0.8)
    intro *= (0.15 + 0.25 * u_intro) * segment_env(t, 0.0, t_morph_start, attack=0.03, release=0.20)

    # Main LIGO-like chirp during morph.
    u_morph = np.clip((t - t_morph_start) / max(t_morph_end - t_morph_start, 1e-6), 0.0, 1.0)
    f_morph = 120.0 + (2100.0 - 120.0) * (u_morph ** 2.9)
    morph = osc_from_freq(f_morph, sr)
    morph += 0.42 * osc_from_freq(2.0 * f_morph + 2.0, sr, phase0=0.25)
    morph += 0.20 * osc_from_freq(3.0 * f_morph + 4.0, sr, phase0=1.10)
    morph_gain = (0.08 + 0.62 * (u_morph ** 1.25))
    morph *= morph_gain * segment_env(t, t_morph_start, t_morph_end, attack=0.05, release=0.16)

    # Merger accent near end of transform.
    accent = np.exp(-0.5 * ((t - t_morph_end) / 0.055) ** 2) * np.sin(2 * np.pi * 990.0 * t)

    # Post-morph resolution and heartbeat.
    post_env = segment_env(t, t_morph_end, T, attack=0.02, release=max(timing["post_wait"] * 0.85, 0.12))
    resolve = (
        0.45 * np.sin(2 * np.pi * 261.63 * t)
        + 0.35 * np.sin(2 * np.pi * 329.63 * t + 0.4)
        + 0.20 * np.sin(2 * np.pi * 392.00 * t + 1.1)
    ) * (0.20 * post_env)
    beat1 = pulse(t, t_morph_end + 0.13, amp=0.42, width=0.085)
    beat2 = pulse(t, t_morph_end + 0.42, amp=0.34, width=0.095)

    # Subtle texture to avoid sterile synthesis.
    rng = np.random.default_rng(7)
    noise = rng.standard_normal(len(t))
    noise = np.convolve(noise, np.ones(40) / 40.0, mode="same")
    noise *= 0.015 * segment_env(t, 0.0, T, attack=0.1, release=0.3)

    mono = pad + intro + morph + 0.20 * accent + resolve + beat1 + beat2 + noise

    # Gentle stereo spread.
    pan = 0.10 * np.sin(2 * np.pi * 0.11 * t + 0.4)
    left = mono * (1.0 - pan)
    right = mono * (1.0 + pan)
    sig = np.stack([left, right], axis=1)

    # Soft limiter + normalization.
    sig = np.tanh(1.25 * sig)
    peak = np.max(np.abs(sig))
    if peak > 0:
        sig = sig / peak * 0.93

    out_path = Path(__file__).with_name("chirp_valentine.wav")
    write(out_path, sr, (sig * 32767).astype(np.int16))

    print(f"Wrote {out_path.name}")
    print(
        "Markers: "
        f"create_end={t_create_end:.3f}s, "
        f"morph_start={t_morph_start:.3f}s, "
        f"morph_end={t_morph_end:.3f}s, "
        f"end={T:.3f}s"
    )


if __name__ == "__main__":
    main()
