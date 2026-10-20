import json, wave, numpy as np
root = r'D:\Code\Code MV\new-word.search(you)'
w = wave.open(root + r'\mv\ref\song44100.wav', 'rb')
sr = w.getframerate(); n = w.getnframes()
data = np.frombuffer(w.readframes(n), dtype=np.int16).reshape(-1,2).astype(np.float32).mean(axis=1)
w.close()
hop = 441; frame=2048
nfr = (len(data)-frame)//hop
idx = np.arange(frame)[None,:]+hop*np.arange(nfr)[:,None]
spec = np.abs(np.fft.rfft(data[idx]*np.hanning(frame)[None,:],axis=1))
freqs = np.fft.rfftfreq(frame,1/sr)
low = spec[:,(freqs>=40)&(freqs<=120)].mean(axis=1)
t = (np.arange(nfr)*hop+frame/2)/sr
print('first 3s low-band peaks:')
for tt in [0.09,0.54,0.97,1.41,1.84,2.27]:
    sl = (t>tt-0.35)&(t<tt+0.35)
    k = np.argmax(low[sl]); print(f'grid {tt:.3f} -> peak {t[sl][k]:.3f} (delta {t[sl][k]-tt:+.3f})')
bt = np.array(json.load(open(root + r'\mv\ref\repo\film\timing\beats.json'))['beat_times'])
def score(off):
    tt = bt[bt+off < t[-1]]+off
    ii = np.clip((tt*sr/hop).astype(int),0,nfr-1)
    return np.log(low[ii]+1).mean()
offs = np.arange(-0.4,0.41,0.005)
sc = np.array([score(o) for o in offs])
print('best offset', round(offs[np.argmax(sc)],3), 'score', round(sc.max(),3), 'at 0', round(score(0),3))
for tt in [106.4, 137.1, 151.9, 179.5, 207.1, 233.8, 261.1, 275.8, 290.8]:
    i0,i1 = int((tt-0.6)*sr/hop), int((tt+0.6)*sr/hop)
    k = np.argmin(low[i0:i1]) if low[i0:i1].size else 0
    print(f'marker {tt}: min low at {t[i0+k]:.3f}')
