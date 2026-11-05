# TUGUMIv6 ジャンル別サウンドデザイン＆インストゥルメントリファレンス

## 1. 概要
GM (General MIDI) 音色マップ規格、NumPyシンセサイザー波形特性、およびBPM/グルーヴ設定の対応表です。

---

## 2. ジャンル別プリセット一覧

### 1. Lo-Fi Hip Hop (チルホップ)
- **BPM**: 75 - 88 (推奨: 82)
- **Key**: Eb Major, F Minor, Bb Major
- **コード進行**: Just The Two of Us (丸サ進行)
- **Lead 音色**: Electric Piano 1 (GM 4: Rhodes風)
- **Pad 音色**: Pad 2 Warm (GM 89)
- **Bass 音色**: Electric Bass (Finger) (GM 33)
- **ドラム**: キック（低域ブースト）、スネア（乾いたクラップ）、ハット（スウィング20%）
- **シンセ波形**: Sine + FM変調 (FMキャリア440Hz / モジュレータ220Hz)

### 2. Cyberpunk Synthwave (レトロフューチャー)
- **BPM**: 116 - 130 (推奨: 120)
- **Key**: A Minor, D Minor
- **コード進行**: Cyber Synth (i - VI - III - VII)
- **Lead 音色**: Lead 1 Square / Lead 2 Sawtooth (GM 80/81)
- **Pad 音色**: Pad 1 New Age (GM 88)
- **Bass 音色**: Synth Bass 1 (GM 38)
- **ドラム**: 80年代リバーブスネア、タイトな4つ打ちキック
- **シンセ波形**: Sawtooth (ノコギリ波) + ADSRシャープアタック

### 3. J-POP / アニメアンセム
- **BPM**: 128 - 145 (推奨: 134)
- **Key**: F Major, G Major, C Major
- **コード進行**: Royal Road (王道進行 IV - V - iii - vi)
- **Lead 音色**: Lead 2 Sawtooth / Trumpet / Bright Acoustic Piano (GM 81/56/1)
- **Pad 音色**: String Ensemble 1 (GM 49)
- **Bass 音色**: Electric Bass (Pick) (GM 34)
- **ドラム**: 疾走感のある8ビート、16分オープンハイハット

### 4. Ambient & Meditation (環境音楽・瞑想)
- **BPM**: 60 - 72 (推奨: 65)
- **Key**: C Major, D Lydian
- **コード進行**: Ambient Chill (Imaj7 - IVmaj7)
- **Lead 音色**: Vibraphone / Music Box (GM 11/10)
- **Pad 音色**: Pad 2 Warm / Choir Aahs (GM 89/52)
- **Bass 音色**: Acoustic Bass (GM 32)
- **ドラム**: ドラムレス、あるいは超微弱なブラシ・ベル音

---

## 3. General MIDI 音色クイックインデックス
- **Piano**: 0=Acoustic Grand, 1=Bright Acoustic, 4=Electric Piano 1 (Rhodes), 5=Electric Piano 2 (DX7)
- **Strings**: 40=Violin, 48=String Ensemble 1, 49=String Ensemble 2, 50=SynthStrings 1
- **Bass**: 32=Acoustic, 33=Electric Finger, 34=Electric Pick, 35=Fretless, 38=Synth Bass 1, 39=Synth Bass 2
- **Lead**: 80=Square, 81=Sawtooth, 84=Charang, 87=Bass + Lead
- **Pad**: 88=New Age, 89=Warm, 90=Polysynth, 92=Bow, 94=Halo, 95=Sweep
