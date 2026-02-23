import json
import re

def parse_sql_insert(line):
    # 匹配INSERT语句中的VALUES部分
    match = re.search(r"VALUES\s*\((.*?)\)", line)
    if not match:
        return None
    values_str = match.group(1)
    # 分割值，注意字符串和数字
    values = []
    current = ""
    in_string = False
    for char in values_str:
        if char == "'" and not in_string:
            in_string = True
        elif char == "'" and in_string:
            in_string = False
        elif char == ',' and not in_string:
            values.append(current.strip())
            current = ""
            continue
        current += char
    values.append(current.strip())
    # 移除引号
    values = [v.strip("'") for v in values]
    return values

def convert_to_json_entry(values):
    if len(values) < 10:
        return None
    qihao = values[0]
    date = values[1]
    weekday = values[2]
    red_balls = [f"{int(v):02d}" for v in values[3:9]]
    blue_ball = f"{int(values[9]):02d}"

    all_jinge = values[11]  # 销售额
    all_cishu = values[12]  # 奖池
    one_cishu = values[13]  # 一等奖注数
    one_jinge = values[14]  # 一等奖金额
    two_cishu = values[15]  # 二等奖注数
    two_jinge = values[16]  # 二等奖金额

    # 其他字段在SQL中都是0
    entry = {
        "期号": qihao,
        "开奖日期": f"{date}({weekday})",
        "开奖号码": {
            "红球": red_balls,
            "蓝球": blue_ball
        },
        "一等奖注数": one_cishu,
        "一等奖金额": one_jinge,
        "二等奖注数": two_cishu,
        "二等奖金额": two_jinge,
        "销售额": all_jinge,
        "奖池金额": all_cishu,
        "开奖公告": ""
    }
    return entry

def main():
    # 读取现有的JSON
    with open('E:\mygithub\showstocksT\cvs_search_app\duball\lottery_results.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 读取SQL文件
    with open('E:\mygithub\showstocksT\cvs_search_app\duball\caipiao_log.sql', 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # 解析每行INSERT
    lines = sql_content.strip().split('\n')
    new_entries = []
    for line in lines:
        if line.startswith('INSERT'):
            values = parse_sql_insert(line)
            if values:
                entry = convert_to_json_entry(values)
                if entry:
                    has_duplicate = False
                    for existing_entry in data:
                        if existing_entry['期号'] == entry['期号']:
                            print(f"期号 {entry['期号']} 已存在，跳过")
                            has_duplicate = True
                            break
                    if not has_duplicate:
                        new_entries.append(entry)

    # 合并数据，假设新数据是旧的，添加到末尾或开头？
    # 由于期号是2003年的，而现有是2026年的，可能添加到开头或末尾。
    # 为了保持顺序，可能添加到开头（早期数据）
    data.extend(new_entries)

    # 保存回JSON
    with open('lottery_results.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()