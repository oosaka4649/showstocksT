import numpy as np

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
        dates, prices, volumes = stock_data["categoryData"], stock_data["closes"], stock_data["volumes"]  # 注意这里我们用的是 volumes_macd 来观察成交量和 macd 的关系
        return dates, prices, volumes
    
    def _split_data_add_snapshot_data(self, data, snapshot_data, start_date=None):
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
        category_data.append("snapshot")  # 添加快照日期 
        closes.append(_snapshot_data["close"])  # 添加快照的收盘价
        volumes.append(_snapshot_data["volume"])  # 添加快照的成交量到 macd 数据中
        
        return {"categoryData": category_data, "closes": closes, "volumes": volumes}    

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
