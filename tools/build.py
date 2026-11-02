# 產生網站資料：site/data.js（選項、規則、零件、採購項目）和 site/img/（選項預覽圖、作者照片）
# 用法：python build.py            （會用 data/raw/*.json；要更新 Printables 資料先跑 fetch.py）
#       python build.py --no-img   （不下載圖片）
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(os.path.dirname(HERE), 'site')
RAW = os.path.join(os.path.dirname(HERE), 'data', 'raw')
PROJ = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(PROJ, '_工具腳本'))
import catalog_def as C
from parts_data import PARTS, RETIRED
from materials import assess
from rename_stl import EXTRA

sys.stdout.reconfigure(encoding='utf-8')


def norm(name):
    return re.sub(r'\.stl$', '', name, flags=re.I).replace(' ', '')


# ---------- Printables 頁面和檔案 ----------
index = json.load(open(os.path.join(RAW, 'index.json'), encoding='utf-8'))
pages, files = {}, {}
for pid, meta in index['pages'].items():
    d = json.load(open(os.path.join(RAW, f'{pid}.json'), encoding='utf-8'))
    pages[pid] = {'name': d['name'], 'zh': meta['zh'], 'kind': meta['kind'], 'author': d['user']['handle'].split('_')[0],
                  'url': f'https://www.printables.com/model/{pid}', 'images': [i['filePath'] for i in d['images']],
                  'updated': max((s['created'] for s in d['stls']), default='')[:10], 'count': len(d['stls'])}
    for s in d['stls']:
        k = f'{pid}:{norm(s["name"])}'
        if k not in files:
            files[k] = {'page': pid, 'file': s['name'], 'preview': s.get('filePreviewPath'), 'date': s['created'][:10]}

# ---------- 中文名稱 ----------
ZH = {}
for p in PARTS:
    ZH[norm(p[0])] = p[1]
for k, v in list(RETIRED.items()) + list(EXTRA.items()):
    ZH.setdefault(norm(k), re.sub(r'（[^）]*(不用|取代|重複件|不相容)[^）]*）', '', v))
OURS = {}   # 我們的材質：原檔名 → (材質, 填充, 理由)
for p in PARTS:
    mat, plate, alt, why = assess(p[0], p[5], p[3])
    OURS[norm(p[0])] = (mat, p[8], why)
# 我們的檔名有前綴，對回 Printables 的頁面
PREFIX = {'HC_': C.HC, 'HL_': C.HEAD, 'PT_': C.HITCH}


def our_key(key):
    pid, f = key.split(':', 1)
    for pre, page in PREFIX.items():
        if pid == page and pre + f in OURS:
            return pre + f
    return f if f in OURS and pid in (C.MAIN, C.WS4, C.TOP, C.AFTER) else None


PAGE_WORDS = {'1557212': {'radlice': '雪鏟 鏟板', 'upper': '雪鏟 上臂', 'lower': '雪鏟 下臂', 'mount': '雪鏟 車頭固定座', 'drzak': '雪鏟 支架'},
              '992013': {'spare_wheel': '備胎（蓋住突出的電池）', 'spare_wheel_cover': '備胎套'}}
WORDS = [('AxleHousing', '強化橋殼'), ('AxleSpindle', '強化轉向節'), ('SparewheelHolder', '備胎架'), ('VTXBox-Mount', 'VTX 盒 固定座'),
         ('VTXBox-cover', 'VTX 盒 上蓋'), ('VTXBox-box', 'VTX 盒'), ('gimbaladapter', 'FPV 雲台座'), ('cameraclip', '相機夾'), ('seatmount', '座椅相機座'),
         ('Holder', '相機座'), ('MainCase', '主殼'), ('Maincase', '主殼'), ('MainBody', '主殼'), ('TransferCaseCover', '傳動箱蓋'), ('transferCaseCover', '傳動箱蓋'),
         ('TransferCaseEnd', '傳動箱端蓋'), ('TransferCase', '傳動箱'), ('transferCase', '傳動箱'), ('FrontCover', '前蓋'), ('MotorPlate', '馬達板'),
         ('MotorMount', '馬達座'), ('Motormount', '馬達座'), ('BearingPlate', '軸承板'), ('Spacer', '墊片'), ('RodTool', '組裝工具'), ('RodToo', '組裝工具'),
         ('Tool', '組裝工具'), ('GearMotor', '馬達齒輪'), ('MotorGear', '馬達齒輪'), ('GearTransfer', '傳動齒輪'), ('GearTailShaft', '尾軸齒輪'),
         ('GearTop', '上齒輪'), ('GearBottom', '下齒輪'), ('Gearbottom', '下齒輪'), ('BeltCover', '皮帶蓋'), ('Cover', '蓋'), ('Locker', '鎖圈'),
         ('BeadLockerRingOuter', '外露鎖圈環'), ('Inner', '內片'), ('WheelRing', '內環'), ('Outter', '外片'), ('Outer', '外片'), ('Alloy', '鋁圈外片'),
         ('Adapter', '轉接環'), ('Receiver', '鉤座'), ('Main', '本體'), ('Upper', '上蓋'), ('Lower', '下扣'), ('Clamp', '夾具'), ('Swivel', '旋轉座'),
         ('Knob', '旋鈕'), ('Slide', '滑塊'), ('knob', '旋鈕'), ('HalfTopTubRear', '半頂後車斗'), ('HalfTopFakeFloor', '半頂假地板'), ('HalfTopCooler', '半頂冰箱'),
         ('HalfTopFuelCell', '半頂油箱'), ('SeatPed', '座椅底座'), ('CenterConsoleBase', '中央扶手座'), ('HalfTop', '半頂車頂'), ('WindowRubber', '擋風玻璃膠條'),
         ('RollBarsMain', '防滾架'), ('TireBars', '備胎架'), ('GasMount', '油桶架'), ('RollBarSpacer', '防滾架墊片'), ('SpareTireHub', '備胎輪轂'),
         ('GasCan', '油桶'), ('GasCap', '油桶蓋'), ('Hardtop', '硬頂'), ('Tuer', '半門'), ('license_plate', '車牌'), ('Stand_Base', '展示架底座'),
         ('Stand_Plate', '展示架托盤'), ('lower_link', '下連桿'), ('upper_link', '上連桿'), ('steering_rod', '轉向推桿'), ('tie_road', '轉向拉桿'),
         ('BumperFront_lightsupport', '前保險桿（可裝 LED）'), ('Grill', '水箱罩（頭燈版）'), ('Bezel', '頭燈框（頭燈版）'), ('Header', '水箱上蓋板（頭燈版）'),
         ('ECSMount', '電變座（頭燈版）'), ('AxleCenterRear', '可調後橋差速殼'), ('AxleCenter', '可調前橋差速殼'), ('TieRod', '轉向拉桿'),
         ('DifferentialGuard', '差速器護板'), ('SportySeat', '跑車座椅'), ('TireCarrier', '備胎架'), ('TireMount', '備胎座'), ('HoodStack', '引擎蓋（通氣管）'),
         ('HoodScoop', '引擎蓋（進氣口）'), ('IntakeHoodPlate', '進氣底板'), ('IntakeFilter', '濾芯'), ('IntakeTop', '進氣上蓋'), ('IntakeBottom', '進氣下座'),
         ('BassBumperWinch', '管狀保險桿（絞盤座）'), ('BassBumper', '管狀保險桿'), ('YJhood', 'YJ 引擎蓋'), ('YJgrill', 'YJ 水箱罩'), ('YJblinker', 'YJ 方向燈'),
         ('YJheadLight', 'YJ 頭燈'), ('YJBassBumper', 'YJ 管狀保險桿'), ('YJBumper', 'YJ 保險桿'), ('CutFender', '剪裁翼子板'), ('BodyCenterLower', 'Morrigan 用（不用印）')]


def zh_of(key):
    pid, f = key.split(':', 1)
    ok = our_key(key)
    if ok and ok in ZH:
        return ZH[ok]
    if f in ZH:
        return ZH[f]
    if f in PAGE_WORDS.get(pid, {}):
        return PAGE_WORDS[pid][f]
    for w, z in WORDS:
        if w in f:
            side = '左' if re.search(r'Left|L$', f) else '右' if re.search(r'Right|R$', f) else ''
            return z + (' ' + side if side and side not in z else '')
    return f


def copies_of(f):
    m = re.search(r'(\d)X', f) or re.search(r'X(\d)', f)
    return int(m.group(1)) if m else 1


def author_infill(key):
    pid, f = key.split(':', 1)
    if f.startswith('031Radiator'):
        return '30%（直線、頂底層 0）'
    if pid == C.HITCH:
        return '90%'
    if pid == C.PRINTED:
        return '20%'
    if re.match(r'038', f) or re.match(r'B1[3-6]Roll|C09|B01RoofRack', f):
        return '25%'
    if pid == C.MAIN and re.match(r'(06[3-9]|07[0-3]|20\d)', f):
        return '80%'
    if pid == C.WS4 and re.match(r'(30[6-9]|31[0-4]|31[78])', f):
        return '80%'
    if pid == C.HC and f.startswith('LinkLower'):
        return '80%'
    if pid == C.AFTER and re.match(r'(AA\d|H|I|J|[PQRS](Wheel|Locker|Alloy|Mag|Bead))', f):
        return '80%'
    if pid in ('992063',):
        return '80%'
    return '15%'


def category(key):
    pid, f = key.split(':', 1)
    n = re.match(r'0*(\d+)', f)
    if pid == C.MAIN and n:
        x = int(n.group(1))
        if x == 0:
            return '0 測試塊'
        if 200 <= x <= 209:
            return '4 車橋'
        if 63 <= x <= 73:
            return '5 連桿與輪框'
        if 43 <= x <= 62 and x not in (57, 58, 60, 62):
            return '2 車架、保險桿、尾門'
        return '1 車身、內裝、燈具'
    return {C.WS4: '3 4WS', C.HC: '2 車架、保險桿、尾門', C.CHEAT: '6 變速箱', C.PRINTED: '6 變速箱', C.TOP: '7 車門與車頂',
            C.HITCH: '2 車架、保險桿、尾門'}.get(pid, '8 選配件')


def part(key):
    if key not in files:
        raise SystemExit(f'找不到檔案：{key}')
    pid, f = key.split(':', 1)
    ok = our_key(key)
    o = OURS.get(ok) if ok else None
    return {'page': pid, 'file': files[key]['file'], 'zh': zh_of(key), 'n': copies_of(f), 'cat': category(key), 'ai': author_infill(key),
            'om': o[0] if o else None, 'oi': o[1] if o else None, 'ow': o[2] if o else None, 'date': files[key]['date']}


parts = {}


def use(keys):
    for k in keys:
        parts[k] = part(k)
    return list(keys)


def expand(opt):
    """把 addPrefix／addPage 展開成零件代號"""
    out = []
    for page, pre in opt.get('addPrefix', []):
        out += [k for k in files if k.startswith(f'{page}:{pre}')]
    ap = opt.get('addPage')
    for page in ([ap] if isinstance(ap, str) else ap or []):
        out += [k for k in files if k.startswith(page + ':')]
    return out


# 主車預設
base = [k for k in files if k.startswith(C.MAIN + ':') and k.split(':', 1)[1] not in C.MAIN_SKIP]
use(base)
groups = []
need_imgs = {}
for g in C.GROUPS:
    G = {k: v for k, v in g.items() if k != 'options'}
    G['options'] = []
    for o in g['options']:
        O = {k: v for k, v in o.items() if k not in ('addPrefix', 'addPage', 'addIf', 'photo', 'preview', 'bomIf', 'wheelset')}
        O['add'] = use(list(dict.fromkeys(o.get('add', []) + expand(o))))
        O['remove'] = o.get('remove', [])
        if 'wheelset' in o:
            O['wheelset'] = {k: use(v) for k, v in o['wheelset'].items()}
            for v in O['wheelset'].values():
                for k in v:
                    parts[k]['cat'] = '5 連桿與輪框'
        O['addIf'] = []
        for c in o.get('addIf', []):
            O['addIf'].append({'when': c['when'], 'add': use(list(dict.fromkeys(c.get('add', []) + expand(c))))})
        O['bomIf'] = []
        for c in o.get('bomIf', []):
            b = c['bom']
            O['bomIf'].append({'when': c['when'], 'bom': [{'item': i, 'qty': q} for i, q in C.TRANS_BOM[b]] if isinstance(b, str) else b})
        if o.get('preview'):
            fk = o['preview']
            if files.get(fk, {}).get('preview'):
                O['img'] = f'img/p_{re.sub(r"[^A-Za-z0-9_.-]", "_", fk)}.jpg'
                need_imgs[O['img']] = 'https://media.printables.com/' + files[fk]['preview']
        elif o.get('page') and pages.get(o['page'], {}).get('images'):
            pass
        if o.get('photo'):
            pg, i = o['photo']
            if len(pages[pg]['images']) > i:
                O['photo'] = f'img/g_{pg}_{i}.jpg'
                need_imgs[O['photo']] = 'https://media.printables.com/' + pages[pg]['images'][i]
        ph = getattr(C, 'PHOTOS', {}).get((g['id'], o['id']), {})
        if ph.get('photo'):
            o = {**o, 'photo': ph['photo']}
            pg, i = ph['photo']
            O['photo'] = f'img/g_{pg}_{i}.jpg'
            need_imgs[O['photo']] = 'https://media.printables.com/' + pages[pg]['images'][i]
        if ph.get('gallery'):
            O['gallery'] = []
            for pg, i, cap in ph['gallery']:
                rel = f'img/g_{pg}_{i}.jpg'
                need_imgs[rel] = 'https://media.printables.com/' + pages[pg]['images'][i]
                O['gallery'].append({'src': rel, 'cap': cap})
        if not O.get('img') and not O.get('photo') and o.get('page') and pages.get(o['page'], {}).get('images'):
            pg = o['page']
            O['photo'] = f'img/g_{pg}_0.jpg'
            need_imgs[O['photo']] = 'https://media.printables.com/' + pages[pg]['images'][0]
        G['options'].append(O)
    groups.append(G)
# 電變座、測試塊
for k in [f'{C.MAIN}:032ECSMount30-60AMP', f'{C.MAIN}:033ECSMount80AMP', f'{C.HEAD}:04ECSMount30', f'{C.HEAD}:04ECSMount80', f'{C.MAIN}:00TestBlock']:
    use([k])
for k, v in parts.items():
    if k.startswith(C.HC + ':Adjustable') or k.startswith(C.HC + ':B540C') or k.startswith(C.HC + ':MotorMount') or k.startswith(C.HC + ':BeltCover') or k.startswith(C.HC + ':Transfer'):
        v['cat'] = '6 變速箱'
    if k.startswith(C.HC + ':LinkLower'):
        v['cat'] = '5 連桿與輪框'

ESC = {'d3530': '30', 'd3536': '30', 'd3542_1000': '30', 'd3542_1450': '30', 'h4250': '80', 'brushed540': '30'}

PITFALLS = [
    ('採購', '40T 同步輪買「軸孔上限 10mm」的便宜款；肩部大、軸孔可到 15mm 的是錯的（作者原文）。', 'author'),
    ('採購', 'GT2 皮帶一定買閉口（無接頭）款，接起來的開口皮帶撞一下就斷。', 'ours'),
    ('採購', '前橋半軸要 SCX10 II／AR44（90046）用的萬向節款，不是初代 SCX10（AR60），也不要 CV 球籠款。', 'ours'),
    ('採購', '輪胎寬度標示常差 1–2mm：到貨先量胎唇寬度，再決定印窄胎或寬胎輪框。', 'ours'),
    ('採購', 'LED 燈大多標 3.7–5V，Fusion SE 的 BEC 是 6V：加 5V 降壓模組，或買標明 4.8–6V 的燈組。', 'ours'),
    ('採購', '螺絲最省事：買 M2／M3 內六角組合盒，再單獨補大量的規格（M2×10、M2×6、M3×10、M3×14）。', 'ours'),
    ('列印', '作者照強化 PLA 設計，內建支撐和公差都照 PLA 調：0.4 噴嘴、層高 0.2（不能更高）、牆 0.8mm、不開支撐。', 'author'),
    ('列印', '散熱格柵 031 要特殊設定：直線填充 30%、頂層 0、底層 0。自己重新合盤時這個設定很容易掉。', 'ours'),
    ('列印', '自己重新合盤（把零件搬到同一盤）時，逐件填充會被盤的預設值蓋掉：車橋、轉向節、輪轂要記得改回 80%。我們就因此有一盤 PA-CF 用 35% 印了。', 'ours'),
    ('列印', '前翼子板頂部的懸垂很極限，頂部要朝向印表機散熱風扇。', 'author'),
    ('列印', 'PETG-CF、PA-CF 會磨損原廠不鏽鋼噴嘴，先換硬化鋼熱端。PA-CF 一定要烘乾（我們用 80°C 24 小時）。', 'ours'),
    ('列印', '每種材料先印一個 00TestBlock，壓一顆 MR115 試鬆緊；球頭太緊可以到 Requested parts 下載縮小 0.1／0.2mm 的連桿。', 'author'),
    ('組裝', '5mm 棒穿不進軸承：先修毛邊，再用小電鑽夾著棒子在 100 號砂紙裡轉一下縮徑（不要用大電鑽、絕對不要用車床）。', 'author'),
    ('組裝', '前翼子板避震座上方要鎖 M2×25 補強螺絲（作者 2023-11 更新，不鎖會裂）。', 'author'),
    ('組裝', '高底盤＋Full Top：座椅底座 B11 會頂到 M3 圓柱頭螺絲，改用圓頭螺絲。', 'author'),
    ('組裝', '用 Fusion SE 不裝電變座，開關要自己用雙面膠或束線帶固定。', 'author'),
]
PRINT_SETTINGS = {'author': '強化 PLA（作者推薦 Prusa PLA、Inland Plus、CC3D Max；Hatchbox 測試不好）；0.4 噴嘴、層高 0.2、牆 0.8mm（2 圈）；一般 15%、防滾架 25%、車橋／連桿／輪轂／輪框 80%（100% 會放大過擠問題）；不開支撐。',
                  'ours': '結構件改用碳纖料：車橋、轉向節、輪轂、全部連桿、B540C、前車架用 PA-CF；車架、輪框用 PETG-CF；保險桿、側踏板、鉸鏈扣具用 PETG；車身外觀照作者用 PLA。'}

data = {'fetched': index.get('fetched'), 'pages': pages, 'parts': parts, 'base': base, 'groups': groups,
        'items': {k: {**v, 'tip': list(v['tip']) if 'tip' in v else None} for k, v in C.ITEMS.items()},
        'baseBom': [{'item': i, 'qty': q} for i, q in C.BASE_BOM], 'presets': C.PRESETS, 'esc': ESC,
        'escParts': {'30': f'{C.MAIN}:032ECSMount30-60AMP', '80': f'{C.MAIN}:033ECSMount80AMP', '30led': f'{C.HEAD}:04ECSMount30', '80led': f'{C.HEAD}:04ECSMount80'},
        'test': f'{C.MAIN}:00TestBlock', 'pitfalls': PITFALLS, 'printSettings': PRINT_SETTINGS}
os.makedirs(SITE, exist_ok=True)
open(os.path.join(SITE, 'data.js'), 'w', encoding='utf-8').write('window.THUMPER = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
print('parts', len(parts), 'groups', len(groups), 'options', sum(len(g['options']) for g in groups), 'images', len(need_imgs))

if '--no-img' not in sys.argv:
    from PIL import Image
    os.makedirs(os.path.join(SITE, 'img'), exist_ok=True)
    tmp = os.path.join(HERE, '_imgtmp'); os.makedirs(tmp, exist_ok=True)

    def get(item):
        rel, url = item
        out = os.path.join(SITE, rel)
        if os.path.exists(out):
            return
        t = os.path.join(tmp, os.path.basename(rel) + '.src')
        subprocess.run(['curl', '-s', '-L', '-o', t, url])
        try:
            im = Image.open(t).convert('RGB')
            if rel.startswith('img/p_'):
                bb = im.convert('L').point(lambda v: 255 if v > 18 else 0).getbbox()
                if bb:
                    w, h = bb[2] - bb[0], bb[3] - bb[1]; pad = int(max(w, h) * .12)
                    im = im.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad), min(im.height, bb[3] + pad)))
                im.thumbnail((360, 360))
            else:
                im.thumbnail((900, 900))
            im.save(out, quality=80, optimize=True)
        except Exception as e:
            print('img fail', rel, e)
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(get, need_imgs.items()))
    print('images ok', len(os.listdir(os.path.join(SITE, 'img'))))
