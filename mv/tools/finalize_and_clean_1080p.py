"""Wait for the 1080p shot masters, assemble/encode/QC the new version, then archive old
deliverables and delete old caches.  Cleanup only runs after the new final passes checks.

Started by the MV1080_Finalize scheduled task; safe to run while the 3 render queues are
still working (it polls assemble.check until all 15 shots are valid).
"""
import datetime
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = r'D:\Code\Code MV\new-word.search(you)'
TOOLS = os.path.join(ROOT, 'mv', 'tools')
OUT = os.path.join(ROOT, 'mv', 'out')
JOBS = os.path.join(OUT, 'jobs')
SHOTS = os.path.join(OUT, 'shots')
FINAL_DIR = os.path.join(OUT, 'final')
FINAL = os.path.join(FINAL_DIR, 'world.search(you)_final_v4.mp4')
FFPROBE = r'C:\ffmpeg\bin\ffprobe.exe'
PY = sys.executable
LOG_PATH = os.path.join(JOBS, 'finalize_V4.log')
EXPECTED_FRAMES = 17721

if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import assemble


def log(msg):
    line = '[%s] %s' % (time.strftime('%H:%M:%S'), msg)
    print(line, flush=True)
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except OSError:
        pass


def run_step(name, cmd):
    log('STEP %s start' % name)
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=7200)
    except Exception as e:
        log('STEP %s EXC %r' % (name, e))
        return False
    step_log = os.path.join(JOBS, 'finalize_V4_%s.log' % name)
    with open(step_log, 'w', encoding='utf-8') as f:
        f.write(p.stdout or '')
        f.write('\n--- stderr ---\n')
        f.write(p.stderr or '')
    log('STEP %s rc=%s log=%s' % (name, p.returncode, step_log))
    return p.returncode == 0


def wait_ready(timeout_h=6.0):
    deadline = time.time() + timeout_h * 3600
    while time.time() < deadline:
        try:
            bad = assemble.check(verbose=False)
        except Exception as e:
            log('CHECK_ERR %r' % (e,))
            bad = [('check', 'ERR')]
        if not bad:
            log('READY 15/15 shots valid')
            return True
        ids = ','.join(str(b[0]) for b in bad)
        log('WAIT bad=%s' % ids)
        time.sleep(60)
    log('TIMEOUT waiting for shots')
    return False


def probe_final():
    try:
        p = subprocess.run([FFPROBE, '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                            '-show_entries', 'stream=nb_read_frames,width,height,r_frame_rate',
                            '-of', 'json', FINAL],
                           capture_output=True, text=True, timeout=600)
        st = json.loads(p.stdout)['streams'][0]
        frames = int(st.get('nb_read_frames', 0))
        w, h = int(st.get('width', 0)), int(st.get('height', 0))
        fps = st.get('r_frame_rate', '')
    except Exception as e:
        log('PROBE_FINAL_ERR %r' % (e,))
        return False
    size = os.path.getsize(FINAL) if os.path.exists(FINAL) else 0
    ok = frames == EXPECTED_FRAMES and w == 1920 and h == 1080 and fps == '60/1' and size > 100 * 1024 * 1024
    log('PROBE_FINAL frames=%s %dx%d fps=%s size=%.1fMB ok=%s' % (
        frames, w, h, fps, size / 1e6, ok))
    return ok


def move_to_archive(paths, archive):
    moved = []
    for p in paths:
        if not os.path.exists(p):
            continue
        try:
            os.makedirs(archive, exist_ok=True)
            dst = os.path.join(archive, os.path.basename(p))
            if os.path.exists(dst):
                dst = dst + '.%d' % int(time.time())
            shutil.move(p, dst)
            moved.append('%s -> %s' % (p, dst))
            log('ARCHIVE %s -> %s' % (p, dst))
        except Exception as e:
            log('ARCHIVE_FAIL %s %r' % (p, e))
    return moved


def rm_tree(path):
    if not os.path.exists(path):
        return False
    try:
        shutil.rmtree(path)
        log('DELETE %s' % path)
        return True
    except Exception as e:
        log('DELETE_FAIL %s %r' % (path, e))
        return False


def cleanup():
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    archive = os.path.join(r'D:\Code\Code MV', '_archive_old_pre_v4_' + stamp)
    old_files = [
        os.path.join(FINAL_DIR, 'world.search(you)_final.mp4'),
        os.path.join(FINAL_DIR, 'world.search(you)_final_v2.mp4'),
        os.path.join(FINAL_DIR, 'world.search(you)_final_v3.mp4'),
        os.path.join(FINAL_DIR, 'CLEANUP_MANIFEST_1080P.txt'),
        os.path.join(FINAL_DIR, 'poster_2560x1440.png'),
        os.path.join(FINAL_DIR, 'poster_1800x2700.png'),
        os.path.join(ROOT, 'mv', 'lookdev.blend1'),
        os.path.join(ROOT, 'mv', 'lookdev_before_convenience.blend'),
    ]
    moved = move_to_archive(old_files, archive)

    deleted = []
    for p in [
        os.path.join(SHOTS, '_stale_1440p'),
        os.path.join(SHOTS, '_stale_v3_partials'),
        os.path.join(OUT, 'lookdev'),
        os.path.join(OUT, 'perf'),
        os.path.join(OUT, 'perf_speed'),
        os.path.join(OUT, 'bench'),
        os.path.join(OUT, 'tests'),
        os.path.join(JOBS, 'jobs'),
        os.path.join(ROOT, 'mv', 'mv'),
    ]:
        if rm_tree(p):
            deleted.append(p)

    # Old job logs/bats only; keep the new V4 run and finalize logs.
    keep = ('queue_V4', 'dispatch_V4', 'run_V4', 'finalize_V4')
    for name in list(os.listdir(JOBS)) if os.path.isdir(JOBS) else []:
        p = os.path.join(JOBS, name)
        if os.path.isdir(p):
            if rm_tree(p):
                deleted.append(p)
            continue
        is_new = name.startswith(keep) or (name.startswith('render_') and 'V4' in name)
        if not is_new:
            try:
                os.remove(p)
                deleted.append(p)
            except OSError as e:
                log('DELETE_FAIL %s %r' % (p, e))

    for tn in ('MV1080_A', 'MV1080_B', 'MV1080_C', 'MV1080_Finalize'):
        subprocess.run(['schtasks', '/Delete', '/TN', tn, '/F'],
                       capture_output=True, text=True)

    manifest = os.path.join(FINAL_DIR, 'CLEANUP_MANIFEST_V4.txt')
    with open(manifest, 'w', encoding='utf-8') as f:
        f.write('1080p final: %s\n' % FINAL)
        f.write('archived old versions to: %s\n' % archive)
        f.write('\nARCHIVED\n')
        f.write('\n'.join(moved) or '(none)')
        f.write('\n\nDELETED CACHES\n')
        f.write('\n'.join(deleted) or '(none)')
        f.write('\n')
    log('CLEANUP archived=%d deleted=%d manifest=%s' % (len(moved), len(deleted), manifest))


def main():
    log('FINALIZE_1080 start')
    if not wait_ready():
        log('FINALIZE_1080 aborted: shots not ready; no cleanup')
        return 2
    if not run_step('assemble_video', [PY, os.path.join(TOOLS, 'assemble.py'), '--video']):
        log('FINALIZE_1080 aborted at assemble_video; no cleanup')
        return 3
    if not run_step('assemble_audio', [PY, os.path.join(TOOLS, 'assemble.py'), '--audio']):
        log('FINALIZE_1080 aborted at assemble_audio; no cleanup')
        return 3
    if not run_step('burn', [PY, os.path.join(TOOLS, 'final_encode.py'), '--burn', '--fast']):
        log('FINALIZE_1080 aborted at burn; no cleanup')
        return 4

    qc_dir = os.path.join(OUT, 'qc')
    if os.path.isdir(qc_dir):
        for n in os.listdir(qc_dir):
            p = os.path.join(qc_dir, n)
            try:
                os.remove(p) if os.path.isfile(p) else shutil.rmtree(p)
            except OSError:
                pass
    if not run_step('qc', [PY, os.path.join(TOOLS, 'final_encode.py'), '--qc']):
        log('FINALIZE_1080 aborted at qc; no cleanup')
        return 5
    if not probe_final():
        log('FINALIZE_1080 aborted: final validation failed; no cleanup')
        return 6

    cleanup()
    log('FINALIZE_1080 done')
    return 0


if __name__ == '__main__':
    sys.exit(main())
