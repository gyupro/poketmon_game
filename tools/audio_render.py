"""pokered 사운드 엔진을 파이썬으로 흉내 내서 음악/효과음/울음소리를 WAV로 렌더링한다.

원작 audio/engine_1.asm 의 동작(음표 길이 계산, 비브라토, 피치 슬라이드, 듀티 회전,
드럼=노이즈 효과음)과 게임보이 음원 칩(사각파 2, 파형 1, 노이즈 1)을 재현한다.

사용법: python tools/audio_render.py
출력: game/assets/audio/{music,sfx,cries}/*.wav, game/data/audio.json (루프 지점)
"""
import json
import os
import re
import struct
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "pokered_src")
OUT = os.path.join(ROOT, "game", "assets", "audio")
DATA = os.path.join(ROOT, "game", "data")

SR = 22050            # 출력 샘플레이트
OS = 4                # 오버샘플링 배수 (앨리어싱 감소)
ISR = SR * OS
FRAME_HZ = 4194304 / 70224   # 59.7275
SPF = ISR / FRAME_HZ         # 내부 샘플/프레임

NOTES = {"C_": 0, "C#": 1, "D_": 2, "D#": 3, "E_": 4, "F_": 5, "F#": 6,
         "G_": 7, "G#": 8, "A_": 9, "A#": 10, "B_": 11}
PITCHES = [0xF82C, 0xF89D, 0xF907, 0xF96B, 0xF9CA, 0xFA23, 0xFA77, 0xFAC7,
           0xFB12, 0xFB58, 0xFB9B, 0xFBDA]
DUTY = [0.125, 0.25, 0.5, 0.75]


# ---------------------------------------------------------------- 파싱
def num(s):
    s = s.strip()
    neg = s.startswith("-")
    if neg:
        s = s[1:]
    if s.startswith("$"):
        v = int(s[1:], 16)
    elif s.startswith("%"):
        v = int(s[1:], 2)
    else:
        v = int(s)
    return -v if neg else v


class Program:
    """모든 음악/효과음 asm 을 하나의 명령 리스트로. labels: 이름 -> 인덱스."""

    def __init__(self):
        self.cmds = []
        self.labels = {}

    def load(self, path):
        glob = ""
        skip = []  # IF DEF(_RED) 처리 스택: True 면 건너뜀
        pending_targets = []
        for raw in open(path, encoding="utf-8").read().splitlines():
            ln = raw.split(";")[0].strip()
            if not ln:
                continue
            if ln.startswith("IF "):
                skip.append("_RED" not in ln)
                continue
            if ln.startswith("ELSE"):
                skip[-1] = not skip[-1]
                continue
            if ln.startswith("ENDC"):
                skip.pop()
                continue
            if any(skip):
                continue
            m = re.match(r"^(\.?\w+):+$", ln)
            if m:
                name = m.group(1)
                if name.startswith("."):
                    name = glob + name
                else:
                    glob = name
                self.labels[name] = len(self.cmds)
                continue
            parts = ln.split(None, 1)
            op = parts[0]
            args = [a.strip() for a in parts[1].split(",")] if len(parts) > 1 else []
            if op in ("sound_call",):
                args = [glob + args[0] if args[0].startswith(".") else args[0]]
            elif op == "sound_loop":
                args = [args[0], glob + args[1] if args[1].startswith(".") else args[1]]
            self.cmds.append((op, args))
        return pending_targets


def load_program():
    p = Program()
    for d in ("music", "sfx"):
        for f in sorted(os.listdir(os.path.join(SRC, "audio", d))):
            if f.endswith(".asm"):
                p.load(os.path.join(SRC, "audio", d, f))
    return p


def parse_headers(fn):
    """헤더 파일 -> {이름: [(채널번호, 라벨), ...]}"""
    out = {}
    cur = None
    for raw in open(os.path.join(SRC, "audio", "headers", fn), encoding="utf-8"):
        ln = raw.split(";")[0].strip()
        m = re.match(r"^(\w+)::$", ln)
        if m:
            cur = m.group(1)
            out[cur] = []
        elif ln.startswith("channel ") and cur:
            a = [x.strip() for x in ln[len("channel"):].split(",")]
            out[cur].append((int(a[0]), a[1]))
    return out


def wave_tables():
    waves = []
    for raw in open(os.path.join(SRC, "audio", "wave_samples.asm"), encoding="utf-8"):
        ln = raw.strip()
        if ln.startswith("dn "):
            waves.append([int(x) for x in ln[3:].split(",")])
    # wave5 는 원작에서 효과음 데이터를 읽어오는 버그 — 주석에 적힌 실제 값 사용
    w5_audio1 = [2, 1, 14, 2, 3, 3, 2, 8, 14, 1, 2, 2, 15, 15, 14, 10, 1, 0, 1, 4, 13, 12, 1, 0, 14, 3, 4, 1, 5, 1, 7, 3]
    w5_audio3 = [2, 1, 14, 2, 3, 3, 2, 8, 14, 1, 2, 2, 15, 15, 2, 2, 15, 7, 2, 4, 2, 2, 15, 7, 3, 4, 2, 4, 15, 7, 4, 4]
    return waves[:5], w5_audio1, w5_audio3


def lfsr_bits(width7):
    lfsr = 0x7FFF
    n = 127 if width7 else 32767
    out = np.zeros(n, dtype=np.float32)
    for i in range(n):
        out[i] = 0.0 if (lfsr & 1) else 1.0
        x = (lfsr & 1) ^ ((lfsr >> 1) & 1)
        lfsr = (lfsr >> 1) | (x << 14)
        if width7:
            lfsr = (lfsr & ~0x40) | (x << 6)
    return out


LFSR15 = lfsr_bits(False)
LFSR7 = lfsr_bits(True)


# ---------------------------------------------------------------- 하드웨어 채널
class HW:
    def __init__(self, kind):
        self.kind = kind  # "sq", "wave", "noise"
        self.on = False
        self.freq = 0
        self.duty = 2
        self.vol = 0
        self.env_dir = 0
        self.env_per = 0
        self.env_t = 0.0
        self.phase = 0.0
        self.wave = [0] * 32
        self.level = 0  # 파형 채널 출력 레벨 0=무음 1=100% 2=50% 3=25%
        self.poly = 0
        self.lpos = 0.0
        # 스윕 (효과음 ch5)
        self.sweep = 0
        self.sweep_t = 0.0

    def set_env(self, b):
        self.env_byte = b

    def trigger(self, env_byte=None):
        self.on = True
        if self.kind != "wave":
            b = env_byte
            self.vol = b >> 4
            self.env_dir = 1 if (b & 8) else -1
            self.env_per = b & 7
            self.env_t = 0.0
            if (b & 0xF8) == 0:  # DAC off
                self.on = False
        if self.kind == "noise":
            self.lpos = 0.0
        self.sweep_t = 0.0

    def render(self, n):
        """n 개 내부 샘플 생성 (0..15 범위)."""
        if not self.on:
            return None
        dt = n / ISR
        if self.kind == "sq":
            hz = 131072.0 / (2048 - self.freq)
            inc = hz / ISR
            ph = (self.phase + inc * np.arange(1, n + 1)) % 1.0
            self.phase = ph[-1]
            out = (ph < DUTY[self.duty]).astype(np.float32) * self.vol
        elif self.kind == "wave":
            if self.level == 0:
                return None
            hz = 65536.0 / (2048 - self.freq)
            inc = hz / ISR
            ph = (self.phase + inc * np.arange(1, n + 1)) % 1.0
            self.phase = ph[-1]
            w = np.array(self.wave, dtype=np.float32)
            out = np.floor(w[(ph * 32).astype(np.int32) % 32] / (1 << (self.level - 1)))
        else:
            s = self.poly >> 4
            r = self.poly & 7
            width7 = bool(self.poly & 8)
            if s >= 14:
                return None
            rate = 524288.0 / (r if r else 0.5) / (2 ** (s + 1))
            bits = LFSR7 if width7 else LFSR15
            pos = self.lpos + rate / ISR * np.arange(1, n + 1)
            self.lpos = pos[-1] % len(bits)
            out = bits[(pos.astype(np.int64)) % len(bits)] * self.vol
        # 볼륨 엔벨로프 (64Hz)
        if self.kind != "wave" and self.env_per:
            self.env_t += dt
            step = self.env_per / 64.0
            while self.env_t >= step:
                self.env_t -= step
                self.vol = max(0, min(15, self.vol + self.env_dir))
        # 주파수 스윕 (128Hz)
        if self.sweep and (self.sweep >> 4) & 7:
            per = ((self.sweep >> 4) & 7) / 128.0
            self.sweep_t += dt
            while self.sweep_t >= per:
                self.sweep_t -= per
                sh = self.sweep & 7
                d = self.freq >> sh
                if self.sweep & 8:
                    self.freq -= d
                else:
                    self.freq += d
                if self.freq > 2047:
                    self.on = False
                    break
                self.freq = max(0, self.freq)
        return out


# ---------------------------------------------------------------- 엔진 채널
class Chan:
    def __init__(self, idx, ptr):
        self.idx = idx          # 0..7 (CHAN1..CHAN8)
        self.ptr = ptr
        self.ret = None
        self.active = True
        self.loop_count = 1
        self.delay = 1
        self.frac = 0
        self.speed = 1
        self.volume = 0
        self.duty = 0
        self.duty_pattern = 0
        self.rotate = False
        self.octave = 4
        self.vib_delay = 0
        self.vib_reload = 0
        self.vib_ext = 0
        self.vib_rate = 0
        self.vib_up = False
        self.freq = 0
        self.perfect = False
        self.slide_on = False
        self.slide_len = 0
        self.slide_target = 0
        self.slide_cur = 0
        self.slide_step = 0
        self.slide_frac_step = 0
        self.slide_frac = 0
        self.slide_dec = False
        self.exec_music = False
        self.wave_inst = 0
        self.first_seen = {}   # 명령 인덱스 -> 최초 실행 프레임 (루프 검출)
        self.loop_start = None
        self.loop_end = None

    @property
    def is_sfx(self):
        return self.idx >= 4

    @property
    def hw_kind(self):
        return {0: "sq", 1: "sq", 2: "wave", 3: "noise"}[self.idx % 4]


def calc_freq(note, octave_reg):
    v = PITCHES[note]
    v = v - 0x10000  # signed
    v >>= (7 - octave_reg)
    return (v + 0x800) & 0x7FF


class Engine:
    def __init__(self, prog, waves, wave5, noise_hdr):
        self.p = prog
        self.waves = waves + [wave5] * 4
        self.noise_hdr = noise_hdr   # 드럼 번호 -> 라벨
        self.hw = [HW("sq"), HW("sq"), HW("wave"), HW("noise")]
        self.chans = [None] * 8
        self.tempo = 0x100
        self.sfx_tempo = 0x100
        self.frame = 0
        self.cry = None   # (pitch, tempo_mod)

    def start(self, chan_no, label):
        c = Chan(chan_no - 1, self.p.labels[label])
        self.chans[chan_no - 1] = c
        return c

    def next(self, c):
        op = self.p.cmds[c.ptr]
        c.ptr += 1
        return op

    def owner_hw(self, c):
        return self.hw[c.idx % 4]

    def sfx_overrides(self, c):
        """음악 채널인데 같은 하드웨어를 효과음이 쓰는 중이면 True."""
        if c.is_sfx:
            return False
        s = self.chans[c.idx + 4]
        return s is not None and s.active

    # -------------------------------------------------------- 프레임 업데이트
    def update(self):
        for c in self.chans:
            if c is None or not c.active:
                continue
            if c.delay == 1:
                self.play_next(c)
            else:
                c.delay -= 1
                if self.sfx_overrides(c):
                    continue
                self.effects(c)
        self.frame += 1

    def effects(self, c):
        hw = self.owner_hw(c)
        if c.rotate:
            c.duty_pattern = ((c.duty_pattern << 2) | (c.duty_pattern >> 6)) & 0xFF
            hw.duty = c.duty_pattern >> 6
        if not c.exec_music and c.is_sfx:
            return
        if c.slide_on:
            self.apply_slide(c, hw)
            return
        if c.vib_delay:
            c.vib_delay -= 1
            return
        if not c.vib_ext:
            return
        if c.vib_rate & 0xF:
            c.vib_rate -= 1
            return
        c.vib_rate = (c.vib_rate & 0xF0) | (c.vib_rate >> 4)
        lo = c.freq & 0xFF
        if c.vib_up:
            c.vib_up = False
            lo = max(0, lo - (c.vib_ext & 0xF))
        else:
            c.vib_up = True
            lo = min(0xFF, lo + (c.vib_ext >> 4))
        hw.freq = (hw.freq & 0x700) | lo

    def apply_slide(self, c, hw):
        if not c.slide_dec:
            cur = c.slide_cur + c.slide_step
            c.slide_frac += c.slide_frac_step
            if c.slide_frac > 0xFF:
                c.slide_frac &= 0xFF
                cur += 1
            if cur > c.slide_target:
                c.slide_on = False
                return
        else:
            cur = c.slide_cur - c.slide_step
            c.slide_frac = (c.slide_frac * 2)
            if c.slide_frac > 0xFF:
                c.slide_frac &= 0xFF
                cur -= 1
            if cur < c.slide_target:
                c.slide_on = False
                return
        c.slide_cur = cur & 0xFFFF
        hw.freq = cur & 0x7FF

    def play_next(self, c):
        c.vib_delay = c.vib_reload
        c.slide_on = False
        c.slide_dec = False
        while True:
            if c.ptr >= len(self.p.cmds):
                self.end_channel(c)
                return
            here = c.ptr
            if here not in c.first_seen:
                c.first_seen[here] = self.frame
            op, a = self.next(c)
            if op == "sound_ret":
                if c.ret is not None:
                    c.ptr, c.ret = c.ret, None
                    continue
                self.end_channel(c)
                return
            if op == "sound_call":
                c.ret = c.ptr
                c.ptr = self.p.labels[a[0]]
                continue
            if op == "sound_loop":
                cnt = num(a[0])
                tgt = self.p.labels[a[1]]
                if cnt == 0:
                    if c.loop_start is None:
                        c.loop_start = c.first_seen.get(tgt, 0)
                        c.loop_end = self.frame
                    c.ptr = tgt
                    continue
                if c.loop_count == cnt:
                    c.loop_count = 1
                    continue
                c.loop_count += 1
                c.ptr = tgt
                continue
            if op == "note_type" or op == "drum_speed":
                c.speed = num(a[0])
                if op == "note_type" and c.idx != 3:
                    vol, fade = num(a[1]), num(a[2])
                    if c.idx % 4 == 2:
                        c.wave_inst = fade & 0xF
                        c.volume = ((vol << 4) & 0x30) << 1
                    else:
                        c.volume = (vol << 4) | (fade & 0xF if fade >= 0 else 8 | (-fade))
                continue
            if op == "toggle_perfect_pitch":
                c.perfect = not c.perfect
                continue
            if op == "vibrato":
                d, depth, rate = num(a[0]), num(a[1]), num(a[2])
                c.vib_delay = c.vib_reload = d
                c.vib_ext = (((depth >> 1) + (depth & 1)) << 4) | (depth >> 1)
                c.vib_rate = (rate << 4) | rate
                continue
            if op == "pitch_slide":
                c.slide_len = num(a[0]) - 1
                c.slide_target = calc_freq(NOTES[a[2]], 8 - num(a[1]))
                c.slide_on = True
                # 다음 바이트(음표)를 음표로 처리
                op, a = self.next(c)
                self.do_note(c, op, a)
                return
            if op == "duty_cycle":
                c.duty = num(a[0])
                self.owner_hw(c).duty = c.duty if not self.sfx_overrides(c) else self.owner_hw(c).duty
                continue
            if op == "duty_cycle_pattern":
                v = [num(x) for x in a]
                c.duty_pattern = (v[0] << 6) | (v[1] << 4) | (v[2] << 2) | v[3]
                c.duty = v[0]
                c.rotate = True
                continue
            if op == "tempo":
                if c.is_sfx:
                    self.sfx_tempo = num(a[0])
                else:
                    self.tempo = num(a[0])
                    for x in self.chans[:4]:
                        if x:
                            x.frac = 0
                continue
            if op in ("volume", "stereo_panning", "unknownmusic0xef"):
                continue
            if op == "execute_music":
                c.exec_music = True
                continue
            if op == "octave":
                c.octave = 8 - num(a[0])
                continue
            if op in ("square_note", "noise_note") and c.is_sfx and not c.exec_music:
                self.sfx_note(c, op, a)
                return
            if op == "pitch_sweep" and c.is_sfx:
                ln, ch = num(a[0]), num(a[1])
                self.hw[0].sweep = (ln << 4) | (8 | -ch if ch < 0 else ch)
                continue
            self.do_note(c, op, a)
            return

    def end_channel(self, c):
        c.active = False
        if c.idx < 3:
            self.hw[c.idx].on = False

    def note_delay(self, c, length):
        if c.is_sfx:
            if c.idx == 7:
                tempo = 0x100
            elif self.cry is not None:
                tempo = 0x80 + self.cry[1]
            else:
                tempo = 0x100
        else:
            tempo = self.tempo
        ls = (length * c.speed) & 0xFF
        v = c.frac + ls * tempo
        c.frac = v & 0xFF
        c.delay = (v >> 8) & 0xFF
        if c.delay == 0:
            c.delay = 256

    def sfx_note(self, c, op, a):
        length = num(a[0]) + 1
        self.note_delay(c, length)
        vol, fade = num(a[1]), num(a[2])
        env = (vol << 4) | (fade if fade >= 0 else 8 | (-fade))
        hw = self.owner_hw(c)
        if op == "noise_note" or c.idx % 4 == 3:
            poly = num(a[3])
            if self.cry is not None:
                poly = (poly + self.cry[0]) & 0xFF
            hw.poly = poly
            hw.trigger(env)
            return
        f = num(a[3])
        if self.cry is not None:
            f = (f + self.cry[0]) & 0x7FF
        hw.duty = c.duty if not c.rotate else c.duty_pattern >> 6
        hw.freq = f & 0x7FF
        if hw.kind == "wave":
            hw.wave = self.waves[c.wave_inst]
            hw.level = (env >> 5) & 3
            hw.on = True
        else:
            hw.trigger(env)

    def do_note(self, c, op, a):
        if op == "drum_note":
            inst, length = num(a[0]), num(a[1])
            if inst in self.noise_hdr:
                s = Chan(7, self.p.labels[self.noise_hdr[inst]])
                self.chans[7] = s
                self.play_next(s)
            self.note_delay(c, length)
            return
        if op == "rest":
            self.note_delay(c, num(a[0]))
            if self.sfx_overrides(c):
                return
            hw = self.owner_hw(c)
            if hw.kind == "wave":
                hw.on = False
            elif c.idx % 4 != 3:
                hw.trigger(0x08)
            return
        if op != "note":
            raise ValueError("unknown op %s %s" % (op, a))
        note, length = NOTES[a[0]], num(a[1])
        self.note_delay(c, length)
        f = calc_freq(note, c.octave)
        if c.slide_on:
            self.init_slide(c, f)
        if self.sfx_overrides(c):
            return
        hw = self.owner_hw(c)
        if c.perfect:
            f += 1
        c.freq = f
        if self.cry is not None and c.is_sfx:
            f = (f + self.cry[0]) & 0x7FF
        hw.freq = f & 0x7FF
        if hw.kind == "wave":
            hw.wave = self.waves[c.wave_inst]
            hw.level = (c.volume >> 5) & 3
            hw.on = True
            hw.phase = 0.0
        else:
            hw.duty = c.duty_pattern >> 6 if c.rotate else c.duty
            hw.trigger(c.volume)

    def init_slide(self, c, f):
        c.slide_cur = f
        n = c.delay - c.slide_len
        if n <= 0:
            n = 1
        diff = f - c.slide_target
        if diff >= 0:
            c.slide_dec = True
        else:
            c.slide_dec = False
            diff = -diff
        c.slide_step = diff // n
        c.slide_frac_step = int((diff % n) * 256 / n)
        c.slide_frac = c.slide_frac_step


# ---------------------------------------------------------------- 렌더링
def run(engine, max_frames, stop_when_done=True, tail_frames=20):
    chunks = []
    acc = 0.0
    done_at = None
    f = 0
    while f < max_frames:
        engine.update()
        acc += SPF
        n = int(acc)
        acc -= n
        mix = np.zeros(n, dtype=np.float32)
        for hw in engine.hw:
            s = hw.render(n)
            if s is not None:
                mix += s
        chunks.append(mix)
        f += 1
        if stop_when_done and done_at is None and all(c is None or not c.active for c in engine.chans):
            done_at = f
        if done_at is not None and f >= done_at + tail_frames:
            break
    x = np.concatenate(chunks) if chunks else np.zeros(1, dtype=np.float32)
    return x


def finish(x):
    """오버샘플 -> 출력 레이트, DC 제거, 16bit 변환."""
    n = len(x) // OS * OS
    x = x[:n].reshape(-1, OS).mean(axis=1)
    # DC 제거: 이동 평균(약 46ms)을 빼는 고역 통과 (게임보이 출력 커패시터 흉내)
    w = 1024
    xs = x.astype(np.float64)
    pad = np.concatenate([np.full(w, xs[0] if len(xs) else 0.0), xs])
    cs = np.cumsum(pad)
    avg = (cs[w:] - cs[:-w]) / w
    out = (xs - avg) / 60.0 * 1.6
    return np.clip(out * 32767, -32768, 32767).astype(np.int16)


def write_wav(path, pcm, loop=None):
    data = pcm.tobytes()
    chunks = [b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, SR, SR * 2, 2, 16),
              b"data" + struct.pack("<I", len(data)) + data]
    body = b"WAVE" + b"".join(chunks)
    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", len(body)) + body)


def frame_to_sample(fr):
    return int(round(fr * SR / FRAME_HZ))


def render_music(prog, waves, w5, name, chans, noise_hdr, max_sec=240):
    e = Engine(prog, waves, w5, noise_hdr)
    started = []
    for ch, lab in chans:
        started.append(e.start(ch, lab))
    # 루프 검출: 모든 채널이 한 번씩 무한 루프 점프를 할 때까지 + 여유
    frames_needed = None
    chunks = []
    acc = 0.0
    f = 0
    done_at = None
    while f < max_sec * 60:
        e.update()
        acc += SPF
        n = int(acc)
        acc -= n
        mix = np.zeros(n, dtype=np.float32)
        for hw in e.hw:
            s = hw.render(n)
            if s is not None:
                mix += s
        chunks.append(mix)
        f += 1
        loops = [c for c in started]
        if all(c.loop_start is not None or not c.active for c in loops):
            if any(c.loop_start is not None for c in loops):
                break
        if all(not c.active for c in loops):
            if done_at is None:
                done_at = f
            if f >= done_at + 30:
                break
    x = np.concatenate(chunks)
    loop = None
    ls = [c for c in started if c.loop_start is not None]
    if ls:
        # 루프 길이 = 가장 긴 채널 기준. 시작 = 가장 늦게 루프 들어간 채널
        lens = [c.loop_end - c.loop_start for c in ls]
        period = max(lens)
        start = max(c.loop_start for c in ls)
        end = start + period
        # 필요한 만큼 더 렌더링
        while f < end + 2:
            e.update()
            acc += SPF
            n = int(acc)
            acc -= n
            mix = np.zeros(n, dtype=np.float32)
            for hw in e.hw:
                s = hw.render(n)
                if s is not None:
                    mix += s
            x = np.concatenate([x, mix])
            f += 1
        loop = (frame_to_sample(start), frame_to_sample(end))
    pcm = finish(x)
    if loop:
        pcm = pcm[:loop[1]]
    return pcm, loop


def main():
    prog = load_program()
    waves, w5a1, w5a3 = wave_tables()
    os.makedirs(os.path.join(OUT, "music"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "sfx"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "cries"), exist_ok=True)
    meta = {"music": {}, "sfx": {}, "cries": {}}
    only = sys.argv[1:]

    sfx_hdrs = {}
    noise_by_bank = {}
    for b in (1, 2, 3):
        h = parse_headers("sfxheaders%d.asm" % b)
        sfx_hdrs[b] = h
        nh = {}
        for k, v in h.items():
            m = re.match(r"SFX_Noise_Instrument(\d+)_%d$" % b, k)
            if m:
                nh[int(m.group(1))] = v[0][1]
        noise_by_bank[b] = nh

    # 음악
    for b in (1, 2, 3):
        for name, chans in parse_headers("musicheaders%d.asm" % b).items():
            short = name.replace("Music_", "")
            if only and short not in only:
                continue
            w5 = w5a3 if b == 3 else w5a1
            pcm, loop = render_music(prog, waves, w5, short, chans, noise_by_bank[b])
            write_wav(os.path.join(OUT, "music", short + ".wav"), pcm)
            meta["music"][short] = {"loop": list(loop) if loop else None, "len": len(pcm)}
            print("music", short, "%.1fs" % (len(pcm) / SR), "loop" if loop else "once")

    # 효과음 (울음소리 원본/노이즈 악기 제외)
    seen = set()
    for b in (1, 2, 3):
        for name, chans in sfx_hdrs[b].items():
            if "Noise_Instrument" in name or re.match(r"SFX_Cry", name) or name == "SFX_Headers_%d" % b:
                continue
            short = re.sub(r"_[123]$", "", name.replace("SFX_", ""))
            if short in seen or (only and short not in only):
                continue
            seen.add(short)
            e = Engine(prog, waves, w5a1, noise_by_bank[b])
            for ch, lab in chans:
                c = e.start(ch, lab)
            x = run(e, 60 * 10, tail_frames=6)
            pcm = finish(x)
            write_wav(os.path.join(OUT, "sfx", short + ".wav"), pcm)
            meta["sfx"][short] = {"len": len(pcm)}
    print("sfx", len(meta["sfx"]))

    # 울음소리: 종 별로 (기본 울음, 음높이, 길이) 적용
    cry_rows = []
    for raw in open(os.path.join(SRC, "data", "pokemon", "cries.asm"), encoding="utf-8"):
        m = re.match(r"\s*mon_cry SFX_CRY_(\w+), \$(\w+), \$(\w+)\s*;\s*(.+)", raw)
        if m:
            cry_rows.append((int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16)))
    # 내부 번호 순서 -> 종 상수
    consts = []
    for raw in open(os.path.join(SRC, "constants", "pokemon_constants.asm"), encoding="utf-8"):
        ln = raw.split(";")[0].strip()
        if ln.startswith("const_skip"):
            consts.append(None)
        elif ln.startswith("const ") and not ln.startswith("const_"):
            consts.append(ln.split()[1])
    # consts[0] = NO_MON
    for i, row in enumerate(cry_rows):
        sp = consts[i + 1] if i + 1 < len(consts) else None
        if not sp or (only and sp not in only):
            continue
        base, pitch, length = row
        lab = "SFX_Cry%02X_1" % base
        if lab not in sfx_hdrs[1]:
            continue
        e = Engine(prog, waves, w5a1, noise_by_bank[1])
        e.cry = (pitch, length)
        for ch, l in sfx_hdrs[1][lab]:
            e.start(ch, l)
        # 울음은 ch5 가 끝나면 전체 종료
        chunks = []
        acc = 0.0
        f = 0
        end = None
        while f < 60 * 5:
            e.update()
            acc += SPF
            n = int(acc)
            acc -= n
            mix = np.zeros(n, dtype=np.float32)
            for hw in e.hw:
                s = hw.render(n)
                if s is not None:
                    mix += s
            chunks.append(mix)
            f += 1
            if not e.chans[4].active:
                break
        pcm = finish(np.concatenate(chunks))
        write_wav(os.path.join(OUT, "cries", sp.lower() + ".wav"), pcm)
        meta["cries"][sp] = {"len": len(pcm)}
    print("cries", len(meta["cries"]))

    if not only:
        with open(os.path.join(DATA, "audio.json"), "w", encoding="utf-8") as fp:
            json.dump(meta, fp)


if __name__ == "__main__":
    main()
