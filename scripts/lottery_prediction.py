#!/usr/bin/env python3
"""彩票预测号码生成 - 每次生成6组号码
- 3组全热号 + 3组全冷号
- 热号组: 全部使用历史高频号码(红球/前区 + 蓝球/后区)
- 冷号组: 全部使用历史低频号码(红球/前区 + 蓝球/后区)
"""
import random
from collections import Counter
import json
import os
from datetime import date, timedelta

SSQ_FILE = '/tmp/ssq_17500.txt'
DLT_FILE = '/tmp/dlt_desc.txt'
BASE = '/root/.openclaw/workspace/lottery'
STAT_FILE = f'{BASE}/stats.json'

# ========== 加载数据 ==========
ssq_red, ssq_blue = [], []
with open(SSQ_FILE, 'r') as f:
    for line in f:
        p = line.strip().split()
        if len(p) >= 9:
            for i in [2,3,4,5,6,7]:
                ssq_red.append(int(p[i]))
            ssq_blue.append(int(p[8]))

dlt_front, dlt_back = [], []
with open(DLT_FILE, 'r') as f:
    for line in f:
        p = line.strip().split()
        if len(p) >= 9:
            for i in [2,3,4,5,6]:
                dlt_front.append(int(p[i]))
            dlt_back += [int(p[7]), int(p[8])]

red_c = Counter(ssq_red)
blue_c = Counter(ssq_blue)
front_c = Counter(dlt_front)
back_c = Counter(dlt_back)

def get_hot(counter, num_range, n):
    pool = [n for n,c in counter.most_common(300) if n <= num_range]
    pool = list(dict.fromkeys(pool))
    random.shuffle(pool)
    return pool[:n]

def get_cold(counter, num_range, n):
    pool = [n for n,c in counter.most_common()[-300:] if n <= num_range]
    pool = list(dict.fromkeys(pool))
    random.shuffle(pool)
    return pool[:n]

def fmt(nums):
    return " ".join("%02d" % n for n in sorted(nums))

def get_next_draw_date(lottery_type):
    today = date.today()
    draw_days = [1, 3, 6] if lottery_type == 'ssq' else [0, 2, 5]
    d = today
    for _ in range(8):
        if d.weekday() in draw_days:
            return d
        d += timedelta(days=1)
    return today

def load_stats():
    if os.path.exists(STAT_FILE):
        with open(STAT_FILE) as f:
            return json.load(f)
    return {'ssq': {'total_cost': 0, 'total_win': 0, 'draws': 0}, 'dlt': {'total_cost': 0, 'total_win': 0, 'draws': 0}}

# ========== 生成双色球 ==========
# 热号组: 6个热红球 + 2个热蓝球
# 冷号组: 6个冷红球 + 2个冷蓝球
ssq_sets = []

hot_blue = get_hot(blue_c, 16, 2)
cold_blue = get_cold(blue_c, 16, 2)

for i in range(3):
    reds = get_hot(red_c, 33, 6)
    ssq_sets.append({'set': i+1, 'red': sorted(reds), 'blue': sorted(hot_blue), 'type': '热号'})

for i in range(3):
    reds = get_cold(red_c, 33, 6)
    ssq_sets.append({'set': i+4, 'red': sorted(reds), 'blue': sorted(cold_blue), 'type': '冷号'})

# ========== 生成大乐透 ==========
# 热号组: 5个热前区 + 2个热后区
# 冷号组: 5个冷前区 + 2个冷后区
dlt_sets = []

hot_back = get_hot(back_c, 12, 2)
cold_back = get_cold(back_c, 12, 2)

for i in range(3):
    fronts = get_hot(front_c, 35, 5)
    dlt_sets.append({'set': i+1, 'front': sorted(fronts), 'back': sorted(hot_back), 'type': '热号', '追加': True})

for i in range(3):
    fronts = get_cold(front_c, 35, 5)
    dlt_sets.append({'set': i+4, 'front': sorted(fronts), 'back': sorted(cold_back), 'type': '冷号', '追加': True})

# ========== 保存预测 ==========
os.makedirs(f'{BASE}/福利彩票/预测数据', exist_ok=True)
os.makedirs(f'{BASE}/体育彩票/预测数据', exist_ok=True)

today = date.today().strftime('%Y-%m-%d')
ssq_draw = get_next_draw_date('ssq')
dlt_draw = get_next_draw_date('dlt')

ssq_data = {
    'generated_date': today, 'draw_date': ssq_draw.strftime('%Y-%m-%d'),
    'type': 'ssq', 'sets': ssq_sets, 'cost': 6 * 2
}
dlt_data = {
    'generated_date': today, 'draw_date': dlt_draw.strftime('%Y-%m-%d'),
    'type': 'dlt', 'sets': dlt_sets, 'cost': 6 * 3
}

with open(f'{BASE}/福利彩票/预测数据/{ssq_draw.strftime("%Y-%m-%d")}.json', 'w') as f:
    json.dump(ssq_data, f, ensure_ascii=False, indent=2)
with open(f'{BASE}/体育彩票/预测数据/{dlt_draw.strftime("%Y-%m-%d")}.json', 'w') as f:
    json.dump(dlt_data, f, ensure_ascii=False, indent=2)

# ========== 输出 ==========
stats = load_stats()
ssq_s = stats['ssq']
dlt_s = stats['dlt']
ssq_roi = (ssq_s['total_win'] / ssq_s['total_cost'] * 100) if ssq_s['total_cost'] > 0 else 0
dlt_roi = (dlt_s['total_win'] / dlt_s['total_cost'] * 100) if dlt_s['total_cost'] > 0 else 0

msg = []
msg.append(f"🎰 彩票预测号码 ({today} 生成)")
msg.append(f"双色球 {ssq_draw.strftime('%m-%d(%a)')} 21:15 | 大乐透 {dlt_draw.strftime('%m-%d(%a)')} 21:25")
msg.append("")
msg.append(f"📊 累计统计")
msg.append(f"双色球: 投入{ssq_s['total_cost']}元 中奖{ssq_s['total_win']}元 收益{ssq_s['total_win']-ssq_s['total_cost']:+d}元 ({ssq_roi:.1f}%) {ssq_s['draws']}期")
msg.append(f"大乐透: 投入{dlt_s['total_cost']}元 中奖{dlt_s['total_win']}元 收益{dlt_s['total_win']-dlt_s['total_cost']:+d}元 ({dlt_roi:.1f}%) {dlt_s['draws']}期")
msg.append("")
msg.append(f"【双色球】6注, 本期投入{ssq_data['cost']}元")
for s in ssq_sets:
    label = f"热{s['set']}" if s['type'] == '热号' else f"冷{s['set']}"
    note = "【全热号】" if s['type'] == '热号' else "【全冷号】"
    blue_note = "热蓝" if s['type'] == '热号' else "冷蓝"
    msg.append(f"  [{label}] {note} 红球: {fmt(s['red'])} | 蓝球: {fmt(s['blue'])}({blue_note})")

msg.append("")
msg.append(f"【大乐透】6注(追加), 本期投入{dlt_data['cost']}元")
for s in dlt_sets:
    label = f"热{s['set']}" if s['type'] == '热号' else f"冷{s['set']}"
    note = "【全热号】" if s['type'] == '热号' else "【全冷号】"
    back_note = "热后区" if s['type'] == '热号' else "冷后区"
    msg.append(f"  [{label}] {note} 前区: {fmt(s['front'])} | 后区: {fmt(s['back'])}({back_note})")

msg.append("")
msg.append("💡 理性购彩，娱乐为主")

print("\n".join(msg))
