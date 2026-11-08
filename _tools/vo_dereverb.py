# -*- coding: utf-8 -*-
"""单通道去混响：numpy 实现的 WPE（加权预测误差），带逐点幅度下限防止过度抑制。

用法：
    from vo_dereverb import dereverb_wav
    y = dereverb_wav(x, sr, taps=10, delay=3, iters=3, floor_db=12, blend=1.0)

原理：语音的晚混响可以用过去几十毫秒的频谱线性预测出来；把预测出的混响成分
从当前帧里减掉，就得到更干的直达声。delay 之前(<32ms)的直达声与早期反射不动，
floor 限制每个频点最多压 floor_db dB，blend 控制干湿混合（1=全处理）。
"""
import numpy as np


def stft(x, nfft=1024, hop=256):
    w = np.hanning(nfft + 1)[:nfft]
    pad = nfft - hop
    xp = np.concatenate([np.zeros(pad), x, np.zeros(nfft)])
    n = 1 + (len(xp) - nfft) // hop
    frames = np.lib.stride_tricks.as_strided(
        xp, shape=(n, nfft), strides=(xp.strides[0] * hop, xp.strides[0])).copy()
    return (frames * w).T @ np.fft.rfft(np.eye(nfft)) if False else np.fft.rfft(frames * w, axis=1).T


def istft(X, nfft=1024, hop=256, length=None):
    w = np.hanning(nfft + 1)[:nfft]
    n = X.shape[1]
    out = np.zeros(nfft + (n - 1) * hop)
    wsum = np.zeros_like(out)
    for t in range(n):
        frame = np.fft.irfft(X[:, t], nfft) * w
        out[t * hop:t * hop + nfft] += frame
        wsum[t * hop:t * hop + nfft] += w ** 2
    out /= np.maximum(wsum, 1e-9)
    pad = nfft - hop
    y = out[pad:pad + (n - 1) * hop + hop]
    if length:
        y = y[:length]
    return y


def _noise_gate(Y, max_att_db=15.0, smooth=0.5):
    """谱减法降噪：逐频点估计噪底，幅度谱减，增益做时间平滑防音乐噪声。"""
    mag = np.abs(Y)
    F, T = mag.shape
    # 噪底：每频点 10% 分位（大多数帧是语音，静隙帧落在低分位），频率方向平滑
    noise = np.percentile(mag, 10, axis=1, keepdims=True)      # (F,1)
    kernel = np.ones(9) / 9.0
    noise = np.convolve(noise[:, 0], kernel, mode="same")[:, None]
    snr = mag ** 2 / (noise ** 2 + 1e-12)
    snr = np.where(np.isfinite(snr), snr, 0.0)
    gain = np.sqrt(np.maximum(snr - 1.0, 0.0) / np.maximum(snr, 1e-12))  # 幅度谱减增益
    floor = 10 ** (-max_att_db / 20.0)
    gain = np.maximum(gain, floor)
    # 时间平滑：只允许缓慢上升（快攻慢放），抑制断续
    g = gain.copy()
    for t in range(1, T):
        g[:, t] = np.maximum(g[:, t], smooth * g[:, t - 1])
    return Y * g


def dereverb_wav(x, sr, taps=10, delay=3, iters=3, floor_db=12.0, blend=1.0,
                 denoise_db=0.0, wmode="inv"):
    """wmode:
         none  - 不加权 LS（最稳，拟合能力强）
         inv   - 1/max(p, P90) 加权（仅削弱过响帧，避免病态）
         sqrt  - 1/sqrt(median 截断 p) 折中
    """
    x = x.astype(np.float64)
    nfft = 1024 if sr >= 20000 else 512
    hop = nfft // 4
    X = stft(x, nfft, hop)               # (F, T) complex
    F, T = X.shape
    Y = X.copy()

    K, D = taps, delay
    alpha = 10 ** (-floor_db / 20.0)
    idx = np.arange(T)[:, None] - D - np.arange(K)[None, :]
    vm_cache = {}

    for _ in range(iters):
        p = np.mean(np.abs(Y) ** 2, axis=0) + 1e-12   # 方差稳定化（用上一轮输出）
        if wmode == "none":
            wgt = np.ones(T)
        elif wmode == "inv":
            wgt = 1.0 / np.maximum(p, np.percentile(p, 90))
        else:
            wgt = 1.0 / np.sqrt(np.maximum(p, np.percentile(p, 50)))
        wgt = wgt / np.mean(wgt)
        wgt[: D + K - 1] = 0.0                        # 无足够历史的帧不参与
        valid_t = np.where(wgt > 0)[0]
        wv = wgt[valid_t]
        for f in range(F):
            xf = X[f]
            vmat = np.stack([xf[idx[valid_t, k]] for k in range(K)], axis=1)  # (Tv, K)
            R = (vmat.conj().T * wv) @ vmat + 1e-6 * np.eye(K)
            r = (vmat.conj().T @ (wv * xf[valid_t]))
            g = np.linalg.solve(R, r)
            yf = xf.copy()
            yf[valid_t] = xf[valid_t] - vmat @ g
            Y[f] = yf

        # 幅度下限：每频点最多压 floor_db，相位用 Y 的
        mag = np.abs(Y)
        lim = alpha * np.abs(X)
        bad = mag < lim
        Y[bad] = lim[bad] * np.exp(1j * np.angle(Y[bad]))

    if denoise_db > 0:
        Y = _noise_gate(Y, max_att_db=denoise_db)

    y = istft(Y, nfft, hop, length=len(x))
    if blend < 1.0:
        y = blend * y + (1 - blend) * x
    # 防止数值溢出削波
    peak = np.max(np.abs(y))
    if peak > 0.99:
        y = y / peak * 0.99
    return y
