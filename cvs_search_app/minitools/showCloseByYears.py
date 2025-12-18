import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np

class InteractiveStockChart:
    def __init__(self, csv_file, start_date=None, use_returns=True):
        """
        初始化交互式股票图表
        
        Args:
            csv_file (str): CSV文件路径
            start_date (str): 起始日期，格式为"MM-DD"，例如"03-01"表示每年从3月1日开始
            use_returns (bool): 是否使用收益率而非绝对价格
        """
        # 在程序开始时调用字体设置
        self.set_chinese_font()          
        self.start_date = start_date
        self.use_returns = use_returns
        self.df = self.load_data(csv_file)
        self.fig, self.ax = plt.subplots(figsize=(14, 8))
        self.lines = {}  # 存储各年份的线条对象
        self.visible_lines = set()  # 当前可见的线条
        self.yearly_data = {}  # 存储各年份数据
        self.line_data = {}  # 存储每条线的数据，用于悬停提示
        self.hover_annotation = None  # 悬停提示注解对象
        self.scatter_points = {}  # 存储散点对象，用于扩大悬停区域
        
        
    # 设置中文字体支持
    def set_chinese_font(self):
        """
        设置matplotlib支持中文显示
        """
        try:
            # 尝试使用系统中已有的中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号
            print("中文字体设置成功")
        except:
            print("警告: 中文字体设置失败，图表中的中文可能显示为方块")
            # 如果上述字体不存在，尝试使用系统默认字体
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
                    
    def load_data(self, csv_file):
        """
        加载CSV数据并预处理
        
        Args:
            csv_file (str): CSV文件路径
            
        Returns:
            pd.DataFrame: 处理后的数据
        """
        # 读取CSV文件
        df = pd.read_csv(csv_file)
        
        # 确保包含必要的列
        required_cols = ['Date', 'Close']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"CSV文件必须包含'{col}'列")
        
        # 转换日期格式
        df['Date'] = pd.to_datetime(df['Date'])
        
        # 按日期排序
        df = df.sort_values('Date')
        
        # 提取年份和日期信息
        df['Year'] = df['Date'].dt.year
        df['MonthDay'] = df['Date'].dt.strftime('%m-%d')
        
        return df
    
    def get_fiscal_year(self, date):
        """
        根据起始日期计算财年
        
        Args:
            date (pd.Timestamp): 日期
            
        Returns:
            tuple: (财年标签, 统一日期, 起始日期)
        """
        if self.start_date is None:
            # 如果没有指定起始日期，使用自然年
            fiscal_year = date.year
            uniform_date = date.replace(year=2000)
            fiscal_start = datetime(date.year, 1, 1)
            return fiscal_year, uniform_date, fiscal_start
        
        # 解析起始日期
        start_month, start_day = map(int, self.start_date.split('-'))
        
        # 创建当前年份的起始日期
        fiscal_start = datetime(date.year, start_month, start_day)
        
        if date >= fiscal_start:
            # 在当前财年内
            fiscal_year = date.year
            # 计算从财年开始的天数偏移
            days_offset = (date - fiscal_start).days
            # 转换为2000年的统一日期
            uniform_date = datetime(2000, 1, 1) + timedelta(days=days_offset)
        else:
            # 在上一个财年内
            fiscal_year = date.year - 1
            # 创建上一个财年的起始日期
            prev_fiscal_start = datetime(date.year - 1, start_month, start_day)
            # 计算从财年开始的天数偏移
            days_offset = (date - prev_fiscal_start).days
            # 转换为2000年的统一日期
            uniform_date = datetime(2000, 1, 1) + timedelta(days=days_offset)
            fiscal_start = prev_fiscal_start
        
        return fiscal_year, uniform_date, fiscal_start
    
    def prepare_yearly_data(self):
        """
        准备按财年分组的数据，并计算收益率
        
        Returns:
            dict: 财年为键，包含统一日期、收盘价和收益率的数据框为值
        """
        yearly_data = {}
        
        # 应用财年计算
        fiscal_data = []
        for _, row in self.df.iterrows():
            fiscal_year, uniform_date, fiscal_start = self.get_fiscal_year(row['Date'])
            fiscal_data.append({
                'FiscalYear': fiscal_year,
                'UniformDate': uniform_date,
                'Close': row['Close'],
                'OriginalDate': row['Date'],
                'FiscalStart': fiscal_start
            })
        
        fiscal_df = pd.DataFrame(fiscal_data)
        
        # 按财年分组
        fiscal_years = fiscal_df['FiscalYear'].unique()
        
        for fiscal_year in sorted(fiscal_years):
            year_data = fiscal_df[fiscal_df['FiscalYear'] == fiscal_year].copy()
            
            # 按统一日期排序
            year_data = year_data.sort_values('UniformDate')
            
            # 计算相对于起始日的收益率
            if len(year_data) > 0:
                # 获取财年起始日的收盘价
                start_date = year_data['FiscalStart'].iloc[0]
                start_price = self.df[
                    (self.df['Date'] >= start_date) & 
                    (self.df['Date'] <= start_date + timedelta(days=30))
                ]['Close']
                
                if len(start_price) > 0:
                    start_close = start_price.iloc[0]
                else:
                    # 如果找不到起始日附近的价格，使用财年第一个数据点
                    start_close = year_data['Close'].iloc[0]
                
                # 计算收益率（百分比）
                year_data['Return'] = (year_data['Close'] / start_close - 1) * 100
                
                # 添加月份和日期信息用于悬停提示
                year_data['MonthDay'] = year_data['OriginalDate'].dt.strftime('%m-%d')
                
                yearly_data[fiscal_year] = year_data
        
        return yearly_data
    
    def create_chart(self):
        """创建交互式图表"""
        self.yearly_data = self.prepare_yearly_data()
        
        if not self.yearly_data:
            print("没有可用的数据")
            return
        
        # 设置颜色循环
        colors = plt.cm.Set3(np.linspace(0, 1, len(self.yearly_data)))
        
        # 绘制各财年线条
        for i, (fiscal_year, year_data) in enumerate(self.yearly_data.items()):
            color = colors[i % len(colors)]
            
            # 选择使用收益率还是收盘价
            if self.use_returns:
                y_data = year_data['Return']
                y_label = '收益率 (%)'
            else:
                y_data = year_data['Close']
                y_label = '收盘价'
            
            # 绘制主线条
            line, = self.ax.plot(year_data['UniformDate'], y_data, 
                               label=str(fiscal_year), linewidth=2, alpha=0.7,
                               color=color, picker=True, pickradius=10)  # 增加pickradius
            
            # 添加透明散点以扩大悬停区域
            scatter = self.ax.scatter(year_data['UniformDate'], y_data, 
                                    s=20, alpha=0,  # 完全透明，但可悬停
                                    picker=True, pickradius=15)
            
            # 存储每条线的数据，用于悬停提示
            self.line_data[fiscal_year] = {
                'month_days': year_data['MonthDay'].tolist(),
                'returns': year_data['Return'].tolist(),  # 收益率数据
                'close_prices': year_data['Close'].tolist(),  # 收盘价数据
                'dates': year_data['UniformDate'].tolist(),
                'line': line,
                'scatter': scatter
            }
            
            self.lines[fiscal_year] = line
            self.scatter_points[fiscal_year] = scatter
            self.visible_lines.add(fiscal_year)
        
        # 设置图表属性
        self.setup_chart()
        
        # 连接事件
        self.connect_events()
        
        plt.tight_layout()
        plt.show()
    
    def setup_chart(self):
        """设置图表样式和格式"""
        # 设置x轴格式
        if self.start_date:
            # 使用自定义起始日期时，显示从起始日期开始的天数
            self.ax.set_xlabel(f'从{self.start_date}开始的天数', fontsize=12)
            
            # 添加主要刻度（每月）
            locator = mdates.MonthLocator()
            self.ax.xaxis.set_major_locator(locator)
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        else:
            # 使用自然年时，显示月-日格式
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            self.ax.xaxis.set_major_locator(mdates.MonthLocator())
            self.ax.set_xlabel('日期（月-日）', fontsize=12)
        
        # 旋转x轴标签
        plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45)
        
        # 设置标题和y轴标签
        if self.start_date:
            if self.use_returns:
                title = f'股票收益率对比（财年从{self.start_date}开始）'
                y_label = '收益率 (%)'
            else:
                title = f'股票收盘价对比（财年从{self.start_date}开始）'
                y_label = '收盘价'
        else:
            if self.use_returns:
                title = '股票收益率年度对比'
                y_label = '收益率 (%)'
            else:
                title = '股票收盘价年度对比'
                y_label = '收盘价'
        
        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.ax.set_ylabel(y_label, fontsize=12)
        
        # 添加零线（当显示收益率时）
        if self.use_returns:
            self.ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        
        # 添加网格
        self.ax.grid(True, alpha=0.3)
        
        # 添加图例
        self.ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        
        # 设置图例点击事件
        if self.ax.legend_:
            for legend_line in self.ax.legend_.get_lines():
                legend_line.set_picker(True)
                legend_line.set_pickradius(10)
    
    def connect_events(self):
        """连接鼠标事件"""
        self.fig.canvas.mpl_connect('pick_event', self.on_pick)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_hover)
    
    def on_pick(self, event):
        """
        处理鼠标点击事件
        
        Args:
            event: 鼠标事件对象
        """
        # 检查是否点击了图例
        if self.ax.legend_ and event.artist in self.ax.legend_.get_lines():
            # 找到对应的财年
            for fiscal_year, line in self.lines.items():
                if line.get_label() == event.artist.get_label():
                    self.toggle_line_visibility(fiscal_year)
                    break
        
        # 检查是否点击了数据线或散点
        elif event.artist in self.lines.values() or event.artist in self.scatter_points.values():
            # 找到对应的财年
            for fiscal_year, line in self.lines.items():
                if line == event.artist or self.scatter_points[fiscal_year] == event.artist:
                    self.toggle_line_visibility(fiscal_year)
                    break
        
        self.fig.canvas.draw()
    
    def on_hover(self, event):
        """
        处理鼠标悬停事件
        
        Args:
            event: 鼠标事件对象
        """
        if event.inaxes != self.ax:
            # 鼠标不在图表区域内，清除提示
            if self.hover_annotation:
                self.hover_annotation.set_visible(False)
                self.fig.canvas.draw_idle()
            return
        
        # 使用更宽松的检测方法
        closest_data = self.find_closest_point_enhanced(event.xdata, event.ydata)
        
        # 显示或更新提示
        if closest_data is not None:
            self.show_tooltip(closest_data, event)
        else:
            # 鼠标不靠近任何线，隐藏提示
            if self.hover_annotation:
                self.hover_annotation.set_visible(False)
                self.fig.canvas.draw_idle()
    
    def find_closest_point_enhanced(self, x, y):
        """
        增强版：找到距离鼠标位置最近的数据点，使用更宽松的检测
        
        Args:
            x: 鼠标x坐标
            y: 鼠标y坐标
            
        Returns:
            dict: 包含最近点数据的字典，或None
        """
        if x is None or y is None:
            return None
            
        closest_distance = float('inf')
        closest_data = None
        
        # 获取坐标轴范围以计算相对距离
        x_lim = self.ax.get_xlim()
        y_lim = self.ax.get_ylim()
        
        # 计算坐标轴范围
        x_range = x_lim[1] - x_lim[0]
        y_range = y_lim[1] - y_lim[0]
        
        # 将x坐标转换为日期数值
        if hasattr(x, 'year'):
            x_num = mdates.date2num(x)
        else:
            x_num = x
        
        for fiscal_year, data in self.line_data.items():
            if fiscal_year not in self.visible_lines:
                continue  # 跳过隐藏的线条
                
            # 获取线条数据
            dates = data['dates']
            values = data['returns'] if self.use_returns else data['close_prices']
            
            # 找到线上最近的点
            for i, (date, value) in enumerate(zip(dates, values)):
                # 将日期转换为数值
                date_num = mdates.date2num(date)
                
                # 计算相对距离（考虑坐标轴范围）
                x_dist = abs(date_num - x_num) / x_range
                y_dist = abs(value - y) / y_range
                
                # 使用加权距离（更重视x轴距离，因为时间序列主要在x轴变化）
                distance = np.sqrt((x_dist * 0.7)**2 + (y_dist * 0.3)**2)
                
                # 设置一个更宽松的阈值
                if distance < closest_distance and distance < 0.05:  # 更宽松的阈值
                    closest_distance = distance
                    closest_data = {
                        'x': date,
                        'y': value,
                        'index': i,
                        'fiscal_year': fiscal_year
                    }
        
        return closest_data
    
    def show_tooltip(self, data, event):
        """
        显示悬停提示
        
        Args:
            data: 包含要显示的数据的字典
            event: 鼠标事件对象
        """
        fiscal_year = data['fiscal_year']
        index = data['index']
        
        # 获取数据
        line_data = self.line_data[fiscal_year]
        month_day = line_data['month_days'][index]
        return_value = line_data['returns'][index]
        close_price = line_data['close_prices'][index]
        
        # 格式化提示内容
        return_text = f"{return_value:.2f}%"
        close_text = f"{close_price:.2f}"
        
        # 创建或更新提示
        if self.hover_annotation is None:
            self.hover_annotation = self.ax.annotate(
                "", 
                xy=(data['x'], data['y']),
                xytext=(20, 20),
                textcoords="offset points",
                bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.9, ec="black"),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0")
            )
        else:
            self.hover_annotation.set_visible(True)
        
        # 更新提示内容
        self.hover_annotation.xy = (data['x'], data['y'])
        self.hover_annotation.set_text(f"{fiscal_year}年\n{month_day}\n收益率: {return_text}\n收盘价: {close_text}")
        
        # 重绘画布
        self.fig.canvas.draw_idle()
    
    def toggle_line_visibility(self, fiscal_year):
        """
        切换线条的可见性
        
        Args:
            fiscal_year (int): 要切换的财年
        """
        line = self.lines[fiscal_year]
        scatter = self.scatter_points[fiscal_year]
        
        if fiscal_year in self.visible_lines:
            line.set_alpha(0.1)  # 设置为半透明
            scatter.set_alpha(0)  # 散点也设为透明
            self.visible_lines.remove(fiscal_year)
        else:
            line.set_alpha(0.7)  # 恢复显示
            scatter.set_alpha(0)  # 散点保持透明（但可悬停）
            self.visible_lines.add(fiscal_year)
        
        # 重绘画布
        self.fig.canvas.draw()
    
    def add_statistics(self):
        """添加统计信息"""
        if not hasattr(self, 'stats_added'):
            print("财年统计信息:")
            for fiscal_year, data in self.yearly_data.items():
                if self.use_returns:
                    values = data['Return']
                    unit = "%"
                else:
                    values = data['Close']
                    unit = ""
                
                print(f"{fiscal_year}财年: 均值={values.mean():.2f}{unit}, "
                      f"标准差={values.std():.2f}{unit}, "
                      f"最小值={values.min():.2f}{unit}, "
                      f"最大值={values.max():.2f}{unit}")
            
            self.stats_added = True
    
    def export_data(self, filename=None):
        """
        导出处理后的数据
        
        Args:
            filename (str): 导出文件名
        """
        if filename is None:
            if self.start_date:
                filename = f"processed_data_start_{self.start_date}.csv"
            else:
                filename = "processed_data.csv"
        
        export_data = []
        for fiscal_year, data in self.yearly_data.items():
            for _, row in data.iterrows():
                export_data.append({
                    'FiscalYear': fiscal_year,
                    'UniformDate': row['UniformDate'],
                    'OriginalDate': row['OriginalDate'],
                    'Close': row['Close'],
                    'Return': row['Return']
                })
        
        export_df = pd.DataFrame(export_data)
        export_df.to_csv(filename, index=False)
        print(f"数据已导出到: {filename}")

def main():
    """
    主函数 - 使用示例
    """
    
    # 使用示例
    csv_file = 'E:\mygithub\showstocksT\cvs_search_app\stockscsv\sh601366.csv'  # 替换为您的CSV文件路径
    
    # 指定起始日期（例如："03-01"表示每年从3月1日开始）
    start_date = "09-01"  # 可以修改为任何想要的起始日期，如"01-01", "07-01"等
    
    # 是否使用收益率（True）还是收盘价（False）
    use_returns = True
    
    try:
        # 尝试加载用户提供的文件
        chart = InteractiveStockChart(csv_file, start_date=start_date, use_returns=use_returns)
        # 显示统计信息
        chart.add_statistics()
        
        # 导出处理后的数据（可选）
        chart.export_data()
        
        # 创建交互式图表
        print(f"正在生成交互式图表（起始日期: {start_date if start_date else '自然年'}）...")
        print("使用说明:")
        print("- 点击图例中的年份可以显示/隐藏该财年的数据线")
        print("- 直接点击数据线也可以切换显示")
        print("- 鼠标悬停在线条附近显示具体日期、收益率和收盘价")
        print("- 悬停区域已扩大，更容易触发提示")
        
        chart.create_chart()        
    except Exception as e:
        print(f"加载文件时出错: {e}")

if __name__ == "__main__":
    main()