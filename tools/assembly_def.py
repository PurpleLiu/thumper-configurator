# 組裝階段、官方影片、齒比資料（由 build.py 匯出到 data.js）
# 條件寫法跟 catalog_def 一樣：when／unless = {群組: [選項, ...]}
# src：author 作者原文、ours 我們的經驗、guess 推測
import re
from catalog_def import MAIN, WS4, HC, CHEAT, PRINTED, TOP, AFTER, HEAD, HITCH, GOPRO

FULL = {'top': ['full', 'fullrack']}
FULLISH = {'top': ['full', 'fullrack', 'noneft']}
HALF = {'top': ['half']}
CHEATERS = ['ch_a2', 'ch_a540', 'ch_b2', 'ch_b540', 'ch_c2', 'b540c_fixed', 'b540c_adj']
PRINTEDS = ['pr_a', 'pr_b', 'pr_c', 'pr_g']


def V(vid, zh, **kw):
    return {'id': vid, 'zh': zh, **kw}


def S(sid, text, src=None, **kw):
    return {'id': sid, 'text': text, 'src': src, **kw}


def W(text, src, **kw):
    return {'text': text, 'src': src, **kw}


STAGES = [
    {'id': 'prep', 'zh': '準備：測試塊、5mm 棒', 'videos': [V('5iUjPRGPsHA', '影片 1／8（開頭有工具和公差說明）')],
     'steps': [
         S('p1', '每種要用的材料各印一個 00TestBlock，壓一顆 MR115（5×11×4）試鬆緊，也試球頭。', 'author'),
         S('p2', '球頭太緊或太鬆：到 Requested parts（396992）下載縮小 0.1／0.2mm 的連桿。', 'author'),
         S('p3', '5mm 棒用黃銅棒最好切。穿不進軸承就先修毛邊，再用小電鑽夾著棒子在 100 號砂紙裡轉一下縮徑；不要用大電鑽，也不要用車床。', 'author'),
         S('p4', '裁變速箱的 5mm 棒：64mm、84mm 各一支，兩端倒角。', 'author', when={'trans': CHEATERS}),
         S('p4p', '裁變速箱的 5mm 棒：113mm、65mm、35mm 各一支（舊影片說 114mm，作者 2023-02 改成 113mm），兩端倒角。', 'author', when={'trans': ['pr_a', 'pr_b']}),
         S('p4g', '裁變速箱的 5mm 棒：長度照 A 或 B 的影片（G 只換馬達端零件，推測跟 A／B 一樣是 113mm、65mm、35mm）。', 'guess', when={'trans': ['pr_g']}),
         S('p4c', '裁變速箱的 5mm 棒：80mm、65mm 各一支，兩端倒角。', 'author', when={'trans': ['pr_c']}),
         S('p5', '要印 PETG-CF／PA-CF 的話先換硬化鋼噴嘴；PA-CF 先烘乾（我們用 80°C 24 小時）。', 'ours'),
     ],
     'warns': [W('作者照強化 PLA 設計：0.4 噴嘴、層高 0.2（不能更高）、牆 0.8mm、不開支撐（模型有內建支撐）。', 'author')]},

    {'id': 'body1', 'zh': '車身 1：前車斗、儀表、前翼子板、側踏板', 'videos': [V('5iUjPRGPsHA', '影片 1／8')],
     'steps': [
         S('b1-1', '拆掉 001 前車斗、008／011 翼子板的內建支撐。'),
         S('b1-2', '002 儀表、003 扶手裝到 001；裝 005 轉向柱、006 方向盤、004 排檔桿。'),
         S('b1-3', '007 前圍板鎖到 001 上方。'),
         S('b1-4', '009／012 加 2 個 010 組成引擎蓋扣，裝到翼子板外側。'),
         S('b1-5', '翼子板換成 AE 剪裁版（左右各一）。', when={'fender': ['AE']}),
         S('b1-6', '翼子板避震座上方鎖 M2×25 補強螺絲（作者 2023-11 更新，不鎖會裂）。', 'author'),
         S('b1-7', '翼子板和 013／014 側踏板鎖到 001。'),
     ],
     'warns': [W('車門、Full Top、Half Top 需要 2023-11 之後的新版 001、015、075（有鉸鏈和車頂孔），舊檔要重新下載。', 'author',
                 when={'doors': ['official'], 'top': ['full', 'fullrack', 'half']}, any=True),
               W('前翼子板頂部的懸垂很極限，列印時頂部朝向散熱風扇。', 'author')]},

    {'id': 'body2', 'zh': '車身 2：後車斗、尾燈、水箱罩、頭燈',
     'videos': [V('vmGx-jKRtDs', '影片 2／8'), V('OYbu29Z1mPk', '會亮的頭燈（1061913）', when={'headlight': ['led']})],
     'steps': [
         S('b2-1', '0016／0017 後側踏板裝到 015 後車斗，再把前後車斗接起來。'),
         S('b2-2', '018 尾燈框加 019 尾燈罩裝到車尾兩角。'),
         S('b2-3', '裝 020／021 冰箱、022 假地板、023／024 油箱。', unless=HALF),
         S('b2-3h', 'Half Top 的後車斗內裝換成 C01–C04（照 Half Top 影片）。', 'guess', when=HALF),
         S('b2-4', '025 水箱罩裝 026 頭燈框、027 燈罩、028／029 方向燈。', unless={'headlight': ['led'], 'hood': ['yj']}, any=True),
         S('b2-4l', '頭燈版水箱罩 01Grill 裝 2 個 02Bezel、027 燈罩、028／029 方向燈；照頭燈影片把 22mm LED 裝進去，線先留好。', when={'headlight': ['led']}),
         S('b2-4y', 'YJ 方燈車頭：水箱罩換 ABYJgrill，頭燈換 ADYJheadLight，方向燈換 ADYJblinker。', when={'hood': ['yj']}),
         S('b2-5', '水箱上蓋板（030，頭燈版是 03Header）、031 散熱格柵、034 引擎蓋扣組在一起，鎖到翼子板和前車斗之間。'),
         S('b2-6', '電變座：30–60A 用 032、80A 用 033；裝會亮的頭燈要改用頭燈頁的 04ECSMount。', unless={'motor': ['fusion']}),
         S('b2-6f', 'Fusion SE 是馬達電變一體，不裝電變座；開關用雙面膠或束線帶固定。', 'author', when={'motor': ['fusion']}),
     ],
     'warns': [W('031 散熱格柵要特殊設定：直線填充 30%、頂層 0、底層 0，才會印成鏤空。自己重新合盤時這個設定很容易掉。', 'author'),
               W('LED 大多標 3.7–5V，Fusion SE 的 BEC 是 6V：加 5V 降壓模組，或買標明 4.8–6V 的燈。', 'ours', when={'headlight': ['led']})]},

    {'id': 'body3', 'zh': '車身 3：引擎蓋、防滾架、座椅',
     'videos': [V('YYE_TkPQzj0', '影片 3／8'), V('L6UjHHtPF4k', '座椅底座 B11（Full Top）', when=FULLISH),
                V('NOItUGeecos', 'Half Top 組裝', when=HALF)],
     'steps': [
         S('b3-1', '036／037 鉸鏈裝到 035 引擎蓋和 007 前圍板，確認開關順、兩側扣得上。', when={'hood': ['orig', 'yj']}),
         S('b3-1a', '引擎蓋換 A01HoodStack，進氣組件 AorB02–05 照頁面組，再裝 036／037 鉸鏈。', when={'hood': ['A']}),
         S('b3-1b', '引擎蓋換 B01HoodScoop，進氣組件 AorB02–05 照頁面組，再裝 036／037 鉸鏈。', when={'hood': ['B']}),
         S('b3-2', '038 一體防滾架裝進車斗。', when={'top': ['none', 'mast52']}),
         S('b3-2t', '038 三件式（M／L／R）組成防滾架，再裝進車斗。', when={'top': ['none3']}),
         S('b3-2f', 'B13 主框、2 支 B14 前桿、B15／B16 後桿組成防滾架。先沿細縫把內建支撐分段剪開再剝，不要直接扳管子。', 'author', when=FULLISH),
         S('b3-2h', 'C09 防滾架加 C13 墊片（照 Half Top 影片）。', when=HALF),
         S('b3-3', '039 中央扶手座、040 扶手蓋、041 杯架，2 張座椅鎖到車斗。', unless={'top': ['full', 'fullrack', 'noneft', 'half']}),
         S('b3-3f', 'B11 座椅底座和 B12 中央扶手座鎖上，裝 040、041；座椅鎖在 B11 上。', when=FULLISH),
         S('b3-3h', 'C05 座椅底座和 C06 中央扶手座鎖上，裝 040、041；座椅鎖在 C05 上。', when=HALF),
         S('b3-4', '座椅用 O 跑車座椅（印 2 個）。', when={'seat': ['O']}),
     ],
     'warns': [W('Full Top 放不進原廠 038 防滾架（一體或三件式都不行），要用 B13–B16。', 'author', when=FULL),
               W('高底盤加 Full Top：B11 座椅底座下方會頂到 M3 圓柱頭螺絲，那幾顆改用圓頭螺絲。', 'author', when={'chassis': ['hc'], 'top': ['full', 'fullrack', 'noneft']})]},

    {'id': 'frame', 'zh': '底盤 1：中車架、前車架、前伺服、前保險桿',
     'videos': [V('fujb8-Tcgms', '影片 4／8（2023-11 更新版）'), V('eOwHuJb2ZyU', '影片 4／8（舊版）', old=True),
                V('v7iBpwpZv34', '高底盤組裝', when={'chassis': ['hc']}),
                V('iOoUGm3lwjE', '高底盤：舊車拆解（原版底盤已經組好才看）', when={'chassis': ['hc']})],
     'steps': [
         S('f1', '043 中車架、044 連接件、045／046 前車架組起來。', unless={'chassis': ['hc']}),
         S('f1h', '高底盤的中車架、前車架左右，加 044 連接件（不用 043、045、046）。', when={'chassis': ['hc']}),
         S('f2', '前車架伺服座鎖 M2×25、M2×15 補強螺絲（高底盤前車架的孔已內建）。', 'author'),
         S('f3', '前伺服通電置中後再裝舵臂，裝到前車架。'),
         S('f4', '鎖上前保險桿。'),
         S('f4w', 'F 保險桿有絞盤座：絞盤先試放再鎖。', 'guess', when={'bumper': ['F']}),
     ],
     'warns': [W('高底盤不用 074 底板。', 'author', when={'chassis': ['hc']})]},

    {'id': 'trans', 'zh': '底盤 2：變速箱',
     'videos': [V('5ARl5_8EhPI', '列印齒輪＋D3530', when={'trans': PRINTEDS, 'motor': ['d3530']}),
                V('hCUsIikkKeA', '列印齒輪＋D3542 1000kv', when={'trans': PRINTEDS, 'motor': ['d3542_1000']}),
                V('Cd5CS3hWXYk', '列印齒輪＋D3542 1450kv', when={'trans': PRINTEDS, 'motor': ['d3542_1450']}),
                V('D6iVMLPrj9U', '列印齒輪＋Hobbyhh 4250', when={'trans': PRINTEDS, 'motor': ['h4250']}),
                V('wBTb4pj5i3o', '金屬齒輪 A2', when={'trans': ['ch_a2']}),
                V('RqDdiswYI5Y', '金屬齒輪 A540', when={'trans': ['ch_a540']}),
                V('paxRNQ038fk', '金屬齒輪 B2', when={'trans': ['ch_b2', 'ch_c2']}),
                V('nWWE1DdX4_o', '金屬齒輪 B540（B540C 的齒輪皮帶一樣，可以對照）', when={'trans': ['ch_b540', 'b540c_fixed', 'b540c_adj']}),
                V('Da3Pi4hBoUU', 'B540C 變速箱（高底盤）', when={'trans': ['b540c_fixed', 'b540c_adj']})],
     'steps': [
         S('t1', '照影片把軸承、軸、齒輪裝進主殼和傳動箱。', when={'trans': PRINTEDS}),
         S('t1c', '照影片把軸承、5mm 棒、同步輪、皮帶裝進主殼和傳動箱；用 M5 墊片消除軸向間隙、讓皮帶對直。', when={'trans': CHEATERS}),
         S('t2', 'C2 沒有自己的影片：照 A2／B2 的結構組。', 'author', when={'trans': ['ch_c2']}),
         S('t3', '同步輪的止付螺絲、馬達螺絲一律上螺絲膠。', 'ours', when={'trans': CHEATERS}),
         S('t4', '可調版：馬達座槽裡放一顆 M3 螺帽，頂部 M3×16 往上拉到皮帶有張力（約 0.5mm），再鎖馬達座螺絲。', 'author', when={'trans': ['b540c_adj']}),
         S('t5', '轉輸出軸確認順、不磨殼，再鎖蓋子。'),
     ],
     'warns': [W('40T 同步輪買「軸孔上限 10mm」的便宜款；肩部大、軸孔可到 15mm 的會卡住。', 'author', when={'trans': CHEATERS}),
               W('GT2 皮帶一定買閉口（無接頭）款，自己接的皮帶撞一下就斷。', 'ours', when={'trans': CHEATERS}),
               W('金屬齒輪變速箱摩擦小，上坡比較容易倒退；搭 Fusion SE 就很穩，用其他馬達要調電變。', 'author', when={'trans': ['ch_a2', 'ch_b2']}),
               W('高底盤只能用 B540C，不能用 769045 的 B540 外殼（主殼短 9mm）。', 'author', when={'chassis': ['hc']})]},

    {'id': 'rear', 'zh': '底盤 3：後車架、尾門電池盒、後保險桿、拖車鉤',
     'videos': [V('1JAfCCM61l0', '影片 5／8（更新版）'), V('3MqvjHLNRvY', '4WS 組裝', when={'steer': ['ws4']}),
                V('ZgsWcj7UD6g', '4WS：舊車拆解準備（原版已經組好才看）', when={'steer': ['ws4']}),
                V('uCtInqaMiSA', 'Pintle 拖車鉤', unless={'hitch': ['none']})],
     'steps': [
         S('r1', '048／049 後車架、050／051 避震座、052 橫樑、054／055 連接件、053 尾門電池盒。', unless={'steer': ['ws4']}),
         S('r1w', '4WS：300／301 後車架、319／320 避震座、052 橫樑、054 連接件、302 側穩定桿座、303 後伺服座、315 尾門電池盒（不用 048–051、053、055、061）。', 'author', when={'steer': ['ws4']}),
         S('r2', '後伺服通電置中後裝上；用 304 線蓋、305／WireClip 線夾、316 線蓋整理走線。', when={'steer': ['ws4']}),
         S('r3', '後保險桿 056、059，057 倒車燈、058 車牌、060 拉把、062 油箱蓋。', unless={'carrier': ['AB', 'AC']}),
         S('r3c', '後保險桿 056、059，057 倒車燈、060 拉把、062 油箱蓋；備胎架裝在車牌位置（不用 058）。', when={'carrier': ['AB', 'AC']}),
         S('r4', 'Pintle 拖車鉤用 3 顆 M2×8 鎖在 052 後車架橫樑，不要鎖在後保險桿（會跟電池一起滑出來）；鉤子用 M3 吊環螺絲剪開。', 'author', unless={'hitch': ['none']}),
         S('r5', '電池放進尾門電池盒試裝，確認滑進滑出順。電池盒不要用 ABS／PC 印（會收縮）。'),
     ],
     'warns': [W('4WS 一定用 300／301 後車架，跟 048／049 尺寸不同，不能混用。', 'author', when={'steer': ['ws4']})]},

    {'id': 'faxle', 'zh': '車橋 1：前橋', 'videos': [V('vJ_oycGUkpc', '重型前橋 6B'), V('sQ5-PiZHEC4', '前橋 6-B（舊版）', old=True)],
     'steps': [
         S('a1', '清 204、205／206、207／208 的內建支撐，確認軸承座平整。'),
         S('a2', '差速殼換 H 可調齒隙版。', when={'func': ['H']}),
         S('a3', '204 差速殼裝 AR44 8T 小齒輪和軸承，確認轉動順。'),
         S('a4', '33T 大齒輪上黃油放進差速殼，接左右橋殼。'),
         S('a5', '穿入前半軸，轉向節壓軸承後裝上，確認左右擺動順。'),
         S('a6', '套上 209 輪轂（12mm 六角）。'),
     ],
     'warns': [W('前半軸買 SCX10 II／AR44（90046）前橋用的萬向節款，不是初代 SCX10（AR60），也不要 CV 球籠款。', 'ours'),
               W('傘齒比用 8T-33T；只有並聯 2S 的高速版才用 8T-24T。', 'author'),
               W('AA 強化車橋與轉向節作者不建議，裝之前看選項說明。', 'author', when={'func': ['AA']})]},

    {'id': 'raxle', 'zh': '車橋 2：後橋',
     'videos': [V('Z6tbW_wxCDI', '後橋 6-A', unless={'steer': ['ws4']}), V('gQJQMzdSiPQ', '重型 4WS 後轉向橋 6C', when={'steer': ['ws4']}),
                V('v-watdKg1SQ', '4WS 後橋 6-C（舊版）', old=True, when={'steer': ['ws4']})],
     'steps': [
         S('ra1', '200 差速殼、201／203 橋殼、2 個 202 軸承座，裝第二組 AR44 齒輪和後半軸。', unless={'steer': ['ws4']}),
         S('ra1r', '（選做）201／203 後橋殼可以各穿一支 5mm×63mm 棒補強（作者 2024-08 更新）。', 'author', unless={'steer': ['ws4']}),
         S('ra2', '後差速殼換 I 可調齒隙版。', when={'func': ['I']}),
         S('ra1w', '309 差速殼、308／310 橋殼、311／312 轉向節（不是再印一組 207／208），照 6C 做橋殼補強。', 'author', when={'steer': ['ws4']}),
         S('ra3', '大齒輪方向要跟前橋一致，前後橋才不會互頂。', 'ours'),
     ],
     'warns': [W('311／312 後轉向節 2025-03 改成高拉桿座版、後橋殼 2025-04 加補強孔；舊檔要重新下載。', 'author', when={'steer': ['ws4']})]},

    {'id': 'links', 'zh': '底盤 4：連桿、傳動軸、避震、輪框（第一次試跑）',
     'videos': [V('GBYVsLcDTF0', '影片 7／8（更新版）'), V('v7iBpwpZv34', '高底盤組裝（下連桿、變速箱位置）', when={'chassis': ['hc']})],
     'steps': [
         S('l1', '前懸吊：前下連桿×2、064 前上連桿、066 側穩定桿、063 拉桿、069 推桿。', unless={'func': ['J']}),
         S('l1j', '前懸吊：前下連桿×2、064 前上連桿、066 側穩定桿、J 加長拉桿、069 推桿。', when={'func': ['J']}),
         S('l1h', '前後下連桿用高底盤版（比原版長約 5mm）。', 'author', when={'chassis': ['hc']}),
         S('l2', '後懸吊：067 後上連桿×2、068 後下連桿×2。', unless={'steer': ['ws4']}),
         S('l2w', '後懸吊（4WS）：後下連桿×2、307 後上連桿、306 後穩定桿、313 後拉桿、314 後推桿，用 317（6mm）／318（2mm）墊片調位置。', 'author', when={'steer': ['ws4']}),
         S('l3', '變速箱放進中車架，裝前後傳動軸（5mm 孔），組好後量長度要在 105–155mm 的伸縮範圍內。', 'author'),
         S('l4', '裝 4 支避震：前上座在翼子板，後上座在後避震座。'),
         S('l5', '組輪框：外片和鎖圈夾住胎唇，加內片、內環；外露鎖圈款最後鎖鎖圈環。用 M4 防鬆螺帽鎖上輪軸。'),
         S('l6', '第一次通電：先上架空轉，再到平地、小坡。滿舵檢查輪胎、避震、連桿有沒有干涉，皮帶有沒有跳齒。', 'ours'),
     ],
     'warns': [W('避震不能超過 100mm；作者推薦內簧款、中或重彈簧。', 'author'),
               W('寬輪框配 50–52mm 胎，裝好後打滿舵確認不碰翼子板和連桿。', 'ours', when={'width': ['wide', 'both']})]},

    {'id': 'final', 'zh': '收尾：擋風玻璃、雨刷、後照鏡',
     'videos': [V('YPlKXbEqJY4', '影片 8／8（更新版）'), V('2gUOvSiTj0M', '影片 8／8（舊版）', old=True)],
     'steps': [
         S('e1', '074 底板鎖到底盤。', unless={'chassis': ['hc']}),
         S('e2', '裁 0.4mm 透明壓克力片當擋風玻璃，用 076 膠條夾進 075 擋風玻璃框。'),
         S('e3', '裝 077–080 鉸鏈。', unless=FULL),
         S('e3f', '只裝 079、080 鉸鏈（Full Top 不用 077、078）。', 'author', when=FULL),
         S('e4', '裝 2 支 081 雨刷，組 082 後照鏡殼、083 鏡面、084 支桿。'),
         S('e5', '整理全車走線，確認車身和底盤鎖牢。'),
     ],
     'warns': [W('075 外角的支撐要先用尖嘴鉗扭掉，不然裝不進車頂框。', 'ours', when={'top': ['full', 'fullrack', 'half']})]},

    {'id': 'doors', 'zh': '選配：車門', 'when': {'doors': ['official', 'mast52']},
     'videos': [V('meKWotT7hmw', '車門組裝（更新版）', when={'doors': ['official']}), V('dg3jTCnxxh8', '車門組裝（舊版）', old=True, when={'doors': ['official']})],
     'steps': [
         S('d1', 'A03／A06 車門內板裝到 A01／A04 車門。', when={'doors': ['official']}),
         S('d2', '裝 A02／A05 門鎖，確認內外門把都能動。', when={'doors': ['official']}),
         S('d3', 'A07–A14 鉸鏈裝到車斗和車門（A08／A12 是後照鏡座），掛上車門調到開關順。', when={'doors': ['official']}),
         S('d4', 'MaSt52 半門照 638066 頁面說明安裝。', when={'doors': ['mast52']}),
     ],
     'warns': [W('作者沒列車門和車頂的螺絲，我們從孔位估約 70–90 顆 M2，長度看影片。', 'ours', when={'doors': ['official']})]},

    {'id': 'top', 'zh': '選配：車頂', 'when': {'top': ['full', 'fullrack', 'half', 'mast52']},
     'videos': [V('v_31ZWYUV-c', 'Full Top 組裝', when=FULL), V('NOItUGeecos', 'Half Top 組裝', when=HALF)],
     'steps': [
         S('tp1', 'B01RoofRack 車頂架鎖到 B01FullTopMainWRack。', when={'top': ['fullrack']}),
         S('tp2', 'B02 後框裝到車頂本體，用 B06–B09 鉸鏈掛上 B03 後掀門。', when=FULL),
         S('tp3', '裝 B04 把手×2、B05 門扣×2、B10 卡扣，確認後掀門扣得住。', when=FULL),
         S('tp4', '車頂蓋到防滾架和車斗上鎖好。', when=FULL),
         S('tp5', 'C07 Half Top 加 C08 膠條，照 Half Top 影片裝到防滾架上。', when=HALF),
         S('tp6', 'MaSt52 硬頂照 687781 頁面說明，裝在原廠 038 防滾架上。', when={'top': ['mast52']}),
     ],
     'warns': [W('Full Top 照作者檔案方向直立印，模型有內建支撐，不要開支撐。', 'author', when=FULL),
               W('車頂在最高處，重心會變高；爬陡坡時可以拆掉。', 'ours')]},

    {'id': 'elec', 'zh': '電控設定與試跑', 'videos': [],
     'steps': [
         S('c1', '接收器 CH1 接前轉向伺服、CH2 接電變（或 Fusion SE）。'),
         S('c2', '4WS：後伺服接 CH3，遙控器設 CH1→CH3 混控；三段開關做「反向（4WS）／關／同向（蟹行）」。', when={'steer': ['ws4']}),
         S('c3', '伺服先置中再裝舵臂，左右行程上限調到不會頂死。'),
         S('c4', '遙控器把油門加速和煞車力道調小（列印齒輪一定要）。', 'author', when={'trans': PRINTEDS}),
         S('c5', 'Fusion SE 用程式卡或 App 設拖曳煞車。', when={'motor': ['fusion']}),
         S('c6', '頭燈經 5V 降壓模組接接收器空通道。', 'ours', when={'headlight': ['led']}),
         S('c7', '兩顆伺服同時打舵時接收器會斷訊的話，加外接 BEC。', 'ours', when={'steer': ['ws4']}),
     ],
     'warns': []},
]

# 影片分頁另外列的影片（不在某個組裝階段裡）
EXTRA_VIDEOS = [
    V('jXBEKSlEzNU', 'Thumper 介紹', cat='介紹'),
    V('lh9M8WSyPVU', '高底盤介紹', cat='介紹', when={'chassis': ['hc']}),
    V('llEIOzB9Q1o', '4WS 介紹', cat='介紹', when={'steer': ['ws4']}),
    V('QE-FoBZ2vPU', '作者整理的網友實車照', cat='網友實車照'),
    V('eNKP3jivkdE', '2025 網友實車照合輯', cat='網友實車照'),
]

# 齒比：作者原文（356820、769045 頁面）
RATIO = {'pr_a': 7.5, 'pr_b': 5, 'pr_c': 1.86, 'pr_g': 7.5, 'ch_a2': 6.25, 'ch_a540': 6.25, 'ch_b2': 4, 'ch_b540': 4, 'ch_c2': 2,
         'b540c_fixed': 4, 'b540c_adj': 4}
KV = {'d3530': 1100, 'd3536': None, 'd3542_1000': 1000, 'd3542_1450': 1450, 'h4250': 800, 'fusion': 1200, 'brushed540': None}
AXLE = [(33, '8T-33T（作者建議，攀爬）'), (30, '8T-30T'), (27, '8T-27T'), (24, '8T-24T（並聯 2S 高速版）')]

# 零件屬於哪個階段：主車看檔名開頭的編號，其他頁看檔名
_MAIN_RANGES = [('prep', 0, 0), ('body1', 1, 14), ('body2', 15, 34), ('body3', 35, 42), ('frame', 43, 47), ('rear', 48, 62),
                ('links', 63, 73), ('final', 74, 84), ('raxle', 200, 203), ('faxle', 204, 209)]
_RULES = [
    ('body1', rf'^{AFTER}:AECut'),
    ('body2', rf'^{HEAD}:|^{AFTER}:AB?D?YJ(grill|blinker|headLight)'),
    ('body3', rf'^{TOP}:(B1[1-6]|C05|C06|C09|C13)|^{AFTER}:(A01Hood|AorB|B01Hood|ADYJhood|ONew)'),
    ('frame', rf'^{HC}:Frame|^{AFTER}:(EBass|FBass|ADYJBumper|ADYJBass)|^993006:'),
    ('trans', rf'^({CHEAT}|{PRINTED}):|^{HC}:(B540C|MotorMount|Transfer|BeltCover|Adjustable)'),
    ('rear', rf'^{MAIN}:WireClip|^{WS4}:(30[0-5]|315|316|319|320)|^{HITCH}:|^{AFTER}:(ABTire|ACTire|AFTire)|^437354:|^1362350:|^992013:'),
    ('faxle', rf'^{AFTER}:(AA20|HAxle)'),
    ('raxle', rf'^{WS4}:(30[89]|31[0-2])|^{AFTER}:IAxle'),
    ('links', rf'^{HC}:Link|^{WS4}:(30[67]|31[3478])|^{AFTER}:([PQRS](Whee|Locker|Alloy|Mag|BeadLocker)|JTie|NDiff)|^992063:|^1264177:'),
    ('doors', rf'^{TOP}:A\d|^638066:'),
    ('top', rf'^{TOP}:(B0|B10|C0[1-47-8])|^687781:'),
]


def stage_of(key):
    pid, f = key.split(':', 1)
    m = re.match(r'(\d+)', f)
    if pid == MAIN and m:
        n = int(m.group(1))
        for sid, a, b in _MAIN_RANGES:
            if a <= n <= b:
                return sid
    for sid, rx in _RULES:
        if re.search(rx, key):
            return sid
    return 'extra'
