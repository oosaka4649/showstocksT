
import random
from typing import List, Tuple

def generate_red_balls() -> List[int]:
    """生成6个不重复的红球号码(1-33)"""
    return sorted(random.sample(range(1, 34), 6))

def generate_blue_ball() -> int:
    """生成1个蓝球号码(1-16)"""
    return random.randint(1, 16)

def calculate_odd_even_ratio(balls: List[int]) -> Tuple[int, int]:
    """计算奇偶比例"""
    odd_count = sum(1 for ball in balls if ball % 2 == 1)
    even_count = 6 - odd_count
    return odd_count, even_count

def calculate_sum(balls: List[int]) -> int:
    """计算红球和值"""
    return sum(balls)

def is_valid_combination(red_balls: List[int]) -> bool:
    """判断号码组合是否符合条件"""
    # 检查奇偶比
    odd_count, even_count = calculate_odd_even_ratio(red_balls)
    valid_ratios = {(3, 3), (4, 2), (2, 4)}
    if (odd_count, even_count) not in valid_ratios:
        return False
    
    # 检查和值范围
    total_sum = calculate_sum(red_balls)
    if not (70 <= total_sum <= 130):
        return False
    
    return True

def generate_valid_ssq() -> Tuple[List[int], int]:
    """生成符合筛选条件的双色球号码"""
    while True:
        red_balls = generate_red_balls()
        if is_valid_combination(red_balls):
            blue_ball = generate_blue_ball()
            return red_balls, blue_ball

def display_combination(red_balls: List[int], blue_ball: int):
    """显示号码组合详情"""
    odd_count, even_count = calculate_odd_even_ratio(red_balls)
    total_sum = calculate_sum(red_balls)
    
    print("=" * 50)
    print("双色球号码生成结果:")
    print(f"红球: {' '.join(f'{ball:02d}' for ball in red_balls)}")
    print(f"蓝球: {blue_ball:02d}")
    print(f"奇偶比: {odd_count}:{even_count}")
    print(f"和值: {total_sum}")
    print("=" * 50)

def count_common_red_balls(current_red: List[int], history_red: List[int]) -> int:
    """计算两个红球序列的相同球数量"""
    return len(set(current_red) & set(history_red))

def find_similar_historical_data(current_ticket: dict, min_matches: int = 3) -> List[dict]:
    """查找历史数据中红球至少有min_matches个相同的记录"""
    similar_records = []
    current_red = current_ticket["red"]
    
    for record in self.history_data:
        common_count = count_common_red_balls(current_red, record["red"])
        if common_count >= min_matches:
            similarity_info = record.copy()
            similarity_info["common_red_balls"] = sorted(list(set(current_red) & set(record["red"])))
            similarity_info["match_count"] = common_count
            similar_records.append(similarity_info)
            
    return similar_records
    
def deduplicate_and_analyze(tickets: List[dict]) -> List[dict]:
    """对生成的票进行去重并分析相似历史数据"""
    unique_tickets = []
    seen_combinations = set()
    
    for ticket in tickets:
        # 创建唯一的标识符用于去重
        combination_key = tuple(sorted(ticket["red"]) + [ticket["blue"]])
        if combination_key not in seen_combinations:
            seen_combinations.add(combination_key)
            ticket_copy = ticket.copy()
            # 查找相似历史数据
            similar_history = find_similar_historical_data(ticket, 3)
            ticket_copy["similar_history"] = similar_history
            unique_tickets.append(ticket_copy)
            
    return unique_tickets
    
def main():
    print("欢迎使用双色球选号器!")
    print("筛选条件:")
    print("- 奇偶比: 3:3, 4:2, 2:4")
    print("- 和值范围: 70-130")
    
    try:
        num_sets = int(input("请输入需要生成的注数(默认1注): ") or "1")
        print(f"\n正在生成{num_sets}注符合筛选条件的双色球号码...\n")
        
        for i in range(num_sets):
            red_balls, blue_ball = generate_valid_ssq()
            print(f"第{i+1}注:")
            display_combination(red_balls, blue_ball)
        # 去重并分析
        unique_tickets = deduplicate_and_analyze(generated_tickets)
        # 显示结果
        display_results(unique_tickets)

    except ValueError:
        print("输入无效，默认生成1注号码")
        red_balls, blue_ball = generate_valid_ssq()
        display_combination(red_balls, blue_ball)
    except KeyboardInterrupt:
        print("\n程序已退出")


def display_results(tickets: List[dict]):
    """显示分析结果"""
    print("=" * 60)
    print("双色球生成与历史数据分析报告")
    print("=" * 60)
    
    for i, ticket in enumerate(tickets, 1):
        print(f"\n第{i}注号码:")
        print(f"  日期: {ticket['date']}")
        print(f"  红球: {' '.join(f'{num:02d}' for num in ticket['red'])}")
        print(f"  蓝球: {ticket['blue']:02d}")
        
        similar_history = ticket.get("similar_history", [])
        if similar_history:
            print(f"  发现{len(similar_history)}条相似历史记录(红球≥3相同):")
            for j, record in enumerate(similar_history, 1):
                print(f"    [{j}] {record['date']}期:")
                print(f"        红球: {' '.join(f'{num:02d}' for num in record['red'])}")
                print(f"        蓝球: {record['blue']:02d}")
                print(f"        相同红球({record['match_count']}个): {' '.join(f'{num:02d}' for num in record['common_red_balls'])}")
        else:
            print("  无相似历史记录(红球≥3相同)")

if __name__ == "__main__":
    main()
