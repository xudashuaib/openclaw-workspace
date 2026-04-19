#!/usr/bin/env python3
"""彩票开奖结果检查 - 更新统计数据"""
from datetime import date
import json
import os
from glob import glob

SSQ_FILE = '/tmp/ssq_17500.txt'
DLT_FILE = '/tmp/dlt_desc.txt'
BASE = '/root/.openclaw/workspace/lottery'
STAT_FILE = f'{BASE}/stats.json'

def get_latest_draw(lottery_file):
    with open(lottery_file, 'r') as f:
        for line in f:
            p = line.strip().split()
            if len(p) >= 9:
                yield p

def get_latest_ssq():
    latest = list(get_latest_draw(SSQ_FILE))[0]
    return {
        'period': latest[0], 'date': latest[1],
        'red': [int(latest[i]) for i in [2,3,4,5,6,7]],
        'blue': int(latest[8])
    }

def get_latest_dlt():
    latest = list(get_latest_draw(DLT_FILE))[0]
    return {
        'period': latest[0], 'date': latest[1],
        'front': [int(latest[i]) for i in [2,3,4,5,6]],
        'back': [int(latest[7]), int(latest[8])]
    }

def check_ssq_set(pred_set, draw):
    """检查一组预测的奖金"""
    red_match = len(set(pred_set['red']) & set(draw['red']))
    blue_hit = 1 if pred_set['blue'][0] == draw['blue'] or pred_set['blue'][1] == draw['blue'] else 0
    
    if red_match == 6 and blue_hit:
        return ('一等奖', 0)
    elif red_match == 6:
        return ('二等奖', 0)
    elif red_match == 5 and blue_hit:
        return ('三等奖', 3000)
    elif red_match == 5 or (red_match == 4 and blue_hit):
        return ('四等奖', 200)
    elif red_match == 4 or (red_match == 3 and blue_hit):
        return ('五等奖', 10)
    elif blue_hit:
        return ('六等奖', 5)
    else:
        return ('未中奖', 0)

def check_dlt_set(pred_set, draw):
    """检查一组大乐透预测的奖金（含追加）"""
    front_match = len(set(pred_set['front']) & set(draw['front']))
    back_match = len(set(pred_set['back']) & set(draw['back']))
    
    # 基本投注奖金
    if front_match == 5 and back_match == 2:
        return ('一等奖', 0, 0)  # 浮动奖
    elif front_match == 5 and back_match == 1:
        return ('二等奖', 0, 0)  # 浮动奖
    elif front_match == 5 or (front_match == 4 and back_match == 2):
        return ('三等奖', 5000, 5000 * 0.8)  # 追加多80%
    elif front_match == 4 or (front_match == 3 and back_match == 2):
        return ('四等奖', 300, 300 * 0.8)
    elif front_match == 4 or (front_match == 3 and back_match == 1) or (front_match == 2 and back_match == 2):
        return ('五等奖', 150, 150 * 0.8)
    elif front_match == 3 or (front_match == 2 and back_match == 1) or (front_match == 1 and back_match == 2) or back_match == 2:
        return ('七等奖', 5, 5)  # 追加无效
    else:
        return ('未中奖', 0, 0)

def load_stats():
    if os.path.exists(STAT_FILE):
        with open(STAT_FILE) as f:
            return json.load(f)
    return {
        'ssq': {'total_cost': 0, 'total_win': 0, 'draws': 0},
        'dlt': {'total_cost': 0, 'total_win': 0, 'draws': 0}
    }

def save_stats(stats):
    with open(STAT_FILE, 'w') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def fmt(nums):
    return " ".join("%02d" % n for n in sorted(nums))

def main():
    today = date.today().strftime('%Y-%m-%d')
    
    # 找今日开奖的预测文件
    ssq_files = glob(f'{BASE}/福利彩票/预测数据/*.json')
    dlt_files = glob(f'{BASE}/体育彩票/预测数据/*.json')
    
    stats = load_stats()
    results = []
    
    for f in ssq_files:
        with open(f) as fh:
            pred = json.load(fh)
        if pred.get('draw_date') == today:
            draw = get_latest_ssq()
            draw_info = {
                'period': draw['period'], 'date': draw['date'],
                'numbers': fmt(draw['red']) + ' + ' + '%02d' % draw['blue'],
                'red': draw['red'], 'blue': draw['blue']
            }
            result_sets = []
            total_win = 0
            for i, s in enumerate(pred['sets']):
                prize, amount = check_ssq_set(s, draw)
                result_sets.append({
                    'set': i+1, 'type': s['type'],
                    'red': s['red'], 'blue': s['blue'],
                    'prize': prize, 'amount': amount
                })
                total_win += amount
            
            stats['ssq']['total_cost'] += pred.get('cost', 12)
            stats['ssq']['total_win'] += total_win
            stats['ssq']['draws'] += 1
            
            results.append(('ssq', {
                'draw': draw_info,
                'sets': result_sets,
                'cost': pred.get('cost', 12),
                'total_win': total_win
            }))
    
    for f in dlt_files:
        with open(f) as fh:
            pred = json.load(fh)
        if pred.get('draw_date') == today:
            draw = get_latest_dlt()
            draw_info = {
                'period': draw['period'], 'date': draw['date'],
                'numbers': fmt(draw['front']) + ' + ' + ' '.join('%02d' % n for n in draw['back']),
                'front': draw['front'], 'back': draw['back']
            }
            result_sets = []
            total_win = 0
            total_win_add = 0
            for i, s in enumerate(pred['sets']):
                prize, amount, amount_add = check_dlt_set(s, draw)
                result_sets.append({
                    'set': i+1, 'type': s['type'],
                    'front': s['front'], 'back': s['back'],
                    'prize': prize, 'amount': amount + amount_add
                })
                total_win += amount + amount_add
            
            stats['dlt']['total_cost'] += pred.get('cost', 18)
            stats['dlt']['total_win'] += total_win
            stats['dlt']['draws'] += 1
            
            results.append(('dlt', {
                'draw': draw_info,
                'sets': result_sets,
                'cost': pred.get('cost', 18),
                'total_win': total_win
            }))
    
    save_stats(stats)
    
    if not results:
        print("今日无开奖，无结果可查")
        return
    
    # 输出
    ssq_stats = stats['ssq']
    dlt_stats = stats['dlt']
    ssq_roi = (ssq_stats['total_win'] / ssq_stats['total_cost'] * 100) if ssq_stats['total_cost'] > 0 else 0
    dlt_roi = (dlt_stats['total_win'] / dlt_stats['total_cost'] * 100) if dlt_stats['total_cost'] > 0 else 0
    
    print(f"🎰 彩票开奖结果 {today}")
    print(f"\n📊 累计统计")
    print(f"双色球: 投入{ssq_stats['total_cost']}元 中奖{ssq_stats['total_win']}元 收益{ssq_stats['total_win']-ssq_stats['total_cost']:+d}元 ({ssq_roi:.1f}%) {ssq_stats['draws']}期")
    print(f"大乐透: 投入{dlt_stats['total_cost']}元 中奖{dlt_stats['total_win']}元 收益{dlt_stats['total_win']-dlt_stats['total_cost']:+d}元 ({dlt_roi:.1f}%) {dlt_stats['draws']}期")
    print()
    
    for kind, r in results:
        d = r['draw']
        if kind == 'ssq':
            print(f"【双色球】{d['period']}期 {d['date']}")
            print(f"开奖: {d['numbers']}")
            for s in r['sets']:
                label = f"热{s['set']}" if s['type'] == '热号' else f"冷{s['set']}"
                print(f"  [{label}] 预测: {fmt(s['red'])} + {' '.join('%02d' % n for n in s['blue'])} | {s['prize']} {'+' + str(s['amount']) + '元' if s['amount'] > 0 else ''}")
            print(f"本期投入: {r['cost']}元 | 中奖: {r['total_win']}元")
        else:
            print(f"【大乐透】{d['period']}期 {d['date']}")
            print(f"开奖: {d['numbers']}")
            for s in r['sets']:
                label = f"热{s['set']}" if s['type'] == '热号' else f"冷{s['set']}"
                print(f"  [{label}] 预测: {fmt(s['front'])} + {' '.join('%02d' % n for n in s['back'])} | {s['prize']} {'+' + str(s['amount']) + '元' if s['amount'] > 0 else ''}")
            print(f"本期投入: {r['cost']}元 | 中奖: {r['total_win']}元")
        print()
    
    # 保存结果记录
    os.makedirs(f'{BASE}/福利彩票/结果记录', exist_ok=True)
    os.makedirs(f'{BASE}/体育彩票/结果记录', exist_ok=True)
    for kind, r in results:
        record = {
            'date': today,
            'draw': r['draw'],
            'sets': r['sets'],
            'cost': r['cost'],
            'total_win': r['total_win'],
            'stats': stats[kind if kind == 'ssq' else 'dlt']
        }
        if kind == 'ssq':
            with open(f'{BASE}/福利彩票/结果记录/{today}.json', 'w') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
        else:
            with open(f'{BASE}/体育彩票/结果记录/{today}.json', 'w') as f:
                json.dump(record, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
