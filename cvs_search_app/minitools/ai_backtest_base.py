import numpy as np

class BaseModel:
    """基础模型类，提供通用工具方法供子类复用。"""
    def _rolling_window(self, a, window):
        """利用 NumPy stride 生成滚动窗口视图（不复制内存）。"""
        a = np.array(a)
        shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
        strides = a.strides + (a.strides[-1],)
        return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


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
