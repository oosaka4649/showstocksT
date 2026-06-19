import numpy as np
import time
import unicodedata

class BaseModel:
    """基础模型类，提供通用工具方法供子类复用。"""
    def _rolling_window(self, a, window):
        """利用 NumPy stride 生成滚动窗口视图（不复制内存）。"""
        a = np.array(a)
        shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
        strides = a.strides + (a.strides[-1],)
        return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

class VP_QuantRunner_BaseModel:
    
    def split_data(self, data, start_date=None):
        category_data = []
        values = []
        volumes = []
        closes = []

        volumes_macd = [] # 这个是为了计算 macd 用的，输入为量值，看看能不能生成一个和 macd 类似的曲线，观察成交量和 macd 的关系

        '''
            date         开        收        最低       最高       量
        ["2004-01-02", 10452.74, 10409.85, 10367.41, 10554.96, 168890000],
        data 结构
        
        '''

        for i, tick in enumerate(data):
            date_str = tick[0]
            if start_date and date_str < start_date:
                continue
            category_data.append(tick[0]) # 日期
            values.append(tick) # 全部内容
            closes.append(tick[2]) # 收盘价
            # 元代码 是 tick 4 错了，应该是 tick 5 因为 4是 最高价，5才是量
            volumes_macd.append(tick[5]) # 这个是为了计算 macd 用的，输入为量值，看看能不能生成一个和 macd 类似的曲线，观察成交量和 macd 的关系

            volumes.append([i, tick[5], 1 if tick[1] > tick[2] else -1])  # i 是序号 从 0 开始，如果 开始大于收盘 1 ，反之 -1 估计是标 量线颜色用 红 绿
        return {"categoryData": category_data, "values": values, "volumes": volumes, "closes": closes, "volumes_macd": volumes_macd}
        
    def load_stock_data(self, stock_data):
        dates, prices, volumes = stock_data["categoryData"], stock_data["closes"], stock_data["volumes_macd"]  # 注意这里我们用的是 volumes_macd 来观察成交量和 macd 的关系
        return dates, prices, volumes
    
    def _split_data_add_snapshot_data(self, data, snapshot_data, start_date=None, add_data_flg=False):
        time_str = time.strftime('%Y-%m-%d')
        category_data = []
        closes = []
        volumes = []

        all_data = self.split_data(data, start_date=start_date)
        category_data = all_data["categoryData"]
        closes = all_data["closes"]
        volumes = all_data["volumes_macd"]
        _snapshot_data = snapshot_data  # 获取市场快照数据
        #print(f"获取到的市场快照数据: {_snapshot_data}")
        # 将快照数据添加到 values 中，日期使用 "snapshot" 作为标识
        #snapshot_tick = ["snapshot", _snapshot_data["open"], _snapshot_data["close"], _snapshot_data["low"], _snapshot_data["high"], _snapshot_data["volume"]]
        if time_str > category_data[-1] and add_data_flg:
            category_data.append(time_str)  # 添加快照日期 
            closes.append(_snapshot_data["close"])  # 添加快照的收盘价
            volumes.append(_snapshot_data["volume"])  # 添加快照的成交量到 macd 数据中
        
        return {"categoryData": category_data, "closes": closes, "volumes_macd": volumes}    
    
    def info2file(self, quant_result_file = None, quant_result_info = None):
        if quant_result_file is None:
            quant_result_file = 'ai_quant.txt'
        if quant_result_info is None:
            return
        # 打开目标文件，后缀名为CSV
        target_file = open(quant_result_file, 'a', encoding='utf-8')
        target_file.write('\n')  # 换行
        target_file.write(quant_result_info)
        target_file.close()

    def side_by_side_print_result(self, left_text, right_text, left_width=None, sep=' | '):
        left_lines = left_text.splitlines()
        right_lines = right_text.splitlines()
        n = max(len(left_lines), len(right_lines))
        if left_width is None:
            left_width = max((len(l) for l in left_lines), default=0) + 2
            left_width = min(left_width, 120)
        for i in range(n):
            L = left_lines[i] if i < len(left_lines) else ''
            R = right_lines[i] if i < len(right_lines) else ''
            self.info2file(quant_result_info=L.ljust(left_width) + sep + R)

    def _display_width(self, text):
        """计算文本在等宽终端中的显示宽度，中文、全角字符视为 2 个宽度。"""
        width = 0
        for ch in text:
            if unicodedata.east_asian_width(ch) in ('F', 'W'):
                width += 2
            else:
                width += 1
        return width


    def _pad_text(self, text, width):
        """按显示宽度补齐文本。"""
        padding = width - self._display_width(text)
        return text + ' ' * padding if padding > 0 else text


    def multi_column_print(self, *texts, col_widths=None, sep=' | '):
        """
        将多段多行文本并排打印到控制台（支持 3 列及以上任意多列）
        
        :param texts: 变长参数，传入多个多行字符串
        :param col_widths: 列表或元组，手动指定每列的宽度。默认 None 则自动计算
        :param sep: 列与列之间的分隔符
        """
        if not texts:
            return

        # 1. 将每段文本按行拆分，形成二维列表：columns_lines[列号][行号]
        columns_lines = [text.splitlines() for text in texts]
        num_columns = len(columns_lines)
        
        # 2. 计算最大行数，决定循环打印多少轮
        max_lines = max(len(lines) for lines in columns_lines)
        
        # 3. 动态计算或解析每一列的对齐宽度
        if col_widths is None:
            col_widths = []
            for lines in columns_lines:
                # 自动计算当前列的最长行宽，+2 作为安全间距，最高限制 120
                w = max((self._display_width(l) for l in lines), default=0) + 2
                w = min(w, 120)
                col_widths.append(w)
        elif len(col_widths) < num_columns:
            # 如果用户提供的宽度列表长度不足，用默认逻辑补齐
            col_widths = list(col_widths) + [120] * (num_columns - len(col_widths))

        # 4. 逐行拼接并打印
        for i in range(max_lines):
            row_cells = []
            for col_idx in range(num_columns):
                lines = columns_lines[col_idx]
                width = col_widths[col_idx]
                
                # 安全取行，超出文本范围则视为空字符串
                cell_text = lines[i] if i < len(lines) else ''
                
                # 最后一列通常不需要 padding 补白，避免右侧有无意义的空格
                if col_idx == num_columns - 1:
                    row_cells.append(cell_text)
                else:
                    row_cells.append(self._pad_text(cell_text, width))
                    
            # 用分隔符拼接当前行的所有列并打印
            self.info2file(quant_result_info=sep.join(row_cells))                   

class VP_BacktestEngine:
    """通用回测统计内核，兼容两个脚本的 evaluate 实现。"""
    @staticmethod
    def evaluate(prices, dates, signals, labels):
        p = np.array(prices, dtype=float)
        sig = np.array(signals, dtype=int)
        n = len(p)

        position = np.zeros(n, dtype=int)
        current_pos = 0
        for i in range(n):
            if sig[i] == 1:
                current_pos = 1
            elif sig[i] == -1:
                current_pos = 0
            position[i] = current_pos

        price_returns = np.zeros(n)
        if n > 1:
            price_returns[1:] = (p[1:] - p[:-1]) / p[:-1]
        strategy_returns = np.zeros(n)
        if n > 1:
            strategy_returns[1:] = position[:-1] * price_returns[1:]

        equity_curve = np.cumprod(1.0 + strategy_returns) if n > 0 else np.array([])
        running_max = np.maximum.accumulate(equity_curve) if n > 0 else np.array([])
        drawdowns = (equity_curve - running_max) / running_max if n > 0 else np.zeros(n)
        max_drawdown = np.min(drawdowns) if len(drawdowns) > 0 else 0.0

        trades = []
        in_trade = False
        buy_price = 0.0
        trade_logs = []

        for i in range(n):
            if sig[i] == 1 and not in_trade:
                in_trade = True
                buy_price = p[i]
                trade_logs.append({"type": "BUY", "date": dates[i], "price": p[i], "reason": labels[i], "return": 0.0})
            elif sig[i] == -1 and in_trade:
                in_trade = False
                sell_price = p[i]
                trade_return = (sell_price - buy_price) / buy_price if buy_price != 0 else 0.0
                trades.append(trade_return)
                trade_logs.append({"type": "SELL", "date": dates[i], "price": p[i], "reason": labels[i], "return": trade_return * 100})

        if in_trade and n > 0:
            trade_return = (p[-1] - buy_price) / buy_price if buy_price != 0 else 0.0
            trades.append(trade_return)
            trade_logs.append({"type": "CLOSE_MANDATORY", "date": dates[-1], "price": p[-1], "reason": "历史数据结束强制平仓", "return": trade_return * 100})

        trades = np.array(trades) if len(trades) > 0 else np.array([])
        total_trades = len(trades)
        winning_trades = np.sum(trades > 0) if total_trades > 0 else 0
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0

        benchmark_return = (p[-1] - p[0]) / p[0] if n > 0 else 0.0

        return {
            "total_return": (equity_curve[-1] - 1.0) * 100 if len(equity_curve) > 0 else 0.0,
            "benchmark_return": benchmark_return * 100,
            "total_trades": total_trades,
            "win_rate": win_rate * 100,
            "max_drawdown": max_drawdown * 100,
            "max_win": np.max(trades) * 100 if total_trades > 0 else 0.0,
            "max_loss": np.min(trades) * 100 if total_trades > 0 else 0.0,
            "trade_logs": trade_logs,
        }
