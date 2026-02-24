
import random
from typing import List, Tuple, Set
from datetime import datetime

class SSQAnalyzer:
    def __init__(self):
        # 初始化历史数据（模拟数据）
        self.history_data = self._generate_sample_history()
    
    def _generate_sample_history(self) -> List[dict]:
        """生成示例历史数据"""
        sample_data = [
            {"date": "2026-01-01", "red": [1, 5, 12, 18, 25, 30], "blue": 8},
            {"date": "2026-01-03", "red": [3, 7, 15, 20, 22, 33], "blue": 12},
            {"date": "2026-01-05", "red": [2, 8, 14, 19, 26, 31], "blue": 5},
            {"date": "2026-01-08", "red": [6, 11, 13, 21, 28, 32], "blue": 9},
            {"date": "2026-01-10", "red": [4, 9, 16, 23, 27, 29], "blue": 14},
            {"date": "2026-01-12", "red": [1, 7, 17, 24, 26, 30], "blue": 3},
            {"date": "2026-01-15", "red": [5, 10, 18, 22, 25, 33], "blue": 11},
            {"date": "2026-01-17", "red": [2, 12, 19, 21, 27, 32], "blue": 6},
            {"date": "2026-01-19", "red": [8, 13, 15, 20, 28, 31], "blue": 16},
            {"date": "2026-01-22", "red": [3, 9, 14, 23, 29, 30], "blue": 1}
        ]
        return sample_data
    
    def generate_ssq(self) -> dict:
        """生成一组双色球号码"""
        red_balls = sorted(random.sample(range(1, 34), 6))
        blue_ball = random.randint(1, 16)
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "red": red_balls,
            "blue": blue_ball
        }
    
    def count_common_red_balls(self, current_red: List[int], history_red: List[int]) -> int:
        """计算两个红球序列的相同球数量"""
        return len(set(current_red) & set(history_red))
    
    def find_similar_historical_data(self, current_ticket: dict, min_matches: int = 3) -> List[dict]:
        """查找历史数据中红球至少有min_matches个相同的记录"""
        similar_records = []
        current_red = current_ticket["red"]
        
        for record in self.history_data:
            common_count = self.count_common_red_balls(current_red, record["red"])
            if common_count >= min_matches:
                similarity_info = record.copy()
                similarity_info["common_red_balls"] = sorted(list(set(current_red) & set(record["red"])))
                similarity_info["match_count"] = common_count
                similar_records.append(similarity_info)
                
        return similar_records
    
    def deduplicate_and_analyze(self, tickets: List[dict]) -> List[dict]:
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
                similar_history = self.find_similar_historical_data(ticket, 3)
                ticket_copy["similar_history"] = similar_history
                unique_tickets.append(ticket_copy)
                
        return unique_tickets
    
    def display_results(self, tickets: List[dict]):
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

def main():
    analyzer = SSQAnalyzer()
    
    # 生成多组双色球号码(包含一些重复号码用于测试去重功能)
    generated_tickets = []
    for _ in range(8):
        ticket = analyzer.generate_ssq()
        generated_tickets.append(ticket)
    
    # 故意添加一些重复号码测试去重功能
    if generated_tickets:
        duplicate_ticket = generated_tickets[0].copy()
        duplicate_ticket["date"] = datetime.now().strftime("%Y-%m-%d")
        generated_tickets.append(duplicate_ticket)
    
    print(f"总共生成{len(generated_tickets)}注号码(包含1个重复)")
    
    # 去重并分析
    unique_tickets = analyzer.deduplicate_and_analyze(generated_tickets)
    
    print(f"去重后剩余{len(unique_tickets)}注唯一号码")
    
    # 显示结果
    analyzer.display_results(unique_tickets)

if __name__ == "__main__":
    main()
