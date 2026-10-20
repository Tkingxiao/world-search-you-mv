"""Build mv/data/shots.json - machine-readable shot contract for the film."""
import json, os

ROOT = r'D:\Code\Code MV\new-word.search(you)'
OUT = os.path.join(ROOT, 'mv', 'data', 'shots.json')

SHOTS = [
 dict(id='s01', name='typing',   t0=0.000,  t1=6.000,  section='PROLOGUE',  stage='00 OFFLINE',
      set='void_ink', camera='macro static, slow push 4%',
      char=[], hud=['title_fade_in'], fx=['paper_fiber', 'dust'], notes='terminal lines typed on near-black; cursor blink'),
 dict(id='s02', name='sinking',  t0=6.000,  t1=10.000, section='PROLOGUE',  stage='00 OFFLINE',
      set='archive', camera='45deg dive, wide 24mm, fall past shelves',
      char=[], hud=[], fx=['shelf_fog', 'paper_drift', 'index_sheet'], notes='giant index sheet floats by; title card world.'),
 dict(id='s03', name='sheet',    t0=10.000, t1=14.360, section='PROLOGUE',  stage='00 OFFLINE',
      set='void_water', camera='medium, slow push',
      char=[('confused', 10.0, 13.1), ('serious', 13.1, 14.36)], hud=['title_card'], fx=['bubbles', 'blank_sheet'], notes='she steps out of the drawing; sheet falls blank'),
 dict(id='s04', name='bubbles',  t0=14.360, t1=28.320, section='SORT', stage='01 SORT',
      set='bubble_shaft', camera='track up with char, 28mm',
      char=[('starry', 14.36, 18.4), ('cheerful', 18.4, 24.0), ('serious', 24.0, 28.32)],
      hud=['memory_her89', 'lyric'], fx=['bubbles_photos', 'pop_on_beat'], notes='lyric 0-1'),
 dict(id='s05', name='memory',   t0=28.320, t1=40.860, section='SORT', stage='01 SORT',
      set='bubble_shaft', camera='orbit half circle, 35mm',
      char=[('shy', 28.32, 33.0), ('serious', 33.0, 36.5), ('cheerful', 36.5, 40.86)],
      hud=['memory_her89', 'lyric', 'log_insert'], fx=['glass_jar', 'drawer_past'], notes='lyric 2-3; insert bubble into past drawer; save sweetest in jar'),
 dict(id='s06', name='table',    t0=40.860, t1=54.460, section='RECALL', stage='02 RECALL',
      set='hall_spot', camera='wide 24mm -> medium 50mm',
      char=[('confused', 40.86, 46.0), ('sad', 46.0, 50.0), ('serious', 50.0, 54.46)],
      hud=['memory_her89', 'label_table', 'lyric', 'log_sim031'], fx=['scan_lines', 'spot_cone'], notes='lyric 4-7'),
 dict(id='s07', name='eggplant', t0=54.460, t1=68.170, section='RECALL', stage='02 RECALL',
      set='hall_spot', camera='low angle 35mm',
      char=[('exasperated', 54.46, 58.0), ('cheerful', 58.0, 63.0), ('confused', 63.0, 68.17)],
      hud=['memory_her80', 'label_eggplant', 'lyric'], fx=['scratch_glow', 'scan_lines'], notes='lyric 8-11'),
 dict(id='s08', name='search_a', t0=68.170, t1=82.890, section='SEARCH-A', stage='03 ROUTE',
      set='archive_shaft', camera='vertical rise, wide',
      char=[('serious', 68.17, 82.89)], hud=['memory_her80', 'stage_route', 'lyric_imsearching'], fx=['koinobori_far', 'god_rays'], notes='interlude; kites first appear; memory dropping'),
 dict(id='s09', name='cat',      t0=82.890, t1=96.640, section='ROUTE', stage='03 ROUTE',
      set='hall_spot', camera='medium close, 50mm',
      char=[('starry', 82.89, 87.0), ('frightened', 87.0, 92.0), ('confused', 92.0, 96.64)],
      hud=['memory_her73', 'label_cat', 'lyric'], fx=['wireframe_cat', 'hiss_glyphs', 'purr_zero'], notes='lyric 13-19'),
 dict(id='s10', name='steak',    t0=96.640, t1=109.720, section='ROUTE', stage='03 ROUTE',
      set='hall_spot', camera='macro 55mm',
      char=[('starry', 96.64, 103.0), ('cheerful', 103.0, 109.72)],
      hud=['memory_her67', 'label_steak', 'lyric'], fx=['mushroom_sauce', 'paper_bite'], notes='lyric 20-23'),
 dict(id='s11', name='flower',   t0=109.720, t1=123.440, section='ROUTE', stage='03 ROUTE',
      set='hall_spot', camera='close, slow push',
      char=[('shy', 109.72, 115.0), ('cheerful', 115.0, 123.44)],
      hud=['memory_her67', 'label_flower', 'lyric'], fx=['petal_beat', 'warm_bloom'], notes='lyric 24-27'),
 dict(id='s12', name='human',    t0=123.440, t1=137.090, section='ROUTE', stage='03 ROUTE',
      set='light_human', camera='side long lens 85mm',
      char=[('frightened', 123.44, 129.0), ('shy', 129.0, 133.0), ('sad', 133.0, 137.09)],
      hud=['memory_her67', 'label_human', 'lyric'], fx=['light_hand', 'edge_on_hand', 'warm_bleed'], notes='lyric 28-31'),
 dict(id='s13', name='void',     t0=137.090, t1=151.840, section='SEARCH-B', stage='03 ROUTE',
      set='void_dark', camera='static wide, drift',
      char=[('serious', 137.09, 144.0), ('sad', 144.0, 151.84)],
      hud=['memory_her24', 'lyric_imsearching', 'log_peer_overwrite'], fx=['kites_pass', 'paper_crack'], notes='interlude; memory collapses'),
 dict(id='s14', name='forget',   t0=151.840, t1=168.000, section='FORGET', stage='04 FORGET',
      set='typewriter_page', camera='frontal flat, 35mm',
      char=[('exasperated', 151.84, 158.0), ('frightened', 158.0, 168.0)],
      hud=['memory_her28', 'lyric', 'typewriter'], fx=['falling_letters', 'wrong_word'], notes='lyric 32-37'),
 dict(id='s15', name='love',     t0=168.000, t1=179.470, section='FORGET', stage='04 FORGET',
      set='typewriter_page', camera='close, sinking',
      char=[('sad', 168.0, 179.47)], hud=['memory_her32', 'lyric', 'logit_dope_love'], fx=['torn_photo', 'sink'], notes='lyric 38-42'),
 dict(id='s16', name='everywhere', t0=179.470, t1=207.140, section='EVERYWHERE', stage='05 EVERYWHERE',
      set='storm', camera='6 jump cuts on downbeats',
      char=[('starry', 179.47, 186.0), ('cheerful', 186.0, 193.0), ('frightened', 193.0, 200.0), ('sad', 200.0, 207.14)],
      hud=['memory_her15', 'lyric', 'label_spam'], fx=['kaleidoscope', 'blank_sheet_drift'], notes='lyric 43-49'),
 dict(id='s17', name='bucket',   t0=207.140, t1=221.180, section='MERGE', stage='06 MERGE',
      set='merge_ring', camera='orbit wide',
      char=[('serious', 207.14, 214.0), ('sad', 214.0, 221.18)],
      hud=['memory_merged', 'lyric', 'peer_labels'], fx=['kites_ring', 'buckets_light'], notes='lyric 50-51'),
 dict(id='s18', name='shred',    t0=221.180, t1=233.770, section='MERGE', stage='06 MERGE',
      set='vortex', camera='spiral in -> low angle up',
      char=[], hud=['memory_merged', 'lyric', 'cut_counter'], fx=['paper_shred', 'whale_form', 'iridescent'],
      notes='lyric 52-53; only volume form of the film'),
 dict(id='s19', name='resurface', t0=233.770, t1=261.060, section='RESURFACE', stage='07 RESURFACE',
      set='warm_hall', camera='long take: flower -> human -> wide',
      char=[], hud=['memory_merged', 'lyric'], fx=['giant_bloom', 'embrace_ok', 'paint_bleed'], notes='lyric 54-57'),
 dict(id='s20', name='ascent',   t0=261.060, t1=275.750, section='ASCENT', stage='07 RESURFACE',
      set='ascent', camera='vertical rise following whale',
      char=[], hud=['lyric_imsearching', 'restore'], fx=['archive_melt', 'petals'], notes='interlude'),
 dict(id='s21', name='restore',  t0=275.750, t1=295.347, section='RESTORE', stage='08 RESTORE',
      set='dawn_surface', camera='wide -> eye level close',
      char=[], hud=['lyric', 'result_you', 'endcard'], fx=['tomato', 'chibi_puppy', 'paint_splash', 'bubble'],
      notes='lyric 58-66; query result at 290.8 chime; title/credits 291.2-295.3'),
]

def main():
    data = {'fps': 60, 'width': 1920, 'height': 1080, 'samples': 10, 'shots': []}
    for s in SHOTS:
        s = dict(s)
        s['dur'] = round(s['t1'] - s['t0'], 3)
        s['frames'] = (int(round(s['t1'] * 60)) - int(round(s['t0'] * 60)))
        data['shots'].append(s)
    total = sum(s['frames'] for s in data['shots'])
    data['total_frames'] = total
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote', OUT, 'shots', len(data['shots']), 'frames', total, 'secs', round(total/60, 1))
    for s in data['shots']:
        print(f"{s['id']} {s['name']:11s} {s['t0']:7.2f}-{s['t1']:7.2f} {s['frames']:5d}f {s['set']:14s} char={len(s['char'])}")

if __name__ == '__main__':
    main()
