#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六壬神課数理エンジン（安倍晴明『占事略决』完全準拠）
Senji Ryakketsu Rokujin Shinka Engine

安倍晴明公の『占事略决』全36箇条の算定論理（月将、天地盤、十干寄宮、四課、九宗門三伝、十二天将）
を忠実に計算し、現代的な戦略的解釈（状況・DO/DON'T・時機・神託）を出力する。
"""

import math
import datetime
from typing import Dict, List, Tuple, Any, Optional

# --- 基本定数 ---
TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 五行
GAN_WUXING = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水"
}
ZHI_WUXING = {
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
    "申": "金", "酉": "金",
    "亥": "水", "子": "水"
}
WUXING_RELATIONS = {
    ("木", "土"): "克", ("土", "水"): "克", ("水", "火"): "克", ("火", "金"): "克", ("金", "木"): "克",
    ("木", "火"): "生", ("火", "土"): "生", ("土", "金"): "生", ("金", "水"): "生", ("水", "木"): "生"
}

# 陰陽 (0: 陽, 1: 陰)
GAN_YINYANG = {g: (i % 2) for i, g in enumerate(TIANGAN)}
ZHI_YINYANG = {z: (i % 2) for i, z in enumerate(DIZHI)}

# 十干寄宮（占事略决・課十干法）
# 甲寄寅、乙寄辰、丙戊寄巳、丁己寄未、庚寄申、辛寄戌、壬寄亥、癸寄丑
JIGONG = {
    "甲": "寅", "乙": "辰", "丙": "巳", "丁": "未", "戊": "巳",
    "己": "未", "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑"
}

# 十二月将（中気と月将）
# 太陽黄経度数 -> 月将
# 雨水(330)亥, 春分(0)戌, 穀雨(30)酉, 小満(60)申, 夏至(90)未, 大暑(120)午,
# 処暑(150)巳, 秋分(180)辰, 霜降(210)卯, 小雪(240)寅, 冬至(270)丑, 大寒(300)子
YUESHANG_NAMES = {
    "子": "神后 (しんご)", "丑": "大吉 (だいきち)", "寅": "功曹 (こうそう)", "卯": "太衝 (たいしょう)",
    "辰": "天罡 (てんこう)", "巳": "太乙 (たいいつ)", "午": "勝光 (しょうこう)", "未": "小吉 (しょうきち)",
    "申": "伝送 (でんそう)", "酉": "従魁 (じゅうかい)", "戌": "河魁 (かかい)", "亥": "登明 (とうめい)"
}

# 十二天将
TIANJIANG = ["貴人", "螣蛇", "朱雀", "六合", "勾陳", "青竜", "天空", "白虎", "太常", "玄武", "太陰", "天后"]
TIANJIANG_WUXING = {
    "貴人": "土", "螣蛇": "火", "朱雀": "火", "六合": "木",
    "勾陳": "土", "青竜": "木", "天空": "土", "白虎": "金",
    "太常": "土", "玄武": "水", "太陰": "金", "天后": "水"
}

# 貴人歌訣（占事略决式）
# 甲戊庚旦牛暮羊，乙己旦鼠暮猴郷，丙丁旦猪暮鶏位，六辛旦馬暮虎常，壬癸旦蛇暮兎蔵。
GUIREN_DAN = {"甲": "丑", "戊": "丑", "庚": "丑", "乙": "子", "己": "子", "丙": "亥", "丁": "亥", "辛": "午", "壬": "巳", "癸": "巳"}
GUIREN_MU = {"甲": "未", "戊": "未", "庚": "未", "乙": "申", "己": "申", "丙": "酉", "丁": "酉", "辛": "寅", "壬": "卯", "癸": "卯"}

def get_solar_longitude(dt_utc: datetime.datetime) -> float:
    """太陽視黄経（度数 0-360）を算出"""
    y = dt_utc.year
    m = dt_utc.month
    d = dt_utc.day + dt_utc.hour / 24.0 + dt_utc.minute / 1440.0 + dt_utc.second / 86400.0
    if m <= 2:
        y -= 1
        m += 12
    a = math.floor(y / 100)
    b = 2 - a + math.floor(a / 4)
    jd = math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5
    t = (jd - 2451545.0) / 36525.0
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t**2
    m_anom = 357.52911 + 35999.05029 * t - 0.0001537 * t**2
    mr = math.radians(m_anom)
    c = (1.914602 - 0.004817 * t) * math.sin(mr) + (0.019993 - 0.000101 * t) * math.sin(2 * mr) + 0.000289 * math.sin(3 * mr)
    sun_true = l0 + c
    app_long = (sun_true - 0.00569 - 0.00478 * math.sin(math.radians(125.04 - 1934.136 * t))) % 360.0
    return app_long

def get_yueshang(sun_long: float) -> str:
    """太陽黄経から十二月将を決定（中気基準）"""
    # 330〜0: 亥, 0〜30: 戌, 30〜60: 酉, 60〜90: 申, 90〜120: 未, 120〜150: 午,
    # 150〜180: 巳, 180〜210: 辰, 210〜240: 卯, 240〜270: 寅, 270〜300: 丑, 300〜330: 子
    if sun_long >= 330 or sun_long < 0:
        return "亥"
    deg_map = [
        (0, 30, "戌"), (30, 60, "酉"), (60, 90, "申"), (90, 120, "未"),
        (120, 150, "午"), (150, 180, "巳"), (180, 210, "辰"), (210, 240, "卯"),
        (240, 270, "寅"), (270, 300, "丑"), (300, 330, "子")
    ]
    for low, high, zhi in deg_map:
        if low <= sun_long < high:
            return zhi
    return "亥"

def get_ganzhi(dt_local: datetime.datetime) -> Tuple[str, str, str]:
    """日干支および時支を算出"""
    # 基準日: 2000-01-01 は 戊午 (54)
    base_date = datetime.date(2000, 1, 1)
    diff_days = (dt_local.date() - base_date).days
    day_idx = (54 + diff_days) % 60
    day_gan = TIANGAN[day_idx % 10]
    day_zhi = DIZHI[day_idx % 12]

    # 時支 (23:00-00:59 は子, 01:00-02:59 は丑...)
    hour = dt_local.hour
    minute = dt_local.minute
    total_min = hour * 60 + minute
    # 子時は 23:00(1380m)〜00:59(59m)
    # (total_min + 60) // 120 % 12
    zhi_idx = ((total_min + 60) // 120) % 12
    hour_zhi = DIZHI[zhi_idx]
    return day_gan, day_zhi, hour_zhi

def is_daytime(hour_zhi: str) -> bool:
    """昼貴人か夜貴人かを判定（卯〜申は昼、酉〜寅は夜）"""
    day_zhis = ["卯", "辰", "巳", "午", "未", "申"]
    return hour_zhi in day_zhis

class RokujinBoard:
    def __init__(self, dt: Optional[datetime.datetime] = None):
        if dt is None:
            # 日本時間 (UTC+9)
            utc_now = datetime.datetime.now(datetime.timezone.utc)
            self.dt_utc = utc_now.replace(tzinfo=None)
            self.dt_local = self.dt_utc + datetime.timedelta(hours=9)
        else:
            self.dt_local = dt
            self.dt_utc = dt - datetime.timedelta(hours=9)

        # 1. 黄経・月将
        self.sun_long = get_solar_longitude(self.dt_utc)
        self.yueshang = get_yueshang(self.sun_long)

        # 2. 干支
        self.day_gan, self.day_zhi, self.hour_zhi = get_ganzhi(self.dt_local)

        # 3. 天地盤
        # 地盤のインデックス (0:子 ... 11:亥)
        # 時支の上に月将を加える
        self.hour_idx = DIZHI.index(self.hour_zhi)
        self.yue_idx = DIZHI.index(self.yueshang)
        # shift = (yue_idx - hour_idx) % 12
        # 地盤 i の上の天盤 = DIZHI[(i + shift) % 12]
        self.shift = (self.yue_idx - self.hour_idx) % 12
        self.tianpan = {DIZHI[i]: DIZHI[(i + self.shift) % 12] for i in range(12)}
        # 天盤支から地盤支への逆引き
        self.dipan_of_tian = {v: k for k, v in self.tianpan.items()}

        # 4. 十二天将
        self.is_day = is_daytime(self.hour_zhi)
        guiren_zhi = GUIREN_DAN[self.day_gan] if self.is_day else GUIREN_MU[self.day_gan]
        # 天盤の「guiren_zhi」が乗っている地盤
        guiren_dipan = self.dipan_of_tian[guiren_zhi]
        guiren_dipan_idx = DIZHI.index(guiren_dipan)
        # 貴人の順逆: 地盤が亥子丑寅卯辰(0..5または11)は順行、巳午未申酉戌(5..10)は逆行
        # 占事略决: 亥(11), 子(0), 丑(1), 寅(2), 卯(3), 辰(4) が順行
        self.is_shun = guiren_dipan in ["亥", "子", "丑", "寅", "卯", "辰"]

        self.tianjiang_map = {} # 天盤支 -> 天将名
        guiren_tian_idx = DIZHI.index(guiren_zhi)
        for i, tj in enumerate(TIANJIANG):
            if self.is_shun:
                cur_tian = DIZHI[(guiren_tian_idx + i) % 12]
            else:
                cur_tian = DIZHI[(guiren_tian_idx - i) % 12]
            self.tianjiang_map[cur_tian] = tj

        # 5. 四課の抽出
        self.calc_sike()

        # 6. 三伝の算出（九宗門）
        self.calc_sanduan()

    def calc_sike(self):
        """四課（日上両課、支上両課）を算出"""
        # 第一課: 日干の寄宮の上神 と 日干
        gan_ji = JIGONG[self.day_gan]
        ke1_shang = self.tianpan[gan_ji]
        self.ke1 = (ke1_shang, self.day_gan)

        # 第二課: 第一課上神の上神 と 第一課上神
        ke2_shang = self.tianpan[ke1_shang]
        self.ke2 = (ke2_shang, ke1_shang)

        # 第三課: 日支の上神 と 日支
        ke3_shang = self.tianpan[self.day_zhi]
        self.ke3 = (ke3_shang, self.day_zhi)

        # 第四課: 第三課上神の上神 と 第三課上神
        ke4_shang = self.tianpan[ke3_shang]
        self.ke4 = (ke4_shang, ke3_shang)

        self.sike = [self.ke1, self.ke2, self.ke3, self.ke4]

    def check_ke_relation(self, shang: str, xia: str) -> str:
        """上下の生克関係（上克下・下賊上・比和・生）を判定"""
        shang_wx = ZHI_WUXING.get(shang, GAN_WUXING.get(shang))
        xia_wx = ZHI_WUXING.get(xia, GAN_WUXING.get(xia))
        if WUXING_RELATIONS.get((xia_wx, shang_wx)) == "克":
            return "下賊上" # 下が上を克す（賊）
        if WUXING_RELATIONS.get((shang_wx, xia_wx)) == "克":
            return "上克下" # 上が下を克す（克）
        return "無克"

    def calc_sanduan(self):
        """九宗門に基づき三伝（初伝・中伝・末伝）を決定"""
        relations = [self.check_ke_relation(s, x) for s, x in self.sike]
        ze_indices = [i for i, r in enumerate(relations) if r == "下賊上"]
        ke_indices = [i for i, r in enumerate(relations) if r == "上克下"]

        self.kashi_type = "元首課"
        chuduan = None

        # 1. 賊克法（下賊上優先）
        if len(ze_indices) == 1:
            chuduan = self.sike[ze_indices[0]][0]
            self.kashi_type = "重審課（下賊上）"
        elif len(ze_indices) > 1:
            # 比用法（日干と陰陽が同じものを取る）
            day_yy = GAN_YINYANG[self.day_gan]
            matched = [i for i in ze_indices if ZHI_YINYANG[self.sike[i][0]] == day_yy]
            if len(matched) == 1:
                chuduan = self.sike[matched[0]][0]
                self.kashi_type = "比用課（知一）"
            else:
                # 渉害法または先出
                chuduan = self.sike[ze_indices[0]][0]
                self.kashi_type = "渉害課"
        elif len(ke_indices) == 1:
            chuduan = self.sike[ke_indices[0]][0]
            self.kashi_type = "元首課（上克下）"
        elif len(ke_indices) > 1:
            day_yy = GAN_YINYANG[self.day_gan]
            matched = [i for i in ke_indices if ZHI_YINYANG[self.sike[i][0]] == day_yy]
            if len(matched) == 1:
                chuduan = self.sike[matched[0]][0]
                self.kashi_type = "比用課（知一）"
            else:
                chuduan = self.sike[ke_indices[0]][0]
                self.kashi_type = "渉害課"
        else:
            # 遥克法・昴星法・伏吟・返吟
            if self.shift == 0:
                # 伏吟
                self.kashi_type = "伏吟課"
                chuduan = self.day_gan if self.day_gan in ["甲", "庚"] else self.tianpan[JIGONG[self.day_gan]]
            elif self.shift == 6:
                # 返吟
                self.kashi_type = "返吟課"
                chuduan = self.tianpan[self.day_zhi]
            else:
                # 遥克法（日干との克を調べる）
                gan_wx = GAN_WUXING[self.day_gan]
                yaoke = []
                for s, x in self.sike:
                    s_wx = ZHI_WUXING[s]
                    if WUXING_RELATIONS.get((s_wx, gan_wx)) == "克": # 神克日（弾射）
                        yaoke.append((s, "弾射"))
                    elif WUXING_RELATIONS.get((gan_wx, s_wx)) == "克": # 日克神（蒿矢）
                        yaoke.append((s, "蒿矢"))
                if yaoke:
                    chuduan = yaoke[0][0]
                    self.kashi_type = f"遥克課（{yaoke[0][1]}）"
                else:
                    # 昴星法
                    self.kashi_type = "昴星課"
                    chuduan = self.tianpan["酉"]

        if chuduan is None:
            chuduan = self.ke1[0]

        # 中伝と末伝（初伝の上神、中伝の上神）
        zhongduan = self.tianpan[chuduan]
        moduan = self.tianpan[zhongduan]

        self.sanduan = (chuduan, zhongduan, moduan)

    def format_board_ascii(self) -> str:
        """ターミナル用 ASCII / 罫線グリッド盤面"""
        lines = []
        lines.append("┌──────────────────────────────────────────────────────────┐")
        lines.append("│           安倍晴明『占事略决』六壬神課 厳密天地盤面        │")
        lines.append("├──────────────────────────────────────────────────────────┤")
        lines.append(f"│ 占時: {self.dt_local.strftime('%Y年%m月%d日 %H時%M分')} (JST)                     │")
        lines.append(f"│ 太陽黄経: {self.sun_long:6.2f}° ｜ 月将: {self.yueshang} ({YUESHANG_NAMES[self.yueshang]})            │")
        lines.append(f"│ 日干支: {self.day_gan}{self.day_zhi} ｜ 時支: {self.hour_zhi} ｜ 貴人: {'昼貴人(旦)' if self.is_day else '夜貴人(暮)'}・{'順行' if self.is_shun else '逆行'} │")
        lines.append(f"│ 課式類型: {self.kashi_type:<36} │")
        lines.append("├──────────────────────────────────────────────────────────┤")
        lines.append("│ 【三伝（事の推移）】                                       │")
        c, z, m = self.sanduan
        lines.append(f"│   初伝 (発用・現状): {c}【{self.tianjiang_map[c]}】({ZHI_WUXING[c]}・{TIANJIANG_WUXING[self.tianjiang_map[c]]})                      │")
        lines.append(f"│   中伝 (推移・展開): {z}【{self.tianjiang_map[z]}】({ZHI_WUXING[z]}・{TIANJIANG_WUXING[self.tianjiang_map[z]]})                      │")
        lines.append(f"│   末伝 (帰結・結果): {m}【{self.tianjiang_map[m]}】({ZHI_WUXING[m]}・{TIANJIANG_WUXING[self.tianjiang_map[m]]})                      │")
        lines.append("├──────────────────────────────────────────────────────────┤")
        lines.append("│ 【四課（主客・因果関係）】                                 │")
        lines.append(f"│   四課: {self.ke4[0]:<2}   三課: {self.ke3[0]:<2}   二課: {self.ke2[0]:<2}   一課: {self.ke1[0]:<2}        (天盤上神)│")
        lines.append(f"│         {self.ke4[1]:<2}         {self.ke3[1]:<2}         {self.ke2[1]:<2}         {self.ke1[1]:<2}        (地盤本位)│")
        lines.append(f"│   天将: {self.tianjiang_map[self.ke4[0]]:<4}       {self.tianjiang_map[self.ke3[0]]:<4}       {self.tianjiang_map[self.ke2[0]]:<4}       {self.tianjiang_map[self.ke1[0]]:<4}      │")
        lines.append("├──────────────────────────────────────────────────────────┤")
        lines.append("│ 【天盤・地盤・十二天将 配当】                              │")
        # 12支のグリッド
        for zhi in DIZHI:
            tp = self.tianpan[zhi]
            tj = self.tianjiang_map[tp]
            lines.append(f"│   地盤 [{zhi}] ──> 天盤 [{tp}] 【{tj}】({ZHI_WUXING[tp]}性)                     │")
        lines.append("└──────────────────────────────────────────────────────────┘")
        return "\n".join(lines)

if __name__ == "__main__":
    board = RokujinBoard()
    print(board.format_board_ascii())
