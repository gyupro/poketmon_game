# 포켓몬스터 레드 온라인 (Godot 4.4)

> **Claude Opus 5.5로 만든 포켓몬입니다.**
> 기획부터 원작 데이터 변환기, 게임 코드, 사운드 렌더러, 한국어 번역, 테스트까지 전부 Anthropic의 Claude Opus 5.5(Claude Code)가 작성했습니다.

Claude 버전별로 만든 포켓몬 게임을 비교한 기록이에요.

## Before / After

### Before (2025 Claude)
![Before - Battle Animation](docs/versions/2025_claude.gif)

### After (2026 Claude)

Python + Pygame으로 만든 버전이에요. 코드는 [`python-version` 태그](https://github.com/gyupro/poketmon_game/tree/python-version)에 남아 있어요.

| World Exploration | Battle System |
|:-:|:-:|
| ![Pallet Town](docs/versions/2026_world_npc.png) | ![Battle Scene](docs/versions/2026_battle_scene.png) |
| *Textured tiles, animated NPCs, character sprites* | *Gradient sky, type badges, HP bars* |

| Pokemon Team | Pause Menu |
|:-:|:-:|
| ![Pokemon Menu](docs/versions/2026_pokemon_menu.png) | ![Pause Menu](docs/versions/2026_pause_menu.png) |
| *Card layout with moves, stats, type badges* | *Dark-theme translucent overlay* |

| Starter Selection |
|:-:|
| ![Starter Select](docs/versions/2026_starter_select.png) |
| *Choose Bulbasaur, Charmander, or Squirtle* |

### Now (Claude Opus 5.5)

원작 **포켓몬스터 레드**의 역어셈블리 소스([pret/pokered](https://github.com/pret/pokered))에서
맵·그래픽·음악·포켓몬·기술·트레이너·대사를 전부 추출해 Godot으로 다시 만든 **2인 협동 멀티플레이 + 한국어** 버전이에요.
태초마을부터 챔피언, 전당 등록, 엔딩까지 원작 스토리를 모두 즐길 수 있어요.

| 필드 · 배틀 · 파도타기 | 스토리 (오박사 등장) |
|:---:|:---:|
| ![플레이 영상](docs/play.gif) | ![스토리 영상](docs/story.gif) |

## 주요 기능

- **원작 맵 222개**: 타일, 충돌, 턱, 문, 워프, 맵 연결, NPC, 표지판, 숨겨진 아이템까지 원작과 같아요. 마을마다 슈퍼게임보이 색이 들어가요.
- **1세대 배틀**:
  - 데미지 공식, 급소, 타입 상성, 상태이상, 기술 효과 대부분
  - 포획, 경험치, 기술 배우기, 진화(레벨/돌/교환)
- **음악·효과음·울음소리**: 원작 사운드 데이터를 게임보이 음원처럼 직접 연주해서 렌더링했어요.
  - BGM 45곡, 효과음 104개, 포켓몬 울음소리 151종
- **필드 기술**:
  - 풀베기, 파도타기, 괴력, 플래시, 공중날기, 구멍파기, 순간이동, 알까기
  - 자전거, 낚싯대 3종, 기술머신·비전머신
- **스토리 전체**:
  - 체육관 관장 8명
  - 로켓단 아지트, 포켓몬타워, 실프주식회사(카드키)
  - 사파리존, 홍련섬 퀴즈, 쌍둥이섬, 챔피언로드 퍼즐
  - 사천왕, 챔피언, 전당 등록, 엔딩
- **부가 요소**: 게임코너 슬롯·경품, 자판기, 이름 평가인, 키우미집, NPC 교환, 화석 부활, 전설의 포켓몬
- **한국어**: 대사 약 1,870개와 포켓몬·기술·도구 이름을 한국어로 옮겼어요.
- **멀티플레이**: 친구와 같은 월드에서 서로 보면서 모험할 수 있고, 통신 대전과 교환도 돼요.

## 설치 (소스에서)

원작 그래픽·음악·데이터는 닌텐도의 저작물이라 **이 저장소에는 들어 있지 않아요.**
대신 pret/pokered 역어셈블리에서 직접 생성하는 스크립트가 들어 있어요.

필요한 것:
- [Godot 4.4.1](https://godotengine.org/download/archive/4.4.1-stable/) (Standard)
- Python 3.10 이상, `pip install pillow numpy`
- git

```bash
git clone https://github.com/gyupro/poketmon_game
cd poketmon_game
python tools/setup.py "C:\Godot\Godot_v4.4.1-stable_win64_console.exe"
```

`setup.py`가 하는 일:
1. pret/pokered를 `pokered_src/`로 받아요.
2. 음악과 효과음을 렌더링해요.
3. 맵, 그래픽, 데이터를 변환해요.
4. Godot 임포트까지 실행해요.

끝나면 `play.bat`(Godot 경로가 `C:\Godot`일 때)을 실행하거나, Godot 에디터로 `game/project.godot`을 열고 F5를 누르면 돼요.

친구에게 보낼 실행 파일 묶음은 `python tools/make_package.py`로 만들어요. `dist/pokemon_online.zip`이 생기고, Godot가 포함돼 있어서 압축을 풀고 `play.bat`만 실행하면 돼요.

## 조작

| 키 | 기능 |
|---|---|
| 방향키 / WASD | 이동 (톡 치면 방향만 전환) |
| Z / Space / J | A 버튼 (말 걸기·결정) |
| X / Backspace / K | B 버튼 (취소) · 필드에서 누른 채 걸으면 달리기 |
| Enter | START (메뉴) |
| Shift | SELECT · 자전거 타기/내리기 |

나무 앞이나 물가에서 A를 누르면 풀베기·파도타기를 바로 쓸 수 있어요.

## 친구와 같이 하기

1. 한 명이 타이틀에서 **방 만들기**를 누르면 화면에 IP가 나와요. 이 IP를 친구에게 알려 주세요.
2. 친구는 **친구 방 참가**를 누르고 IP를 입력해요.
3. 같은 맵에 있으면 서로 보여요. 친구 앞에서 **A**를 누르면 **대전 / 교환**을 신청할 수 있어요.

- 포트는 **UDP 24680**이에요. 인터넷으로 할 때는 아래 중 하나를 쓰면 돼요.
  - Radmin VPN / Tailscale / ZeroTier 같은 가상 LAN (가장 쉬워요)
  - 호스트 공유기에서 포트포워딩
- 세이브는 각자 따로예요.
  - 대전은 원작 통신대전처럼 결과가 파티에 영향을 주지 않아요.
  - 교환은 실제로 교환되고, 교환 진화(윤겔라 → 후딘 등)도 돼요.

## 구조

```
tools/
  setup.py           처음 설치 (pokered 받기 → 음원 렌더링 → 데이터 변환 → 임포트)
  convert.py         pokered → game/data/*.json, game/assets/** 변환기
  audio_render.py    pokered 사운드 엔진 재현 → 음악/효과음/울음소리 WAV
  ko_names.py        포켓몬/기술/도구/트레이너 한국어 이름
  make_package.py    친구용 실행 zip 생성
game/
  data/ko.json       한국어 대사 (키: 원작 텍스트 라벨) ← 번역 수정은 여기
  scripts/core/      데이터, 세이브, 포켓몬 계산, 사운드, 네트워크, 대전/교환
  scripts/overworld/ 필드, 캐릭터, 필드 기술, 이벤트 분배
  scripts/story/     구간별 스토리 스크립트, 체육관 관장 ← 스토리 수정은 여기
  scripts/battle/    1세대 배틀 로직, 배틀 화면/PvP
  scripts/ui/        대화창, 메뉴, 타이틀
  scripts/debug/     자동 테스트 (Godot --path game -- autotest=명령파일)
```

## 크레딧

- 원작: GAME FREAK / Nintendo / Creatures — 포켓몬스터 레드
- 역어셈블리: [pret/pokered](https://github.com/pret/pokered)
- 폰트: [Galmuri](https://github.com/quiple/galmuri) (SIL Open Font License 1.1)
- 개발: **Claude Opus 5.5** (Anthropic, Claude Code)

비상업적인 팬 프로젝트이며, 포켓몬 관련 권리는 모두 원저작자에게 있어요.
