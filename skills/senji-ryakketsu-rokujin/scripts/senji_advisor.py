#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安倍晴明『占事略决』現代風六壬神課・総合鑑定アドバイザー
Senji Ryakketsu Rokujin Advisor (Hybrid: Math Engine + Gemini AI + Fallback)

計算エンジン（RokujinBoard）から算出された厳密な六壬盤（天地盤・四課・三伝・十二天将・課式）
に基づき、現代の言葉で分かりやすく解釈し、具体的行動指針（DO / DON'T / 時機 / 神託）を生成する。
"""

import sys
import os
import datetime
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rokujin_engine import RokujinBoard, ZHI_WUXING, TIANJIANG_WUXING, YUESHANG_NAMES

TIANJIANG_MODERN = {
    "貴人": {
        "title": "貴人（最高峰の庇護・社会的信用）",
        "essence": "公明正大、上司・有力者の強い後押し、公式な承認、正攻法の勝利。",
        "risk": "慢心、傲慢、形式主義に囚われて機動力を失うこと。",
        "do": ["正々堂々と筋を通す", "キーパーソンや上位層へ迅速に報告・相談する", "オープンな場で透明性を担保する"],
        "dont": ["小細工や裏工作に手を染めること", "目上の助言を軽視すること", "非公式な抜け道を探すこと"]
    },
    "螣蛇": {
        "title": "螣蛇（怪異・パニック・突発トラブル）",
        "essence": "予期せぬハプニング、疑心暗鬼、誤解による炎上、神経過敏。",
        "risk": "パニックに陥って慌てて下した判断が傷口を広げる。",
        "do": ["まず事実確認を行い、一次情報だけを信じる", "深呼吸して感情的なリアクションを24時間保留する", "火種を小さいうちに消火する"],
        "dont": ["噂話や未確認情報に踊らされること", "焦って夜中に感情的な長文メッセージを送ること", "敵を過大評価して自滅すること"]
    },
    "朱雀": {
        "title": "朱雀（情報・文書・発信と論争）",
        "essence": "メディア、SNS、プレゼン、契約書、公の議論、言葉の威力。",
        "risk": "失言、口論、揚げ足取り、契約条項の読み落としによるトラブル。",
        "do": ["公表前のドキュメントや規約を二重チェックする", "明瞭かつポジティブな言葉で意図を発信する", "記録を証跡（ログ・メール）として残す"],
        "dont": ["売り言葉に買い言葉で応酬すること", "口約束だけで重要事項を進めること", "感情に任せて公の場で批判を展開すること"]
    },
    "六合": {
        "title": "六合（調和・提携・パートナーシップ）",
        "essence": "契約締結、チームワーク、Win-Winの提携、恋愛成就、人脈の結合。",
        "risk": "馴れ合いによる妥協、共依存、役割分担の曖昧化。",
        "do": ["相手のメリットを先に提示して合意を形成する", "信頼できるパートナーとタッグを組む", "お互いの境界線と責任範囲を明確に取り決める"],
        "dont": ["一人ですべてを抱え込もうとすること", "相手への遠慮から肝心な条件を濁すこと", "不満を溜め込んで突然関係を断つこと"]
    },
    "勾陳": {
        "title": "勾陳（膠着・遅延・過去のしがらみ）",
        "essence": "進捗の停滞、対立・訴訟、古いルールや過去のトラブルのぶり返し。",
        "risk": "無理に前進しようとして泥沼に足を取られる。",
        "do": ["現状のボトルネックを徹底的に洗い出し、基盤整備に徹する", "過去の未清算な課題（負債・感情）を先に片付ける", "長期戦を覚悟し、守りを固める"],
        "dont": ["力づくで相手を屈服させようとすること", "焦って強引な突破を図ること", "手続きやルールを無視して突っ走ること"]
    },
    "青竜": {
        "title": "青竜（拡大・財運・新規挑戦）",
        "essence": "資金調達、昇進、売上急増、好機到来、積極的な攻め。",
        "risk": "調子に乗りすぎた過剰投資、リソースの枯渇、見栄。",
        "do": ["攻めの姿勢でチャンスを掴みに行く", "将来への先行投資や新スキルの習得に資金・時間を使う", "成果を周囲に分配して味方を増やす"],
        "dont": ["過信してリスク管理を放棄すること", "身の丈に合わない浪費・大風呂敷を広げること", "成功の要因をすべて自分の実力だと過信すること"]
    },
    "天空": {
        "title": "天空（虚妄・空虚とクリエイティブ）",
        "essence": "実体のない話、誇大広告、口約束の不履行、しかし企画・着想・断捨離には絶大な効果。",
        "risk": "絵に描いた餅にリソースを注ぎ込む、詐欺まがいの甘言に引っかかる。",
        "do": ["アイデアを具体化する前にプロトタイプで検証する", "不要になった物や執着を大胆に断捨離する", "言葉の裏にある『実態』を冷静に見極める"],
        "dont": ["根拠のない甘い話・誇大広告を真に受けること", "実行計画のない思いつきだけで人を巻き込むこと", "形骸化した無駄な作業に固執し続けること"]
    },
    "白虎": {
        "title": "白虎（急変・衝突・外科的メス）",
        "essence": "急激なショック、厳しい指摘、健康面の注意、不要なものの強制終了。",
        "risk": "激しい衝突、怪我・体調不良、感情的な攻撃による破綻。",
        "do": ["ダメなプロジェクトや関係性に迅速に損切り・メスを入れる", "健康管理・休養を最優先し、過労を防ぐ", "突発的なトラブルに備えて予備リソースを確保する"],
        "dont": ["危険な兆候を無視して無理を重ねること", "他人に八つ当たりして攻撃的な態度を取ること", "安全確認を怠ってスピードを優先すること"]
    },
    "太常": {
        "title": "太常（平穏・飲食・日常の報酬）",
        "essence": "会食、リフレッシュ、日常の確かな成果、穏やかな人間関係、習慣化。",
        "risk": "現状維持への甘え、退屈、変化を恐れる保守化。",
        "do": ["美味しい食事や良質な睡眠で心身を整える", "周囲への感謝を小さなプレゼントやねぎらいで表現する", "日々のルーティンを淡々と継続する"],
        "dont": ["暴飲暴食や怠惰な生活に流されること", "安定に胡座をかいて自己研鑽を怠ること", "重要でない雑務に忙殺されて本質を見失うこと"]
    },
    "玄武": {
        "title": "玄武（潜行・裏切り・情報流出）",
        "essence": "秘密裏の作戦、影の動き、盗難・漏洩リスク、詐欺、腹の探り合い。",
        "risk": "背信行為、パスワードや機密の漏洩、都合の悪い真実の隠蔽。",
        "do": ["機密情報や個人情報のセキュリティを最高レベルに引き上げる", "手の内をすべて明かさず、切り札を手元に残す", "相手の言動の『裏の意図』を慎重にプロファイリングする"],
        "dont": ["重要なパスワードや計画を安易に他人に明かすこと", "不正や嘘でその場をしのぐこと", "うますぎる投資や裏ルートの誘いに乗ること"]
    },
    "太陰": {
        "title": "太陰（深謀遠慮・密かな準備・女性の援助）",
        "essence": "水面下の着実な仕込み、洞察力、緻密なリサーチ、目立たぬ支援者。",
        "risk": "陰気、ネガティブ思考への沈み込み、密室での孤立。",
        "do": ["表に出る前の『下調べ』と『根回し』を完璧に仕上げる", "信頼できる少人数とだけ密に連携する", "内省を通じて自らの本心と向き合う"],
        "dont": ["準備不足のまま派手に公表・デビューすること", "裏で他人の悪口や陰湿な噂を流すこと", "一人で悩みを抱え込んで心を閉ざすこと"]
    },
    "天后": {
        "title": "天后（慈愛・包容力・柔軟な適応）",
        "essence": "感情のケア、内助の功、柔軟な立ち回り、傷ついたものの回復、水のような適応。",
        "risk": "感情に流されて優柔不断になること、境界線の曖昧さ。",
        "do": ["相手の心情に深く寄り添い、聞き役に徹する", "対立を避け、柳のように柔軟に受け流す", "自分自身のメンタルケアとリラクゼーションを大切にする"],
        "dont": ["冷酷な損得勘定だけで人を切り捨てること", "同情心から引き受けきれない重荷を背負い込むこと", "ヒステリックに感情を爆発させること"]
    }
}

KASHI_INTERPRETATION = {
    "元首課（上克下）": {
        "desc": "【元首の象】君が臣を統べ、理が情に勝つ正攻法の課式。",
        "advice": "堂々たる正義と論理で前進すべき時。リーダーシップを発揮し、規律正しく進めれば周囲は必ず従います。"
    },
    "重審課（下賊上）": {
        "desc": "【重審の象】下が上を突き上げ、内部からの変革を迫られる課式。",
        "advice": "現場の声や部下の不満、足元の小さなほころびを見逃してはなりません。上意下達ではなく、謙虚な傾聴が命運を分けます。"
    },
    "比用課（知一）": {
        "desc": "【知一の象】複数の選択肢から、自己の真の価値観（同調するもの）を選び取る課式。",
        "advice": "迷いが生じた時は、損得ではなく『自分自身の魂の純度』に合致する道を選んでください。二兎を追わず、一点集中が鉄則です。"
    },
    "渉害課": {
        "desc": "【渉害の象】深い大河を渡るように、困難やリスクを一つずつ乗り越える試練の課式。",
        "advice": "近道や裏ワザはありません。綿密な準備と覚悟を持って、目の前の障壁を一つずつ着実にクリアしていく粘り強さが勝利を呼びます。"
    },
    "遥克課（弾射）": {
        "desc": "【弾射の象】遠方・外部から矢が放たれるように、思いがけない外圧を受ける課式。",
        "advice": "直接の関係者以外からの飛び火やネットの反響に注意。守りを固め、不意の衝撃に対して冷静に対処してください。"
    },
    "遥克課（蒿矢）": {
        "desc": "【蒿矢の象】ヨモギの矢を放つように、こちらの働きかけが相手に届く課式。",
        "advice": "直接対決ではなく、遠回しの働きかけや第三者を介した間接的アプローチが功を奏します。"
    },
    "昴星課": {
        "desc": "【昴星の象】夜空の昴（すばる）を見上げるように、先行きが見えず手探りとなる課式。",
        "advice": "今は無理に結論を急ぐべきではありません。霧が晴れるのを待ち、静かに力を蓄える時期です。"
    },
    "伏吟課": {
        "desc": "【伏吟の象】天地が動かず重なり合い、身動きが取れない忍耐の課式。",
        "advice": "新規の着手や移転・転職は凶。今ある場所を徹底的に磨き上げ、内部のメンテナンスと足場固めに集中してください。"
    },
    "返吟課": {
        "desc": "【返吟の象】天地が激しく対立し、状況が二転三転して揺れ動く課式。",
        "advice": "一度白紙に戻ることを恐れないでください。過去の失敗から学び、まったく新しい視点でやり直すことで劇的な逆転が生まれます。"
    }
}

class RokujinAdvisor:
    def __init__(self, board: RokujinBoard, question: str = ""):
        self.board = board
        self.question = question or "現在の全般的な運勢・重大な意思決定について"

    def analyze_rulebased(self) -> Dict[str, Any]:
        c, z, m = self.board.sanduan
        tj_c = self.board.tianjiang_map[c]
        tj_z = self.board.tianjiang_map[z]
        tj_m = self.board.tianjiang_map[m]

        c_info = TIANJIANG_MODERN.get(tj_c, TIANJIANG_MODERN["貴人"])
        z_info = TIANJIANG_MODERN.get(tj_z, TIANJIANG_MODERN["青竜"])
        m_info = TIANJIANG_MODERN.get(tj_m, TIANJIANG_MODERN["六合"])

        kashi_info = KASHI_INTERPRETATION.get(self.board.kashi_type, {
            "desc": "【陰陽調和の象】天地の巡りに従い、時宜を得て進むべき課式。",
            "advice": "全体のバランスを見極め、偏りを排して中庸を保つことが成功への鍵となります。"
        })

        dos = []
        donts = []
        for action in c_info["do"]:
            if action not in dos:
                dos.append(action)
        for action in z_info["do"][:2]:
            if action not in dos:
                dos.append(action)

        for avoid in c_info["dont"]:
            if avoid not in donts:
                donts.append(avoid)
        for avoid in m_info["dont"][:2]:
            if avoid not in donts:
                donts.append(avoid)

        timeline = {
            "chuduan": {
                "step": "初伝（発用・現状）",
                "zhi": c,
                "tianjiang": tj_c,
                "summary": f"{c_info['title']}が臨む。事の発端・現在の火種。",
                "detail": f"いま目の前で起きている事象の本質は「{c_info['essence']}」にあります。{c_info['risk']}"
            },
            "zhongduan": {
                "step": "中伝（推移・プロセス）",
                "zhi": z,
                "tianjiang": tj_z,
                "summary": f"{z_info['title']}が臨む。中盤の展開・乗り越えるべき試練。",
                "detail": f"事態が進むにつれて「{z_info['essence']}」という局面を迎えます。ここで油断せず、{z_info['do'][0]}を意識して立ち回ることが重要です。"
            },
            "moduan": {
                "step": "末伝（帰結・結末）",
                "zhi": m,
                "tianjiang": tj_m,
                "summary": f"{m_info['title']}が臨む。最終的な着着点・成果。",
                "detail": f"最終的な結末は「{m_info['essence']}」へ収束します。{m_info['dont'][0]}を徹底して避けることで、望む果実を確実に収穫できます。"
            }
        }

        timing_advice = f"現在の時支は【{self.board.hour_zhi}】。貴人は【{'順行' if self.board.is_shun else '逆行'}】。"
        if self.board.is_shun:
            timing_advice += " 事態は素直に前進する流れにあります。躊躇せず波に乗り、早い段階でアクションを起こすのが吉です。"
        else:
            timing_advice += " 事態は水面下で回り道をする傾向があります。即答や拙速な決断を避け、裏付けを固めてから動くのが賢明です。"

        oracle = (
            f"『占事略决』曰く、天に十二辰あり、地に十二支あり、人に十二神あり。"
            f"いま課式は【{self.board.kashi_type}】を発用せり。事の兆しは初伝【{c}・{tj_c}】に萌し、末伝【{m}・{tj_m}】に極まる。"
            f"凶変を恐るることなかれ。善く時機を察し、虚妄を捨てて誠を執らば、神将みな汝を護らん。"
        )

        return {
            "question": self.question,
            "kashi_type": self.board.kashi_type,
            "kashi_desc": kashi_info["desc"],
            "kashi_advice": kashi_info["advice"],
            "timeline": timeline,
            "dos": dos[:3],
            "donts": donts[:3],
            "timing": timing_advice,
            "oracle": oracle
        }

    def generate_ai_enhanced_interpretation(self) -> Optional[str]:
        """Gemini API を用いて、ご相談内容に100%特化した深層現代風解釈を動的生成"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            b = self.board
            c, z, m = b.sanduan

            system_instruction = (
                "あなたは平安時代の天才陰陽師・安倍晴明の叡智と、現代の最高峰の意思決定コンサルタントの知性を併せ持つ鑑定士です。"
                "与えられた『占事略决』の六壬神課の厳密な計算結果（課式、天地盤、四課、三伝、十二天将）に基づき、"
                "相談者の問いに対して、曖昧さを排した極めて実践的で具体的、かつ現代的な言葉で解き明かしてください。"
                "専門用語は分かりやすく噛み砕き、特に【今やるべき事（DO）】3点と【絶対に避けるべき事（DON'T）】3点を明確に指示してください。"
            )

            prompt = f"""
【鑑定対象の相談内容】: {self.question}

【厳密な六壬神課・計算結果】:
- 鑑定日時: {b.dt_local.strftime('%Y-%m-%d %H:%M')} JST
- 日干支: {b.day_gan}{b.day_zhi}日
- 月将: {b.yueshang} ({YUESHANG_NAMES[b.yueshang]})
- 時支: {b.hour_zhi}時
- 貴人: {'昼貴人(旦)' if b.is_day else '夜貴人(暮)'}・{'順行' if b.is_shun else '逆行'}
- 発用課式: {b.kashi_type}
- 初伝（発用・現状）: {c} 【{b.tianjiang_map[c]}】 (地盤: {b.dipan_of_tian[c]})
- 中伝（推移・プロセス）: {z} 【{b.tianjiang_map[z]}】 (地盤: {b.dipan_of_tian[z]})
- 末伝（帰結・結末）: {m} 【{b.tianjiang_map[m]}】 (地盤: {b.dipan_of_tian[m]})
- 四課:
  一課: 上神={b.ke1[0]}({b.tianjiang_map[b.ke1[0]]}) / 下神={b.ke1[1]} (自己・顕在)
  二課: 上神={b.ke2[0]}({b.tianjiang_map[b.ke2[0]]}) / 下神={b.ke2[1]} (自己・潜在)
  三課: 上神={b.ke3[0]}({b.tianjiang_map[b.ke3[0]]}) / 下神={b.ke3[1]} (相手・現場)
  四課: 上神={b.ke4[0]}({b.tianjiang_map[b.ke4[0]]}) / 下神={b.ke4[1]} (相手・水面下)

以下のフォーマット（Markdown）で、相談者に深く突き刺さる実践的な回答を出力してください：
1. 盤面概況と大局診断（いまどんなエネルギーの中にいるのか、課式の意味）
2. 三伝のタイムライン（初伝＝現在・発端、中伝＝途中の試練・展開、末伝＝最終的な結果）
3. 【今すぐやるべき事 (DO)】3選（具体的アクション）
4. 【絶対に避けるべき事 (DON'T)】3選（地雷・禁忌）
5. 決断と勝負の時機（タイミング・方角）
6. 安倍晴明公の箴言（背中を押す守護メッセージ）
"""
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7
                )
            )
            return response.text
        except Exception:
            return None

    def format_report(self) -> str:
        # まずAI拡張解釈を試行
        ai_text = self.generate_ai_enhanced_interpretation()
        b = self.board

        if ai_text:
            report = []
            report.append(f"# 🔮 安倍晴明『占事略决』六壬神課 現代風特別鑑定 (AIオムニ解読)")
            report.append("")
            report.append(f"> **ご相談内容**: {self.question}")
            report.append(f"> **鑑定日時**: {b.dt_local.strftime('%Y年%m月%d日 %H:%M')} JST ｜ **日干支**: {b.day_gan}{b.day_zhi}日 ｜ **月将**: {b.yueshang} ({YUESHANG_NAMES[b.yueshang]}) ｜ **時支**: {b.hour_zhi}時")
            report.append("")
            report.append(ai_text.strip())
            report.append("")
            report.append("---")
            report.append("")
            report.append("### 【参考・厳密六壬盤面】")
            report.append("```text")
            report.append(b.format_board_ascii())
            report.append("```")
            return "\n".join(report)

        # フォールバック（ルールベース）
        data = self.analyze_rulebased()
        c, z, m = b.sanduan

        report = []
        report.append("# 🔮 安倍晴明『占事略决』六壬神課 現代風特別鑑定")
        report.append("")
        report.append(f"> **ご相談内容**: {data['question']}")
        report.append(f"> **鑑定日時**: {b.dt_local.strftime('%Y年%m月%d日 %H:%M')} JST ｜ **日干支**: {b.day_gan}{b.day_zhi}日 ｜ **月将**: {b.yueshang} ({YUESHANG_NAMES[b.yueshang]}) ｜ **時支**: {b.hour_zhi}時")
        report.append("")
        report.append("---")
        report.append("")
        report.append("## 1. 盤面概況と大局（マクロ診断）")
        report.append(f"**【発用課式】: {data['kashi_type']}**")
        report.append(f"- **大局の象**: {data['kashi_desc']}")
        report.append(f"- **戦略アドバイス**: {data['kashi_advice']}")
        report.append("")
        report.append("---")
        report.append("")
        report.append("## 2. 三伝リアル解読（タイムライン予測）")
        report.append("平安の秘法が暴く、事の「起こり」「推移」「結末」の3段階シナリオです。")
        report.append("")
        tl = data["timeline"]
        report.append(f"### ① 【現在・発端】初伝: {c}宮 × {tl['chuduan']['tianjiang']}")
        report.append(f"- **状況**: {tl['chuduan']['summary']}")
        report.append(f"- **深層解説**: {tl['chuduan']['detail']}")
        report.append("")
        report.append(f"### ② 【展開・中盤】中伝: {z}宮 × {tl['zhongduan']['tianjiang']}")
        report.append(f"- **状況**: {tl['zhongduan']['summary']}")
        report.append(f"- **深層解説**: {tl['zhongduan']['detail']}")
        report.append("")
        report.append(f"### ③ 【結末・落着】末伝: {m}宮 × {tl['moduan']['tianjiang']}")
        report.append(f"- **状況**: {tl['moduan']['summary']}")
        report.append(f"- **深層解説**: {tl['moduan']['detail']}")
        report.append("")
        report.append("---")
        report.append("")
        report.append("## 3. 【行動指針】今やるべき事 vs やるべきでない事")
        report.append("")
        report.append("### ✅ 【今すぐやるべき事 (DO)】")
        for i, do_item in enumerate(data["dos"], 1):
            report.append(f"{i}. **{do_item}**")
        report.append("")
        report.append("### ❌ 【絶対に避けるべき事 (DON'T)】")
        for i, dont_item in enumerate(data["donts"], 1):
            report.append(f"{i}. **{dont_item}**")
        report.append("")
        report.append("---")
        report.append("")
        report.append("## 4. 決断と勝負の時機（タイミング）")
        report.append(f"- {data['timing']}")
        report.append("")
        report.append("---")
        report.append("")
        report.append("## 5. 安倍晴明公からの神託（守護箴言）")
        report.append(f"> *{data['oracle']}*")
        report.append("")
        report.append("```text")
        report.append(b.format_board_ascii())
        report.append("```")
        return "\n".join(report)

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "現在の重要決断について"
    board = RokujinBoard()
    advisor = RokujinAdvisor(board, q)
    print(advisor.format_report())
