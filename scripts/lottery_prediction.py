#!/usr/bin/env python3
"""彩票预测号码生成 - 每次生成6组号码"""
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

def pick_mix(counter, n_hot, n_cold, num_range):
    """选号: n_hot个热号 + n_cold个冷号, 确保无重复"""
    # 按频率排序的所有号码
    all_by_freq = counter.most_common()
    
    # 热号候选: 前100个(最高频), 不超过num_range
    hot_pool = [n for n,c in all_by_freq[:100] if n <= num_range]
    # 冷号候选: 后100个(最低频), 不超过num_range
    cold_pool = [n for n,c in all_by_freq[-100:] if n <= num_range]
    
    random.shuffle(hot_pool)
    random.shuffle(cold_pool)
    
    # 取候选中不重复的
    selected = []
    for n in hot_pool[:n_hot*2]:
        if n not in selected:
            selected.append(n)
    hot_taken = len(selected)
    
    for n in cold_pool[:n_cold*2]:
        if n not in selected:
            selected.append(n)
    
    # 随机打乱并取前n_hot+n_cold个
    random.shuffle(selected)
    return selected[:n_hot + n_cold]

def fmt(nums):
    return " ".join("%02d" % n for n in sorted(nums))

def get_next_draw_date(lottery_type):
    today = date.today()
    if lottery_type == 'ssq':
        draw_days = [1, 3, 6]
    else:
        draw_days = [0, 2, 5]
    d = today
    for _ in range(8):
        if d.weekday() in draw_days:
            return d
        d += timedelta(days=1)
    return today

# ========== 加载统计 ==========
def load_stats():
    if os.path.exists(STAT_FILE):
        with open(STAT_FILE) as f:
            return json.load(f)
    return {'ssq': {'total_cost': 0, 'total_win': 0, 'draws': 0}, 'dlt': {'total_cost': 0, 'total_win': 0, 'draws': 0}}

stats = load_stats()
ssq_stats = stats['ssq']
dlt_stats = stats['dlt']

# ========== 生成6组双色球号码 ==========
ssq_sets = []
blue_hot_num = blue_c.most_common(1)[0][0]
blue_pool = list(range(1, 17))
random.shuffle(blue_pool)
ssq_blue = [blue_hot_num, blue_pool[0]]

for i in range(3):
    reds = pick_mix(red_c, 3, 3, 33)
    ssq_sets.append({'set': i+1, 'red': sorted(reds), 'blue': sorted(ssq_blue), 'type': '热号'})

for i in range(3):
    reds = pick_mix(red_c, 3, 3, 33)
    ssq_sets.append({'set': i+4, 'red': sorted(reds), 'blue': sorted(ssq_blue), 'type': '冷号'})

# ========== 生成6组大乐透号码 ==========
dlt_sets = []
back_hot_num = back_c.most_common(1)[0][0]
back_pool = list(range(1, 13))
random.shuffle(back_pool)
dlt_back = [back_hot_num, back_pool[0]]

for i in range(3):
    fronts = pick_mix(front_c, 3, 3, 35)
    dlt_sets.append({'set': i+1, 'front': sorted(fronts), 'back': sorted(dlt_back), 'type': '热号', '追加': True})

for i in range(3):
    fronts = pick_mix(front_c, 3, 3, 35)
    dlt_sets.append({'set': i+4, 'front': sorted(fronts), 'back': sorted(dlt_back), 'type': '冷号', '追加': True})

# ========== 保存预测 ==========
os.makedirs(f'{BASE}/福利彩票/预测数据', exist_ok=True)
os.makedirs(f'{BASE}/体育彩票/预测数据', exist_ok=True)

today = date.today().strftime('%Y-%m-%d')
ssq_draw = get_next_draw_date('ssq')
dlt_draw = get_next_draw_date('dlt')

ssq_data = {
    'generated_date': today, 'draw_date': ssq_draw.strftime('%Y-%m-%d'),
    'type': 'ssq', 'sets': ssq_sets,
    'cost': 6 * 2
}
dlt_data = {
    'generated_date': today, 'draw_date': dlt_draw.strftime('%Y-%m-%d'),
    'type': 'dlt', 'sets': dlt_sets,
    'cost': 6 * 3
}

with open(f'{BASE}/福利彩票/预测数据/{ssq_draw.strftime("%Y-%m-%d")}.json', 'w') as f:
    json.dump(ssq_data, f, ensure_ascii=False, indent=2)
with open(f'{BASE}/体育彩票/预测数据/{dlt_draw.strftime("%Y-%m-%d")}.json', 'w') as f:
    json.dump(dlt_data, f, ensure_ascii=False, indent=2)

# ========== 统计数据摘要 ==========
ssq_roi = (ssq_stats['total_win'] / ssq_stats['total_cost'] * 100) if ssq_stats['total_cost'] > 0 else 0
dlt_roi = (dlt_stats['total_win'] / dlt_stats['total_cost'] * 100) if dlt_stats['total_cost'] > 0 else 0

# ========== 输出消息 ==========
msg = []
msg.append(f"🎰 彩票预测号码 ({today} 生成)")
msg.append(f"双色球 {ssq_draw.strftime('%m-%d(%a)')} 21:15 | 大乐透 {dlt_draw.strftime('%m-%d(%a)')} 21:25")
msg.append("")
msg.append(f"📊 累计统计")
msg.append(f"双色球: 投入{ssq_stats['total_cost']}元 中奖{ssq_stats['total_win']}元 收益{ssq_stats['total_win']-ssq_stats['total_cost']:+d}元 ({ssq_roi:.1f}%) {ssq_stats['draws']}期")
msg.append(f"大乐透: 投入{dlt_stats['total_cost']}元 中奖{dlt_stats['total_win']}元 收益{dlt_stats['total_win']-dlt_stats['total_cost']:+d}元 ({dlt_roi:.1f}%) {dlt_stats['draws']}期")
msg.append("")
msg.append(f"【双色球】6注, 本期投入{ssq_data['cost']}元")
for s in ssq_sets:
    label = f"热{s['set']}" if s['type'] == '热号' else f"冷{s['set']}"
    msg.append(f"  [{label}] 红球: {fmt(s['red'])} | 蓝球: {' '.join('%02d' % n for n in s['blue'])}")

msg.append("")
msg.append(f"【大乐透】6注(追加), 本期投入{dlt_data['cost']}元")
for s in dlt_sets:
    label = f"热{s['set']}" if s['type'] == '热号' else f"冷{s['set']}"
    msg.append(f"  [{label}] 前区: {fmt(s['front'])} | 后区: {' '.join('%02d' % n for n in s['back'])}")

msg.append("")
msg.append("💡 理性购彩，娱乐为主")

print("\n".join(msg))
