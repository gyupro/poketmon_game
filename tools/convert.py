"""pokered(역어셈블리) 데이터를 Godot 프로젝트용 JSON/PNG로 변환한다.

사용법: python tools/convert.py
입력: pokered_src/   출력: game/data/*.json, game/assets/**
"""
import json
import os
import re
import shutil
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from ko_names import KO_POKEMON, KO_MOVES, KO_TYPES, KO_ITEMS, KO_TRAINERS  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "pokered_src")
OUT = os.path.join(ROOT, "game")
DATA = os.path.join(OUT, "data")
ASSETS = os.path.join(OUT, "assets")


def src(*p):
    return os.path.join(SRC, *p)


def read(*p):
    with open(src(*p), encoding="utf-8") as f:
        return f.read()


def strip_comment(line):
    # ';' 이후 주석 제거 (문자열 내부의 ';'는 pokered에서 거의 없음)
    in_str = False
    for i, c in enumerate(line):
        if c == '"':
            in_str = not in_str
        elif c == ";" and not in_str:
            return line[:i]
    return line


def lines(*p):
    for raw in read(*p).splitlines():
        yield strip_comment(raw).rstrip()


def parse_num(s):
    s = s.strip()
    if s.startswith("$"):
        return int(s[1:], 16)
    if s.startswith("%"):
        return int(s[1:], 2)
    return int(s)


def args_of(line, macro):
    rest = line.strip()[len(macro):]
    return [a.strip() for a in rest.split(",")]


def save_json(name, obj):
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def gb_rgb(r, g, b):
    return [round(r * 255 / 31), round(g * 255 / 31), round(b * 255 / 31)]


# ---------------------------------------------------------------- constants
def parse_const_list(path, macro="const"):
    """const_def 이후 const 목록을 순서대로 반환."""
    out = []
    val = 0
    for ln in lines(path):
        s = ln.strip()
        if s.startswith("const_def"):
            a = s[len("const_def"):].strip()
            val = parse_num(a.split(",")[0]) if a else 0
        elif s.startswith("const_skip"):
            a = s[len("const_skip"):].strip()
            val += parse_num(a) if a else 1
        elif s.startswith("const_next"):
            val = parse_num(s[len("const_next"):].strip())
        elif s.startswith(macro + " ") or s.startswith(macro + "\t"):
            name = args_of(s, macro)[0]
            out.append((name, val))
            val += 1
    return out


# ---------------------------------------------------------------- palettes
def parse_super_palettes():
    pals = {}
    skip = False
    for ln in read("data", "sgb", "sgb_palettes.asm").splitlines():
        s = ln.strip()
        if s.startswith("IF DEF(_BLUE)"):
            skip = True
            continue
        if s.startswith("ENDC"):
            skip = False
            continue
        if skip:
            continue
        m = re.match(r"RGB\s+([\d,\s]+);\s*(PAL_\w+)", s)
        if m:
            nums = [int(x) for x in m.group(1).replace(" ", "").split(",") if x]
            cols = [gb_rgb(*nums[i:i + 3]) for i in range(0, 12, 3)]
            pals[m.group(2)] = cols
    return pals


# ---------------------------------------------------------------- text
TEXT_REPL = [
    ("#MON", "POKéMON"), ("#", "POKé"), ("<PK><MN>", "PKMN"), ("<PKMN>", "PKMN"),
    ("<PLAYER>", "{PLAYER}"), ("<RIVAL>", "{RIVAL}"), ("<USER>", "{USER}"),
    ("<TARGET>", "{TARGET}"), ("<……>", "……"), ("<……>", "……"), ("<DOT>", "."),
    ("<LF>", ""), ("<to>", "→"),
]


def clean_text(s):
    for a, b in TEXT_REPL:
        s = s.replace(a, b)
    s = s.replace("@", "")
    return s


def parse_all_texts():
    """text/*.asm, data/text/*.asm 의 `_Label::` 블록을 문자열로."""
    texts = {}
    files = [os.path.join("text", f) for f in os.listdir(src("text")) if f.endswith(".asm")]
    files += [os.path.join("data", "text", f) for f in os.listdir(src("data", "text")) if f.endswith(".asm")]
    files += ["text.asm"]
    for rel in files:
        cur = None
        buf = []

        def flush():
            if cur is not None:
                texts[cur] = "".join(buf).strip("\n")

        for raw in read(rel).splitlines():
            ln = strip_comment(raw).rstrip()
            m = re.match(r"^(\w+)::?\s*$", ln)
            if m:
                flush()
                cur, buf = m.group(1), []
                continue
            if cur is None:
                continue
            s = ln.strip()
            m = re.match(r'^(text|line|cont|para|next|page)\s+"(.*)"', s)
            if m:
                kind, body = m.group(1), clean_text(m.group(2))
                if kind == "text":
                    if buf and not buf[-1].endswith("\f") and buf[-1] not in ("{RAM}", "{NUM}"):
                        buf.append("\n")
                    buf.append(body)
                elif kind in ("line", "cont", "next"):
                    buf.append("\n" + body)
                elif kind in ("para", "page"):
                    buf.append("\f" + body)
            elif s.startswith("text_ram"):
                buf.append("{RAM}")
            elif s.startswith("text_decimal") or s.startswith("text_bcd"):
                buf.append("{NUM}")
        flush()
    return texts


def parse_script_texts(map_name, all_texts):
    """scripts/<Map>.asm 에서 TEXT 상수 -> 텍스트 정보(라벨/트레이너)."""
    path = src("scripts", map_name + ".asm")
    if not os.path.exists(path):
        return {}, {}
    raw = [strip_comment(l).rstrip() for l in open(path, encoding="utf-8").read().splitlines()]
    # 라벨별 본문
    blocks = {}
    cur = None
    for ln in raw:
        m = re.match(r"^([\w.]+):+\s*$", ln)
        if m:
            name = m.group(1)
            if name.startswith("."):
                name = (cur.split(".")[0] if cur else "") + name
            cur = name
            blocks[cur] = []
            continue
        if cur:
            blocks[cur].append(ln.strip())
    # 트레이너 헤더
    headers = {}
    hdr_order = []
    for label, body in blocks.items():
        for s in body:
            if s.startswith("trainer "):
                a = args_of(s, "trainer")
                headers[label] = {
                    "event": a[0], "sight": parse_num(a[1]),
                    "battle": a[2], "end": a[3], "after": a[4],
                }
                hdr_order.append(label)
                break

    def far_of(label):
        """라벨 본문을 따라가 최초의 text_far 대상을 찾음."""
        body = blocks.get(label, [])
        for s in body:
            if s.startswith("text_far"):
                return s.split()[1]
        return None

    def resolve(label):
        body = blocks.get(label, [])
        info = {"label": label}
        for s in body:
            m = re.match(r"ld hl, (\w+)", s)
            if m and m.group(1) in headers:
                h = headers[m.group(1)]
                info["trainer"] = {
                    "event": h["event"], "sight": h["sight"],
                    "battle": far_of(h["battle"]), "end": far_of(h["end"]),
                    "after": far_of(h["after"]),
                }
                return info
            if s.startswith("script_mart"):
                info["mart"] = args_of(s, "script_mart")
                return info
        f = far_of(label)
        if not f:
            # text_asm 안에서 ld hl, .Text 로 부르는 첫 대사
            for s2 in body:
                m2 = re.match(r"ld hl, (\.?\w+)", s2)
                if m2:
                    nm = m2.group(1)
                    if nm.startswith("."):
                        nm = label + nm
                    f = far_of(nm)
                    if f:
                        break
        if f:
            info["text"] = f
        if body and body[0] == "text_asm":
            info["scripted"] = True
        return info

    pointers = {}
    for ln in raw:
        s = ln.strip()
        if s.startswith("dw_const"):
            a = args_of(s, "dw_const")
            pointers[a[1]] = resolve(a[0])
    return pointers, headers


# ---------------------------------------------------------------- maps
def parse_maps(pals):
    consts = {}
    order = []
    for ln in lines("constants", "map_constants.asm"):
        s = ln.strip()
        if s.startswith("map_const "):
            a = args_of(s, "map_const")
            consts[a[0]] = (int(a[1]), int(a[2]), len(order))
            order.append(a[0])
    first_indoor = order.index("REDS_HOUSE_1F")
    num_city = order.index("UNUSED_MAP_0B")

    tileset_ids = [n for n, _ in parse_const_list(os.path.join("constants", "tileset_constants.asm"))]

    # tileset -> gfx/block 파일
    ts_gfx, ts_blk = {}, {}
    pend_g, pend_b = [], []
    for ln in lines("gfx", "tilesets.asm"):
        m = re.match(r"^(\w+)_(GFX|Block)::\s*(INCBIN\s+\"([^\"]+)\")?", ln.strip())
        if not m:
            continue
        name, kind, _, f = m.groups()
        (pend_g if kind == "GFX" else pend_b).append(name)
        if f:
            f = f.replace(".2bpp", ".png")
            for n in (pend_g if kind == "GFX" else pend_b):
                (ts_gfx if kind == "GFX" else ts_blk)[n] = f
            if kind == "GFX":
                pend_g = []
            else:
                pend_b = []
    # 충돌 타일
    coll = {}
    pend = []
    for ln in lines("data", "tilesets", "collision_tile_ids.asm"):
        s = ln.strip()
        m = re.match(r"^(\w+)_Coll::", s)
        if m:
            pend.append(m.group(1))
            continue
        if s.startswith("coll_tiles"):
            vals = [parse_num(x) for x in args_of(s, "coll_tiles") if x]
            for n in pend:
                coll[n] = vals
            pend = []
    # 헤더 (카운터, 풀)
    ts_info = []
    for ln in lines("data", "tilesets", "tileset_headers.asm"):
        s = ln.strip()
        if s.startswith("tileset "):
            a = args_of(s, "tileset")
            ts_info.append({
                "name": a[0],
                "counters": [parse_num(x) for x in a[1:4] if parse_num(x) >= 0],
                "grass": parse_num(a[4]),
            })
    tilesets = {}
    tile_imgs = {}
    for i, t in enumerate(ts_info):
        name = t["name"]
        img = Image.open(src(ts_gfx[name])).convert("L")
        tile_imgs[name] = img
        bst = open(src(ts_blk[name]), "rb").read()
        tilesets[tileset_ids[i]] = {
            "name": name, "img": img, "blocks": bst,
            "coll": coll[name], "counters": t["counters"], "grass": t["grass"],
        }

    headers_dir = src("data", "maps", "headers")
    maps = {}
    map_imgs = os.path.join(ASSETS, "maps")
    os.makedirs(map_imgs, exist_ok=True)
    all_texts = parse_all_texts()
    sprite_files = parse_sprite_files()

    for fn in sorted(os.listdir(headers_dir)):
        name = fn[:-4]
        hdr = list(lines("data", "maps", "headers", fn))
        m_hdr = None
        conns = []
        for s in (l.strip() for l in hdr):
            if s.startswith("map_header"):
                m_hdr = args_of(s, "map_header")
            elif s.startswith("connection"):
                a = args_of(s, "connection")
                conns.append({"dir": a[0], "map": a[2], "offset": int(a[3])})
        if not m_hdr:
            continue
        const, tileset = m_hdr[1], m_hdr[2]
        w, h, idx = consts[const]
        blk_path = src("maps", name + ".blk")
        if not os.path.exists(blk_path) or w == 0:
            continue
        blk = open(blk_path, "rb").read()
        if len(blk) < w * h:
            blk = blk + bytes(w * h - len(blk))
        ts = tilesets[tileset]

        # 오브젝트
        obj_path = os.path.join("data", "maps", "objects", name + ".asm")
        warps, signs, npcs = [], [], []
        border = 0
        obj_consts = []
        for s in (l.strip() for l in lines(obj_path)):
            if s.startswith("db ") and "border" in read(obj_path) and border == 0 and not warps:
                try:
                    border = parse_num(s[3:].split(";")[0])
                except ValueError:
                    pass
            elif s.startswith("const_export"):
                obj_consts.append(s.split()[1])
            elif s.startswith("warp_event"):
                a = args_of(s, "warp_event")
                warps.append({"x": int(a[0]), "y": int(a[1]), "map": a[2], "warp": int(a[3])})
            elif s.startswith("bg_event"):
                a = args_of(s, "bg_event")
                signs.append({"x": int(a[0]), "y": int(a[1]), "text": a[2]})
            elif s.startswith("object_event"):
                a = args_of(s, "object_event")
                o = {
                    "x": int(a[0]), "y": int(a[1]), "sprite": a[2],
                    "move": a[3], "dir": a[4], "text": a[5],
                }
                if len(a) >= 8 and a[6].startswith("OPP_"):
                    o["trainer_class"] = a[6][4:]
                    o["trainer_index"] = int(a[7])
                elif len(a) >= 8 and a[6].isupper():
                    o["pokemon"] = a[6]
                    o["level"] = int(a[7])
                elif len(a) == 7:
                    o["item"] = a[6]
                o["id"] = obj_consts[len(npcs)] if len(npcs) < len(obj_consts) else "%s_%d" % (const, len(npcs))
                o["sprite_file"] = sprite_files.get(a[2], "")
                npcs.append(o)

        ptrs, _ = parse_script_texts(name, all_texts)

        # 렌더링 (그레이스케일, 흰색=255)
        img = Image.new("L", (w * 32, h * 32), 255)
        cells = []  # 16x16 셀별 좌하단 타일 id
        for by in range(h):
            for bx in range(w):
                b = blk[by * w + bx]
                tiles = ts["blocks"][b * 16:(b + 1) * 16]
                for ty in range(4):
                    for tx in range(4):
                        t = tiles[ty * 4 + tx]
                        sx, sy = (t % 16) * 8, (t // 16) * 8
                        tile = ts["img"].crop((sx, sy, sx + 8, sy + 8))
                        img.paste(tile, (bx * 32 + tx * 8, by * 32 + ty * 8))
        for cy in range(h * 2):
            row = []
            for cx in range(w * 2):
                b = blk[(cy // 2) * w + (cx // 2)]
                tiles = ts["blocks"][b * 16:(b + 1) * 16]
                sub_x, sub_y = cx % 2, cy % 2
                row.append(tiles[(sub_y * 2 + 1) * 4 + sub_x * 2])
            cells.append(row)
        img.save(os.path.join(map_imgs, name + ".png"))

        # 경계 블록 이미지
        btiles = ts["blocks"][border * 16:(border + 1) * 16]
        bimg = Image.new("L", (32, 32), 255)
        for ty in range(4):
            for tx in range(4):
                t = btiles[ty * 4 + tx]
                sx, sy = (t % 16) * 8, (t // 16) * 8
                bimg.paste(ts["img"].crop((sx, sy, sx + 8, sy + 8)), (tx * 8, ty * 8))
        bimg.save(os.path.join(map_imgs, name + "_border.png"))

        # 팔레트
        if tileset == "CEMETERY":
            pal = "PAL_GRAYMON"
        elif tileset == "CAVERN":
            pal = "PAL_CAVE"
        elif idx < num_city:
            pal = list(pals.keys())[idx + 1]  # 도시 팔레트 = 맵 id + 1
        elif idx < first_indoor:
            pal = "PAL_ROUTE"
        else:
            pal = None  # 실내: 직전 실외 맵 팔레트 상속

        maps[const] = {
            "name": name, "id": idx, "w": w, "h": h, "tileset": tileset,
            "outdoor": idx < first_indoor, "palette": pal,
            "connections": conns, "warps": warps, "signs": signs, "npcs": npcs,
            "cells": cells, "texts": ptrs, "blk": list(blk[:w * h]),
        }
    ts_dir = os.path.join(ASSETS, "tilesets")
    os.makedirs(ts_dir, exist_ok=True)
    for k, v in tilesets.items():
        v["img"].save(os.path.join(ts_dir, k + ".png"))
    tileset_out = {k: {"name": v["name"], "coll": v["coll"], "counters": v["counters"],
                       "grass": v["grass"],
                       "blocks": [list(v["blocks"][i:i + 16]) for i in range(0, len(v["blocks"]), 16)]}
                   for k, v in tilesets.items()}
    return maps, tileset_out, all_texts


def parse_sprite_files():
    """SPRITE_XXX -> 파일명."""
    consts = [n for n, _ in parse_const_list(os.path.join("constants", "sprite_constants.asm"))]
    labels = []
    for ln in lines("data", "sprites", "sprites.asm"):
        s = ln.strip()
        if s.startswith("overworld_sprite"):
            labels.append(args_of(s, "overworld_sprite")[0])
    lab_file = {}
    for ln in lines("gfx", "sprites.asm"):
        m = re.match(r'^(\w+)::\s*INCBIN\s+"gfx/sprites/([\w.]+)\.2bpp"', ln.strip())
        if m:
            lab_file[m.group(1)] = m.group(2)
    out = {}
    for i, lab in enumerate(labels):
        if i + 1 < len(consts):
            out[consts[i + 1]] = lab_file.get(lab, "")
    return out


# ---------------------------------------------------------------- pokemon
def parse_pokemon(pals):
    mon_consts = dict(parse_const_list(os.path.join("constants", "pokemon_constants.asm")))
    # 내부 id -> 이름
    names = []
    for ln in lines("data", "pokemon", "names.asm"):
        m = re.search(r'(?:li|db|dname)\s+"([^"]*)"', ln)
        if m:
            names.append(m.group(1).replace("@", ""))
    # 진화/기술 (내부 순서)
    evo_ptrs = []
    for ln in lines("data", "pokemon", "evos_moves.asm"):
        s = ln.strip()
        if s.startswith("dw ") and s.endswith("EvosMoves"):
            evo_ptrs.append(s[3:])
    evo_blocks = {}
    cur = None
    for ln in lines("data", "pokemon", "evos_moves.asm"):
        s = ln.strip()
        m = re.match(r"^(\w+EvosMoves):", s)
        if m:
            cur = m.group(1)
            evo_blocks[cur] = []
            continue
        if cur and s.startswith("db "):
            evo_blocks[cur].append([x.strip() for x in s[3:].split(",")])
    # 기본 스탯 (도감 순서 파일)
    stat_files = []
    for ln in lines("data", "pokemon", "base_stats.asm"):
        m = re.search(r'INCLUDE "(data/pokemon/base_stats/\w+\.asm)"', ln)
        if m:
            stat_files.append(m.group(1))
    stat_files.append("data/pokemon/base_stats/mew.asm")
    # palettes (도감 순서, 0=missingno)
    mon_pals = []
    for ln in lines("data", "pokemon", "palettes.asm"):
        s = ln.strip()
        if s.startswith("db PAL_"):
            mon_pals.append(s[3:].strip())
    # pics
    pic_front, pic_back = {}, {}
    for ln in lines("gfx", "pics.asm"):
        m = re.match(r'^(\w+)Pic(Front|Back)::\s*INCBIN\s+"gfx/pokemon/(front|back)/([\w.]+)\.pic"', ln.strip())
        if m:
            (pic_front if m.group(2) == "Front" else pic_back)[m.group(1)] = m.group(4)

    growth = ["MEDIUM_FAST", "SLIGHTLY_FAST", "SLIGHTLY_SLOW", "MEDIUM_SLOW", "FAST", "SLOW"]

    mons = {}
    os.makedirs(os.path.join(ASSETS, "pokemon", "front"), exist_ok=True)
    os.makedirs(os.path.join(ASSETS, "pokemon", "back"), exist_ok=True)
    for f in stat_files:
        L = [l.strip() for l in lines(*f.split("/")) if l.strip()]
        dex_const = L[0].split()[1]
        dex = len(mons) + 1
        stats = [int(x) for x in L[1][3:].split(",")]
        types = [x.strip() for x in L[2][3:].split(",")]
        catch = int(L[3][3:])
        base_exp = int(L[4][3:])
        pics = L[6][3:].split(",")
        front_lab = pics[0].strip().replace("PicFront", "")
        start_moves = [x.strip() for x in L[7][3:].split(",") if x.strip() != "NO_MOVE"]
        gr = L[8].split()[1].replace("GROWTH_", "")
        tmhm = []
        j = 9
        while j < len(L) and not L[j].startswith("db 0"):
            t = L[j].replace("tmhm", "").replace("\\", "")
            tmhm += [x.strip() for x in t.split(",") if x.strip()]
            j += 1
        const = dex_const.replace("DEX_", "")
        internal = mon_consts[const]
        evo_label = evo_ptrs[internal - 1]
        evos, learn = [], []
        part = 0
        for row in evo_blocks[evo_label]:
            if row == ["0"]:
                part += 1
                continue
            if part == 0:
                if row[0] == "EVOLVE_LEVEL":
                    evos.append({"method": "level", "level": int(row[1]), "to": row[2]})
                elif row[0] == "EVOLVE_ITEM":
                    evos.append({"method": "item", "item": row[1], "to": row[3]})
                elif row[0] == "EVOLVE_TRADE":
                    evos.append({"method": "trade", "to": row[2]})
            elif part == 1:
                learn.append([int(row[0]), row[1]])
        # 그림 (팔레트 적용)
        pal = pals[mon_pals[dex]]
        fname = pic_front.get(front_lab, const.lower())
        bname = pic_back.get(front_lab, fname + "b")
        colorize(src("gfx", "pokemon", "front", fname + ".png"),
                 os.path.join(ASSETS, "pokemon", "front", const.lower() + ".png"), pal, transparent=True)
        colorize(src("gfx", "pokemon", "back", bname + ".png"),
                 os.path.join(ASSETS, "pokemon", "back", const.lower() + ".png"), pal, transparent=True)
        mons[const] = {
            "dex": dex, "internal": internal, "name": KO_POKEMON[dex - 1], "name_en": names[internal - 1],
            "types": sorted(set(types), key=types.index),
            "hp": stats[0], "atk": stats[1], "def": stats[2], "spd": stats[3], "spc": stats[4],
            "catch": catch, "exp": base_exp, "moves": start_moves, "growth": gr,
            "tmhm": tmhm, "evos": evos, "learn": learn, "palette": pal,
        }
    # 도감 설명
    return mons


def colorize(path_in, path_out, pal, transparent=False):
    im = Image.open(path_in).convert("L")
    out = Image.new("RGBA", im.size)
    px = im.load()
    op = out.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            v = px[x, y]
            idx = 3 - round(v / 85)
            c = pal[idx]
            a = 0 if (transparent and idx == 0) else 255
            op[x, y] = (c[0], c[1], c[2], a)
    out.save(path_out)


def parse_moves():
    out = {}
    order = []
    for ln in lines("data", "moves", "moves.asm"):
        s = ln.strip()
        if s.startswith("move "):
            a = args_of(s, "move")
            order.append(a[0])
            out[a[0]] = {
                "id": len(order), "name": KO_MOVES[len(order) - 1], "effect": a[1],
                "power": int(a[2]), "type": a[3], "acc": int(a[4]), "pp": int(a[5]),
            }
    names_en = []
    for ln in lines("data", "moves", "names.asm"):
        m = re.search(r'li\s+"([^"]*)"', ln)
        if m:
            names_en.append(m.group(1))
    for i, k in enumerate(order):
        if i < len(names_en):
            out[k]["name_en"] = names_en[i]
    return out


def parse_types():
    chart = []
    for ln in lines("data", "types", "type_matchups.asm"):
        s = ln.strip()
        if s.startswith("db ") and "," in s:
            a = [x.strip() for x in s[3:].split(",")]
            if len(a) == 3:
                mult = {"SUPER_EFFECTIVE": 2.0, "NOT_VERY_EFFECTIVE": 0.5, "NO_EFFECT": 0.0}[a[2]]
                chart.append([a[0], a[1], mult])
    return {"chart": chart, "names": KO_TYPES}


def parse_items():
    consts = parse_const_list(os.path.join("constants", "item_constants.asm"))
    names = []
    for ln in lines("data", "items", "names.asm"):
        m = re.search(r'li\s+"([^"]*)"', ln)
        if m:
            names.append(m.group(1))
    prices = []
    for ln in lines("data", "items", "prices.asm"):
        s = ln.strip()
        if s.startswith("bcd3"):
            prices.append(int(s.split()[1]))
    items = {}
    for (name, val) in consts:
        if name == "NO_ITEM" or val == 0 or val > len(names):
            continue
        items[name] = {
            "id": val, "name": KO_ITEMS.get(name, names[val - 1]), "name_en": names[val - 1],
            "price": prices[val - 1] if val - 1 < len(prices) else 0,
        }
    # 기술머신/비전머신
    tm_prices = []
    for ln in lines("data", "items", "tm_prices.asm"):
        s2 = ln.strip()
        if s2.startswith("nybble ") and not s2.startswith("nybble_array"):
            tm_prices.append(int(s2.split()[1]) * 1000)
    hm_i, tm_i = 0, 0
    for ln in lines("constants", "item_constants.asm"):
        s2 = ln.strip()
        m = re.match(r"add_(hm|tm)\s+(\w+)", s2)
        if not m:
            continue
        mv = m.group(2)
        if m.group(1) == "hm":
            hm_i += 1
            items["HM_" + mv] = {"id": 0xC3 + hm_i, "name": "비전머신%02d" % hm_i, "name_en": "HM%02d" % hm_i,
                                  "price": 0, "move": mv, "hm": hm_i}
        else:
            tm_i += 1
            items["TM_" + mv] = {"id": 0xC8 + tm_i, "name": "기술머신%02d" % tm_i, "name_en": "TM%02d" % tm_i,
                                  "price": tm_prices[tm_i - 1] if tm_i - 1 < len(tm_prices) else 0,
                                  "move": mv, "tm": tm_i}
    marts = {}
    cur = None
    for ln in lines("data", "items", "marts.asm"):
        s = ln.strip()
        m = re.match(r"^(\w+)::", s)
        if m:
            cur = m.group(1)
        elif s.startswith("script_mart") and cur:
            marts[cur] = args_of(s, "script_mart")
    return items, marts


def parse_trainers():
    classes = [n for n, _ in parse_const_list(os.path.join("constants", "trainer_constants.asm"), "trainer_const")]
    names = []
    for ln in lines("data", "trainers", "names.asm"):
        m = re.search(r'li\s+"([^"]*)"', ln)
        if m:
            names.append(m.group(1))
    money, pics = [], []
    for ln in lines("data", "trainers", "pic_pointers_money.asm"):
        s = ln.strip()
        if s.startswith("pic_money"):
            a = args_of(s, "pic_money")
            pics.append(a[0])
            money.append(int(a[1]))
    pic_file = {}
    for ln in lines("gfx", "pics.asm"):
        m = re.match(r'^(\w+Pic)::\s*INCBIN\s+"gfx/trainers/([\w.]+)\.pic"', ln.strip())
        if m:
            pic_file[m.group(1)] = m.group(2)
    # 파티
    ptr_order = []
    blocks = {}
    cur = None
    for ln in lines("data", "trainers", "parties.asm"):
        s = ln.strip()
        if s.startswith("dw ") and s.endswith("Data"):
            ptr_order.append(s[3:])
            continue
        m = re.match(r"^(\w+Data):", s)
        if m:
            cur = m.group(1)
            blocks[cur] = []
            continue
        if cur and s.startswith("db "):
            a = [x.strip() for x in s[3:].split(",")]
            if a[-1] == "0":
                a = a[:-1]
            party = []
            if a[0] == "$FF":
                for k in range(1, len(a), 2):
                    party.append([int(a[k]), a[k + 1]])
            else:
                lv = int(a[0])
                party = [[lv, mn] for mn in a[1:]]
            blocks[cur].append(party)
    os.makedirs(os.path.join(ASSETS, "trainers"), exist_ok=True)
    gray = [[255, 255, 255], [170, 170, 170], [85, 85, 85], [0, 0, 0]]
    out = {}
    for i, cls in enumerate(classes[1:]):
        f = pic_file.get(pics[i], "")
        if f:
            colorize(src("gfx", "trainers", f + ".png"),
                     os.path.join(ASSETS, "trainers", cls.lower() + ".png"), gray, transparent=True)
        out[cls] = {
            "name": KO_TRAINERS.get(cls, names[i] if i < len(names) else cls),
            "name_en": names[i] if i < len(names) else cls,
            "money": money[i], "pic": cls.lower() if f else "",
            "parties": blocks.get(ptr_order[i], []) if i < len(ptr_order) else [],
        }
    return out


def parse_wild():
    labels = []
    for ln in lines("data", "wild", "grass_water.asm"):
        s = ln.strip()
        if s.startswith("dw "):
            labels.append(s[3:])
    map_order = []
    for ln in lines("constants", "map_constants.asm"):
        s = ln.strip()
        if s.startswith("map_const "):
            map_order.append(args_of(s, "map_const")[0])
    blocks = {}
    for fn in os.listdir(src("data", "wild", "maps")):
        cur = None
        sect = None
        for ln in lines("data", "wild", "maps", fn):
            s = ln.strip()
            m = re.match(r"^(\w+):", s)
            if m:
                cur = m.group(1)
                blocks[cur] = {"grass": {"rate": 0, "mons": []}, "water": {"rate": 0, "mons": []}}
            elif s.startswith("def_grass_wildmons"):
                sect = "grass"
                blocks[cur][sect]["rate"] = int(s.split()[1])
            elif s.startswith("def_water_wildmons"):
                sect = "water"
                blocks[cur][sect]["rate"] = int(s.split()[1])
            elif s.startswith("db ") and cur and sect:
                a = [x.strip() for x in s[3:].split(",")]
                if len(a) == 2:
                    blocks[cur][sect]["mons"].append([int(a[0]), a[1]])
    out = {}
    for i, lab in enumerate(labels):
        if i < len(map_order) and lab in blocks:
            out[map_order[i]] = blocks[lab]
    return out


def parse_growth():
    out = []
    for ln in lines("data", "growth_rates.asm"):
        s = ln.strip()
        if s.startswith("growth_rate"):
            out.append([int(x) for x in args_of(s, "growth_rate")])
    return dict(zip(["MEDIUM_FAST", "SLIGHTLY_FAST", "SLIGHTLY_SLOW", "MEDIUM_SLOW", "FAST", "SLOW"], out))


def copy_sprites():
    d = os.path.join(ASSETS, "sprites")
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(src("gfx", "sprites")):
        if f.endswith(".png"):
            im = Image.open(src("gfx", "sprites", f)).convert("L")
            out = Image.new("LA", im.size)
            px, op = im.load(), out.load()
            for y in range(im.size[1]):
                for x in range(im.size[0]):
                    v = px[x, y]
                    op[x, y] = (v, 0 if v == 255 else 255)
            out.save(os.path.join(d, f))


def copy_misc(pals):
    d = os.path.join(ASSETS, "misc")
    os.makedirs(d, exist_ok=True)
    gray = [[255, 255, 255], [170, 170, 170], [85, 85, 85], [0, 0, 0]]
    colorize(src("gfx", "player", "red.png"), os.path.join(d, "red_front.png"), gray, transparent=True)
    colorize(src("gfx", "player", "redb.png"), os.path.join(d, "red_back.png"), gray, transparent=True)
    for f in ["balls.png", "battle_hud_1.png", "battle_hud_2.png", "battle_hud_3.png"]:
        colorize(src("gfx", "battle", f), os.path.join(d, f), gray, transparent=True)
    for f in ["pokemon_logo.png", "red_version.png"]:
        p = src("gfx", "title", f)
        if os.path.exists(p):
            shutil.copy(p, os.path.join(d, f))
    g = src("gfx", "battle", "ghost.png")
    if os.path.exists(g):
        colorize(g, os.path.join(d, "ghost.png"), gray, transparent=True)
    emote = src("gfx", "emotes", "shock.png")
    if os.path.exists(emote):
        colorize(emote, os.path.join(d, "shock.png"), gray, transparent=True)


def parse_toggles():
    out = {}
    for ln in lines("data", "maps", "toggleable_objects.asm"):
        s = ln.strip()
        if s.startswith("toggle_object_state"):
            a = args_of(s, "toggle_object_state")
            out[a[0]] = a[1] == "ON"
    return out


def parse_doors():
    ts_ids = [n for n, _ in parse_const_list(os.path.join("constants", "tileset_constants.asm"))]
    ptr = {}
    cur = []
    labels = {}
    for ln in lines("data", "tilesets", "door_tile_ids.asm"):
        s = ln.strip()
        if s.startswith("dbw "):
            a = args_of(s, "dbw")
            ptr.setdefault(a[1], []).append(a[0])
        m = re.match(r"^(\.\w+):", s)
        if m:
            cur.append(m.group(1))
        elif s.startswith("door_tiles"):
            vals = [parse_num(x) for x in args_of(s, "door_tiles") if x]
            for c in cur:
                labels[c] = vals
            cur = []
    out = {}
    for lab, tss in ptr.items():
        for t in tss:
            out[t] = labels.get(lab, [])
    return out


def parse_hidden():
    out = {}
    cur = None
    for ln in lines("data", "events", "hidden_events.asm"):
        s = ln.strip()
        if s.startswith("hidden_events_for"):
            cur = s.split()[1]
            out.setdefault(cur, [])
        elif cur and (s.startswith("hidden_event ") or s.startswith("hidden_text_predef")):
            macro = s.split()[0]
            a = args_of(s, macro)
            out[cur].append({"x": int(a[0]), "y": int(a[1]), "handler": a[2], "arg": a[3] if len(a) > 3 else ""})
    return out


def parse_songs():
    order = []
    for ln in lines("constants", "map_constants.asm"):
        t = ln.strip()
        if t.startswith("map_const "):
            order.append(args_of(t, "map_const")[0])
    songs = []
    for ln in lines("data", "maps", "songs.asm"):
        t = ln.strip()
        if t.startswith("db MUSIC_"):
            songs.append(t[3:].split(",")[0].strip())
    names = [f[:-4] for f in os.listdir(os.path.join(ASSETS, "audio", "music"))] if os.path.isdir(os.path.join(ASSETS, "audio", "music")) else []
    lut = {n.lower(): n for n in names}
    out = {}
    for i, mc in enumerate(songs):
        if i < len(order):
            key = mc.replace("MUSIC_", "").replace("_", "").lower()
            out[order[i]] = lut.get(key, "")
    return out


def _db_list(path, label=None):
    """단순 'db A, B, ...' 목록 (label 이후 -1 까지)."""
    rows = []
    active = label is None
    for ln in lines(*path.split("/")):
        t = ln.strip()
        if label and t.startswith(label):
            active = True
            continue
        if not active:
            continue
        if t.startswith("db "):
            a = [x.strip() for x in t[3:].split(",")]
            if a[0] == "-1":
                if label:
                    break
                continue
            rows.append(a)
    return rows


def parse_extra():
    ex = {}
    ex["water_tilesets"] = [r[0] for r in _db_list("data/tilesets/water_tilesets.asm")]
    ex["bike_tilesets"] = [r[0] for r in _db_list("data/tilesets/bike_riding_tilesets.asm")]
    ex["escape_rope_tilesets"] = [r[0] for r in _db_list("data/tilesets/escape_rope_tilesets.asm")]
    ex["cut_trees"] = [[parse_num(r[0]), parse_num(r[1])] for r in _db_list("data/tilesets/cut_tree_blocks.asm")]
    ex["pair_land"] = [[r[0], parse_num(r[1]), parse_num(r[2])] for r in _db_list("data/tilesets/pair_collision_tile_ids.asm", "TilePairCollisionsLand")]
    ex["pair_water"] = [[r[0], parse_num(r[1]), parse_num(r[2])] for r in _db_list("data/tilesets/pair_collision_tile_ids.asm", "TilePairCollisionsWater")]
    fb = []
    for ln in lines("data", "maps", "force_bike_surf.asm"):
        t = ln.strip()
        if t.startswith("force_bike_surf "):
            a = args_of(t, "force_bike_surf")
            fb.append([a[0], int(a[1]), int(a[2])])
    ex["force_bike_surf"] = fb
    # 날기 위치
    fly = {}
    order = []
    for ln in lines("data", "maps", "special_warps.asm"):
        t = ln.strip()
        m = re.match(r"^\.(\w+):\s*fly_warp (\w+),\s*(\d+),\s*(\d+)", t)
        if m:
            fly[m.group(2)] = [int(m.group(3)), int(m.group(4))]
    ex["fly"] = fly
    # 낚시
    ex["good_rod"] = [[int(r[0]), r[1]] for r in _db_list("data/wild/good_rod.asm") if len(r) == 2]
    sr_maps = {}
    groups = {}
    cur = None
    for ln in lines("data", "wild", "super_rod.asm"):
        t = ln.strip()
        if t.startswith("dbw "):
            a = args_of(t, "dbw")
            sr_maps[a[0]] = a[1]
        m = re.match(r"^(\.\w+):", t)
        if m:
            cur = m.group(1)
            groups[cur] = []
        elif cur and t.startswith("db ") and "," in t:
            a = [x.strip() for x in t[3:].split(",")]
            groups[cur].append([int(a[0]), a[1]])
    ex["super_rod"] = {k: groups.get(v, []) for k, v in sr_maps.items()}
    # NPC 교환
    trades = []
    for ln in lines("data", "events", "trades.asm"):
        t = ln.strip()
        if t.startswith("npctrade "):
            a = args_of(t, "npctrade")
            trades.append({"give": a[0], "get": a[1], "dialog": a[2], "nick": a[3].strip('"')})
    ex["trades"] = trades
    # 회전 타일 (비주시티 체육관, 로켓단 아지트)
    spin = {}
    for fn in ["ViridianGym", "RocketHideoutB2F", "RocketHideoutB3F"]:
        raw = [strip_comment(l).strip() for l in read("scripts", fn + ".asm").splitlines()]
        labels = {}
        cur = None
        for t in raw:
            m = re.match(r"^(\w+):", t)
            if m:
                cur = m.group(1)
                labels[cur] = []
            elif cur and t.startswith("db PAD_"):
                a = [x.strip() for x in t[3:].split(",")]
                labels[cur].append([a[0].replace("PAD_", ""), int(a[1])])
        coords = {}
        for t in raw:
            if t.startswith("map_coord_movement"):
                a = args_of(t, "map_coord_movement")
                coords["%d,%d" % (int(a[0]), int(a[1]))] = labels.get(a[2], [])
        spin[fn] = coords
    ex["spinners"] = spin
    # TOGGLE_ 상수 -> 오브젝트 id
    tconsts = [n for n, _ in parse_const_list(os.path.join("constants", "toggle_constants.asm"))]
    tobjs = []
    for ln in lines("data", "maps", "toggleable_objects.asm"):
        t = ln.strip()
        if t.startswith("toggle_object_state "):
            tobjs.append(args_of(t, "toggle_object_state")[0])
    ex["toggle_names"] = dict(zip(tconsts, tobjs))
    return ex


def main():
    pals = parse_super_palettes()
    maps, tilesets, texts = parse_maps(pals)
    hidden = parse_hidden()
    for k, v in maps.items():
        v["hidden"] = hidden.get(k, [])
    songs = parse_songs()
    for k, v in maps.items():
        v["music"] = songs.get(k, "")
    save_json("maps.json", maps)
    save_json("extra.json", parse_extra())
    doors = parse_doors()
    for k, v in tilesets.items():
        v["doors"] = doors.get(k, [])
    save_json("tilesets.json", tilesets)
    save_json("toggles.json", parse_toggles())
    save_json("texts_en.json", texts)
    save_json("palettes.json", pals)
    save_json("pokemon.json", parse_pokemon(pals))
    save_json("moves.json", parse_moves())
    save_json("types.json", parse_types())
    items, marts = parse_items()
    save_json("items.json", items)
    save_json("marts.json", marts)
    save_json("trainers.json", parse_trainers())
    save_json("wild.json", parse_wild())
    save_json("growth.json", parse_growth())
    copy_sprites()
    copy_misc(pals)
    print("maps:", len(maps), "texts:", len(texts))


if __name__ == "__main__":
    main()
