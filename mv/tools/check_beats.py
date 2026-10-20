import json, wave, numpy as np
root = r'D:\Code\Code MV\new-word.search(you)'
# read wav (44.1k stereo s16)
w = wave.open(root + r'\mv\ref\song44100.wav', 'rb')
sr = w.getframerate(); n = w.getnframes()
print('wav', sr, n, n/sr)
data = np.frombuffer(w.readframes(n), dtype=np.int16).reshape(-1,2).astype(np.float32).mean(axis=1)
w.close()
env = np.abs(data)
# onset strength via spectral flux on 512 hop
hop = 512
frame = 2048
nfr = (len(data)-frame)//hop
win = np.hanning(frame).astype(np.float32)
# vectorized stft magnitude
idx = np.arange(frame)[None,:] + hop*np.arange(nfr)[:,None]
spec = np.abs(np.fft.rfft(data[idx]*win, axis=1))
flux = np.maximum(0, np.diff(spec, axis=0)).sum(axis=1)
flux = np.concatenate([[0],flux])
t = (np.arange(nfr)*hop + frame/2)/sr
# repo beats
b = json.load(open(root + r'\mv\ref\repo\film\timing\beats.json'))
bt = np.array(b['beat_times'])
print('beats', len(bt), bt[:5], bt[-3:])

def score(offset):
    tt = bt + offset
    tt = tt[(tt>0)&(tt<t[-1])]
    ii = np.searchsorted(t, tt)
    sel = flux[np.clip(ii,0,len(flux)-1)]
    return sel.mean()
best = max(np.arange(-0.5,0.51,0.01), key=score)
print('best offset', round(best,3), 'score', round(score(best),2), 'score@0', round(score(0),2), 'mean', round(flux.mean(),2))
# also test fixed 138.3 grid
for bpm, first in [(139.17,0.0878),(138.3,0.1028)]:
    per = 60/bpm
    tg = first + per*np.arange(int((292.5-first)/per))
    ii = np.searchsorted(t, tg); print(bpm, 'score', round(flux[np.clip(ii,0,len(flux)-1)].mean(),2))
np.save(root + r'\mv\data\onset_env.npy', np.stack([t, flux]).astype(np.float32))
print('saved onset env')
