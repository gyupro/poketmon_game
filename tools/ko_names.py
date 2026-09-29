# 한국어 이름 테이블 (1세대 정발 기준)

KO_POKEMON = """이상해씨 이상해풀 이상해꽃 파이리 리자드 리자몽 꼬부기 어니부기 거북왕 캐터피
단데기 버터플 뿔충이 딱충이 독침붕 구구 피죤 피죤투 꼬렛 레트라
깨비참 깨비드릴조 아보 아보크 피카츄 라이츄 모래두지 고지 니드런♀ 니드리나
니드퀸 니드런♂ 니드리노 니드킹 삐삐 픽시 식스테일 나인테일 푸린 푸크린
주뱃 골뱃 뚜벅쵸 냄새꼬 라플레시아 파라스 파라섹트 콘팡 도나리 디그다
닥트리오 나옹 페르시온 고라파덕 골덕 망키 성원숭 가디 윈디 발챙이
슈륙챙이 강챙이 캐이시 윤겔라 후딘 알통몬 근육몬 괴력몬 모다피 우츠동
우츠보트 왕눈해 독파리 꼬마돌 데구리 딱구리 포니타 날쌩마 야돈 야도란
코일 레어코일 파오리 두두 두트리오 쥬쥬 쥬레곤 질퍽이 질뻐기 셀러
파르셀 고오스 고우스트 팬텀 롱스톤 슬리프 슬리퍼 크랩 킹크랩 찌리리공
붐볼 아라리 나시 탕구리 텅구리 시라소몬 홍수몬 내루미 또가스 또도가스
뿔카노 코뿌리 럭키 덩쿠리 캥카 쏘드라 시드라 콘치 왕콘치 별가사리
아쿠스타 마임맨 스라크 루주라 에레브 마그마 쁘사이저 켄타로스 잉어킹 갸라도스
라프라스 메타몽 이브이 샤미드 쥬피썬더 부스터 폴리곤 암나이트 암스타 투구
투구푸스 프테라 잠만보 프리져 썬더 파이어 미뇽 신뇽 망나뇽 뮤츠
뮤""".split()
assert len(KO_POKEMON) == 151, len(KO_POKEMON)

KO_MOVES = """막치기 태권당수 연속뺨치기 연속펀치 메가톤펀치 고양이돈받기 불꽃펀치 냉동펀치 번개펀치 할퀴기
찝기 가위자르기 칼바람 칼춤 풀베기 바람일으키기 날개치기 날려버리기 공중날기 조이기
힘껏치기 덩굴채찍 짓밟기 두번치기 메가톤킥 점프킥 돌려차기 모래뿌리기 박치기 뿔찌르기
마구찌르기 뿔드릴 몸통박치기 누르기 김밥말이 돌진 난동부리기 이판사판태클 꼬리흔들기 독침
더블니들 바늘미사일 째려보기 물기 울음소리 울부짖기 노래하기 초음파 소닉붐 사슬묶기
용해액 불꽃세례 화염방사 흰안개 물대포 하이드로펌프 파도타기 냉동빔 눈보라 환상빔
거품광선 오로라빔 파괴광선 쪼기 회전부리 지옥의바퀴 안다리걸기 카운터 지구던지기 괴력
흡수 메가드레인 씨뿌리기 성장 잎날가르기 솔라빔 독가루 저리가루 수면가루 꽃잎댄스
실뿜기 용의분노 회오리불꽃 전기쇼크 10만볼트 전기자석파 번개 돌떨구기 지진 땅가르기
구멍파기 맹독 염동력 사이코키네시스 최면술 요가포즈 고속이동 전광석화 분노 순간이동
나이트헤드 흉내내기 싫은소리 그림자분신 HP회복 단단해지기 작아지기 연막 이상한빛 껍질에숨기
웅크리기 배리어 빛의장막 흑안개 리플렉터 기충전 참기 손가락흔들기 따라하기 자폭
알폭탄 핥기 스모그 오물공격 뼈다귀치기 불대문자 폭포오르기 껍질끼우기 스피드스타 로케트박치기
가시대포 휘감기 망각술 숟가락휘기 알낳기 무릎차기 뱀눈초리 꿈먹기 독가스 구슬던지기
흡혈 악마의키스 불새 변신 거품 잼잼펀치 버섯포자 플래시 사이코웨이브 튀어오르기
녹기 찝게햄머 대폭발 마구할퀴기 뼈다귀부메랑 잠자기 스톤샤워 필살앞니 각지기 텍스처
트라이어택 분노의앞니 베어가르기 대타출동 발버둥""".split()
assert len(KO_MOVES) == 165, len(KO_MOVES)

KO_TYPES = {
    "NORMAL": "노말", "FIGHTING": "격투", "FLYING": "비행", "POISON": "독", "GROUND": "땅",
    "ROCK": "바위", "BUG": "벌레", "GHOST": "고스트", "FIRE": "불꽃", "WATER": "물",
    "GRASS": "풀", "ELECTRIC": "전기", "PSYCHIC_TYPE": "에스퍼", "ICE": "얼음", "DRAGON": "드래곤",
    "BIRD": "새",
}

KO_ITEMS = {
    "MASTER_BALL": "마스터볼", "ULTRA_BALL": "하이퍼볼", "GREAT_BALL": "수퍼볼", "POKE_BALL": "몬스터볼",
    "TOWN_MAP": "타운맵", "BICYCLE": "자전거", "SAFARI_BALL": "사파리볼", "POKEDEX": "포켓몬 도감",
    "MOON_STONE": "달의돌", "ANTIDOTE": "해독제", "BURN_HEAL": "화상치료제", "ICE_HEAL": "얼음상태치료제",
    "AWAKENING": "잠깨는약", "PARLYZ_HEAL": "마비치료제", "FULL_RESTORE": "회복약", "MAX_POTION": "풀회복약",
    "HYPER_POTION": "고급상처약", "SUPER_POTION": "좋은상처약", "POTION": "상처약",
    "BOULDERBADGE": "회색배지", "CASCADEBADGE": "블루배지", "THUNDERBADGE": "오렌지배지",
    "RAINBOWBADGE": "무지개배지", "SOULBADGE": "핑크배지", "MARSHBADGE": "골드배지",
    "VOLCANOBADGE": "진홍배지", "EARTHBADGE": "그린배지",
    "ESCAPE_ROPE": "동굴탈출로프", "REPEL": "벌레회피스프레이", "OLD_AMBER": "비밀의호박",
    "FIRE_STONE": "불꽃의돌", "THUNDER_STONE": "천둥의돌", "WATER_STONE": "물의돌",
    "HP_UP": "맥스업", "PROTEIN": "타우린", "IRON": "사포닌", "CARBOS": "알칼로이드",
    "CALCIUM": "리보플라빈", "RARE_CANDY": "이상한사탕", "DOME_FOSSIL": "껍질화석",
    "HELIX_FOSSIL": "조개화석", "SECRET_KEY": "비밀열쇠", "BIKE_VOUCHER": "자전거교환권",
    "X_ACCURACY": "잘-맞히기", "LEAF_STONE": "리프의돌", "CARD_KEY": "카드키", "NUGGET": "금구슬",
    "POKE_DOLL": "삐삐인형", "FULL_HEAL": "만병통치제", "REVIVE": "기력의조각",
    "MAX_REVIVE": "기력의덩어리", "GUARD_SPEC": "이펙트가드", "SUPER_REPEL": "실버스프레이",
    "MAX_REPEL": "골드스프레이", "DIRE_HIT": "크리티컷", "COIN": "코인", "FRESH_WATER": "맛있는물",
    "SODA_POP": "미네랄사이다", "LEMONADE": "후르츠밀크", "S_S_TICKET": "배표", "GOLD_TEETH": "금틀니",
    "X_ATTACK": "플러스파워", "X_DEFEND": "디펜드업", "X_SPEED": "스피드업", "X_SPECIAL": "스페셜업",
    "COIN_CASE": "동전케이스", "OAKS_PARCEL": "오박사의 소포", "ITEMFINDER": "다우징머신",
    "SILPH_SCOPE": "실프스코프", "POKE_FLUTE": "포켓몬피리", "LIFT_KEY": "엘리베이터키",
    "EXP_ALL": "학습장치", "OLD_ROD": "낡은낚싯대", "GOOD_ROD": "좋은낚싯대", "SUPER_ROD": "대단한낚싯대",
    "PP_UP": "포인트업", "ETHER": "PP에이드", "MAX_ETHER": "PP회복", "ELIXER": "PP에이더",
    "MAX_ELIXER": "PP맥스",
}

KO_TRAINERS = {
    "YOUNGSTER": "반바지 꼬마", "BUG_CATCHER": "곤충채집 소년", "LASS": "짧은치마",
    "SAILOR": "뱃사람", "JR_TRAINER_M": "꼬마 트레이너♂", "JR_TRAINER_F": "꼬마 트레이너♀",
    "POKEMANIAC": "포켓몬 마니아", "SUPER_NERD": "괴짜", "HIKER": "등산가", "BIKER": "폭주족",
    "BURGLAR": "도둑", "ENGINEER": "기술자", "FISHER": "낚시꾼", "SWIMMER": "수영팬티 소년",
    "CUE_BALL": "빡빡이", "GAMBLER": "승부사", "BEAUTY": "아가씨", "PSYCHIC_TR": "초능력자",
    "ROCKER": "로커", "JUGGLER": "요술쟁이", "TAMER": "조련사", "BIRD_KEEPER": "새조련사",
    "BLACKBELT": "태권왕", "RIVAL1": "라이벌", "PROF_OAK": "오박사", "SCIENTIST": "연구원",
    "GIOVANNI": "비주기", "ROCKET": "로켓단", "COOLTRAINER_M": "엘리트 트레이너♂",
    "COOLTRAINER_F": "엘리트 트레이너♀", "BRUNO": "시바", "BROCK": "웅", "MISTY": "이슬",
    "LT_SURGE": "마티스", "ERIKA": "민화", "KOGA": "독수", "BLAINE": "강연", "SABRINA": "초련",
    "GENTLEMAN": "신사", "RIVAL2": "라이벌", "RIVAL3": "라이벌", "LORELEI": "칸나",
    "CHANNELER": "무당", "AGATHA": "국화", "LANCE": "목호",
}
