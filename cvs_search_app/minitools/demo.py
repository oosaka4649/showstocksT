'''
https://juejin.cn/post/7281089570375893053

1 根据csv，显示 k线图，可以显示均线，后续，根据周，月均线等 看能否显示到一个图里面
2 结合均线，指标，等

3 这tools文件夹，后面作为我小工具的文件夹  talib and pyecharts stock analysis tools

https://pyecharts.org/#/zh-cn/donate   中文文档  pip install pyecharts
https://gallery.pyecharts.org/#/Candlestick/professional_kline_chart  代码示例
https://github.com/pyecharts/pyecharts  代码库
https://bbs.huaweicloud.com/blogs/421186   一个实例

生成的html文件，只能用edge打开

https://blog.csdn.net/qiuxiaodu/article/details/145389009   将浏览器中的图形全屏宽显示
\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyecharts\render\templates
macro 文件里面的 第 二行  width:100% 修改成下面一样
    <div id="{{ c.chart_id }}" class="chart-container" style="width:100%; height:{{ c.height }}; {{ c.horizontal_center }}"></div>



https://ta-lib-python.transdocs.org/  指标库  python -m pip install TA-Lib
https://zxdd.com/TA-Lib
https://zhuanlan.zhihu.com/p/683857187



这网站kaggle提供，浏览器登陆后，可以在这网站远程训练ai模型
bowu3394@gmail.com  我使用了默认的gmail邮箱登录

Your username
oosaka4649 (not editable)

Your account number
31407199
https://www.kaggle.com/


学习网站
http://python.86x.net/pandas13/index.html
https://docs.python.org/zh-cn/3/tutorial/datastructures.html#sets




WorldQuant101
预测股票市场的101个alpha因子的解读与总结
http://www.qianshancapital.com/h-nd-329.html
'''


'''
选股手顺

1 直接跑 最后一个框中 ，勾选list名后，点 执行回测   策略  
    看结果，选取收益高的 30%以上，再研究，进出场时机 

    或把选出的 每天跑，如果有入场信号就买入试试

2 或，按当日个股涨幅榜，取 换手率高于 25%以上，再看看 回测结果，重复上面 步骤

3 自己库存的股票，执行上面 结果

4 每天跑一下上穿25日均线的股票，选出想买的票，再一个个分析和回测


历年双色球中奖号码数据集
https://gitcode.com/open-source-toolkit/ae637/blob/main/README.md
https://gitcode.com/open-source-toolkit/ae637/blob/main/%E5%8E%86%E5%B9%B4%E5%8F%8C%E8%89%B2%E7%90%83%E4%B8%AD%E5%A5%96%E5%8F%B7%E7%A0%812003-2023%E5%B9%B4.rar




PyPortfolioOpt   PyPortfolioOpt

这个操作指南，主要针对那些对优化组合一些资产（很可能是股票）的快速方法感兴趣的用户。 
在必要的时候，我也介绍了所需的理论，也指出了可能是更高级优化技术的合适跳板的领域。 
有关参数的细节可以在各自的文档页面中找到（请见侧边导航栏）。

在本指南中，我们将专注于均值-方差优化（MVO），这是大多数人听到“投资组合优化”时想到的东西。 
MVO 构成了 PyPortfolioOpt 产品的核心，不过需要注意的是，MVO 有很多种类，可能有非常不同的性能特征。 
请参考侧边导航栏，了解各种可能性，以及提供的其他优化方法。现在，我们将继续使用标准的有效前沿。
https://www.wuzao.com/document/pyportfolioopt/UserGuide.html
https://portfolio.apachecn.org/Installation/


Kronos：金融市场语言的基础模型
Kronos 是首个面向金融K线图的开源基础模型， 基于全球超过45家交易所的数据训练而成。
https://github.com/shiyu-coder/kronos?tab=readme-ov-file
https://github.com/shiyu-coder/kronos  
https://www.zdoc.app/zh/shiyu-coder/Kronos


2026-04-15 到 2026-05-15 期间，工作计划

https://www.youtube.com/watch?v=rQkTmB9g3rk&list=PLkWWcTwDGs4ambkQlcVLtehFPPnTseKab&index=4  太极拳下载

1 stock_price_analysis_by_list.py 这个文件，主要是根据股票列表，改造成读入股票代码list，在一个html里面同时显示全部股票的最高，最低价的信息，供短线时查看参考。

https://www.google.com/search?q=pyechats%E7%94%BB%E9%A5%BC%E5%9B%BE%EF%BC%8C%E5%B9%B6%E5%AE%9A%E4%B9%89%E6%98%BE%E7%A4%BA&oq=pyechats%E7%94%BB%E9%A5%BC%E5%9B%BE%EF%BC%8C%E5%B9%B6%E5%AE%9A%E4%B9%89%E6%98%BE%E7%A4%BA&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIJCAEQIRgKGKAB0gEKNDQwNzNqMGoxNagCCLACAQ&sourceid=chrome&ie=UTF-8
2 通过学习，看能否，把饼图鼠标移到上面的显示，改为日期和具体差价等信息，增加实用性


2. 代码实现
python
from pyecharts.charts import Pie
from pyecharts import options as opts

# 1. 准备数据
data = [("苹果", 40), ("香蕉", 20), ("葡萄", 30), ("芒果", 10)]

# 2. 创建饼图实例
pie = (
    Pie()
    .add(
        series_name="水果销量",  # 系列名称
        data_pair=data,       # 数据
        radius=["40%", "70%"],  # 定义环形图，内圈半径和外圈半径
        label_opts=opts.LabelOpts(
            position="outside",  # 标签显示在外部
            # 自定义显示内容: {b}名称, {c}数值, {d}百分比
            formatter="{b}: {c} ({d}%)"
        ),
    )
    # 3. 设置全局配置项
    .set_global_opts(
        title_opts=opts.TitleOpts(title="水果销量饼图"),
        legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%"),
    )
    # 4. 设置系列配置项 (自定义颜色等)
    .set_series_opts(
        label_opts=opts.LabelOpts(formatter="{b}: {c} ({d}%)"),
    )
)

# 5. 生成并保存HTML文件
pie.render("pie_chart.html")
3. 自定义显示说明 
CSDN博客
CSDN博客
 +1
半径设置 (radius): radius=["40%", "70%"] 传入列表，分别表示内半径和外半径。如果是 radius="50%" 则为普通饼图。
标签格式化 (formatter): formatter="{b}: {c} ({d}%)"
{a}: 系列名称 (series_name)
{b}: 数据项名称 (如 "苹果")
{c}: 数值 (如 40)
{d}: 百分比 (如 40%)
标签位置 (position): 可选 "outside"（外部）、"inside"（内部）、"center"（中心）。
图例方向 (orient): legend_opts 中可设置 "horizontal" (水平) 或 "vertical" (垂直)。
运行代码后会生成一个 pie_chart.html 文件，用浏览器打开即可看到自定义样式的饼图。


使用 pyecharts 绘制饼图，核心在于使用 Pie 类及其配置项。你可以通过 label_opts 来自定义数据显示格式（如显示名称、数值或百分比）。 
CSDN博客
CSDN博客
 +1
1. 基础绘制与显示定义
在 pyecharts 中，最常用的显示定义是通过 Formatter 回调字符串实现的。例如：
{b}：代表数据项名称。
{c}：代表数值。
{d}：代表百分比。 
CSDN博客
CSDN博客
python
from pyecharts import options as opts
from pyecharts.charts import Pie

# 1. 准备数据：格式为 [(key1, value1), (key2, value2)]
data = [("华为", 150), ("小米", 120), ("苹果", 100), ("三星", 80)]

# 2. 创建饼图实例
c = (
    Pie()
    .add(
        "", 
        data,
        # 设置半径，[内半径, 外半径] 可做成环形图
        radius=["40%", "75%"] 
    )
    # 3. 全局配置项
    .set_global_opts(
        title_opts=opts.TitleOpts(title="手机销量占比"),
        legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%")
    )
    # 4. 系列配置项：定义标签显示内容
    .set_series_opts(
        label_opts=opts.LabelOpts(formatter="{b}: {c} ({d}%)")
    )
)

# 5. 渲染图表到 HTML
c.render("pie_chart.html")
请谨慎使用此类代码。
2. 常用显示配置技巧
显示百分比（不带小数）：使用 formatter="{b}: {d}%"。
环形图效果：在 add() 方法中设置 radius=["inner", "outer"]，如 radius=["30%", "70%"]。
玫瑰图效果：设置 rosetype="radius" 或 rosetype="area"，使半径随数值大小变化。
隐藏标签：若饼图太挤，可设置 label_opts=opts.LabelOpts(is_show=False)，仅在鼠标悬停时显示。 
CSDN博客


占位符是固定内容吗，我可以自定义其他的内容呢
占位符（如 {b}, {c}, {d}）是 ECharts 内置的快捷变量，它们确实是固定的，只能代表名称、数值和百分比。
如果你想显示数据中额外定义的字段（比如“负责人”、“备注”或者“单位”），或者想加入自定义的文字逻辑，主要有以下两种方案：
方案一：在数据源中“埋”入额外信息（JsCode 配合）
pyecharts 的基础数据格式通常是 [名称, 数值]，但你可以在数据项中加入更多自定义键值对。
python
from pyecharts import options as opts
from pyecharts.charts import Pie
from pyecharts.commons.utils import JsCode

# 定义数据，注意这里每个项除了 value，还可以自定义其他属性（如 unit, manager）
data_pairs = [
    {"value": 150, "name": "华为", "unit": "万台", "manager": "张三"},
    {"value": 120, "name": "小米", "unit": "万台", "manager": "李四"},
    {"value": 100, "name": "苹果", "unit": "台", "manager": "王五"},
]

c = (
    Pie()
    .add(
        series_name="销量详情",
        data_pair=data_pairs, # 直接传入字典列表
    )
    .set_series_opts(
        label_opts=opts.LabelOpts(
            # 使用 JsCode 提取自定义内容
            # params.data 指向的就是我们上面定义的字典对象
            formatter=JsCode(
                """
                function(params) {
                    return params.name + ' [' + params.data.manager + ']\\n' + 
                           '销量：' + params.value + params.data.unit;
                }
                """
            )
        )
    )
)
请谨慎使用此类代码。
方案二：直接在字符串里拼接固定内容
如果你只是想在每个标签后面加点固定的文字（不随数据变化），直接在字符串里写就行：
python
# 这里的“部门报告”和“截止月底”是完全自定义的
.set_series_opts(
    label_opts=opts.LabelOpts(formatter="部门报告：{b} \n 实时数据：{c} (截止月底)")
)
请谨慎使用此类代码。
总结：如何选择？
纯固定文字：直接在 formatter="{b} 任何你想写的字" 里拼。
数据随动内容：比如有的项单位是“个”，有的是“吨”，必须用 JsCode + params.data。
计算后的内容：比如你想显示 数值 * 2 的结果，也必须用 JsCode 在前端动态计算。
你现在的数据源里，是否包含了一些特定的列（如“日期”、“同比增速”）是默认占位符显示不出来的？我可以帮你写对应的 JsCode 逻辑。


======================================================== 股票 =========================================================

https://ta-lib.org/install/ 下载最新 ta-lib 共享静态库和头文件，按照说明进行安装。

模板
最近交易：


日线macd：

买卖计划：





https://algebrica.org/
https://github.com/antoniolupetti/algebrica
免费、无广告的大学数学知识库

https://jubt13.xyz/cn/study.html


通达信函数
DYNAINFO(3)	昨收盘价
DYNAINFO(4)	开盘价
DYNAINFO(5)	最高价
DYNAINFO(6)	最低价
DYNAINFO(7)	现价
DYNAINFO(8)	总量
DYNAINFO(9)	现量
DYNAINFO(10)	总金额
DYNAINFO(11)	均价
DYNAINFO(12)	日涨跌
DYNAINFO(13)	振幅
DYNAINFO(14)	涨幅
DYNAINFO(15)	开盘金额
DYNAINFO(16)	前5日每分钟均量
DYNAINFO(17)	量比
DYNAINFO(18)	上涨家数
DYNAINFO(19)	下跌家数
DYNAINFO(20)	买价(即买一价)
DYNAINFO(21)	卖价(即卖一价)
DYNAINFO(22)	内盘/板块指数跌停数
DYNAINFO(23)	外盘/板块指数涨停数
SELLVOL	内盘
BUYVOL	外盘
DYNAINFO(24)	涨速
DYNAINFO(25)	几分钟前的价格
DYNAINFO(26)	涨停价
DYNAINFO(27)	跌停价
DYNAINFO(28)	[新]笼子买入价上限
DYNAINFO(29)	[新]笼子卖出价下限
DYNAINFO(30)	[新]昨开盘成交里(手)
DYNAINFO(31)	[新]竞价涨停委买额
DYNAINFO(34)	昨日涨幅
DYNAINFO(35)	[新]3日换手Z
DYNAINFO(36)	[新]换手率Z
DYNAINFO(37)	换手率
DYNAINFO(38)	市盈(静)
DYNAINFO(39)	市盈(动)
DYNAINFO(40)	市盈(TTM)
DYNAINFO(49)	成交方向
DYNAINFO(50)	采样点数(分笔数)
DYNAINFO(51)	内外比
DYNAINFO(52)	港股资金流向
DYNAINFO(53)	应计利息/昨净值
DYNAINFO(54)	IOPV
DYNAINFO(55)	基金估算涨幅%
DYNAINFO(57)	笔涨跌
DYNAINFO(58)	买量(即买一量)
DYNAINFO(59)	卖量(即卖一量)
DYNAINFO(60)	沪深京总上涨家数
DYNAINFO(61)	沪深京总下跌家数
DYNAINFO(62)	沪深京总成交金额
DYNAINFO(63)	3日涨幅
DYNAINFO(64)	5日涨幅
DYNAINFO(65)	10日涨幅
DYNAINFO(66)	20日涨幅
DYNAINFO(67)	60日涨幅
DYNAINFO(68)	年初至今涨幅
DYNAINFO(69)	[新]月初至今涨幅
DYNAINFO(70)	[新]1年涨幅
DYNAINFO(71)	买二价
DYNAINFO(72)	买二量
DYNAINFO(73)	卖二价
DYNAINFO(74)	卖二量
DYNAINFO(75)	买三价
DYNAINFO(76)	买三量
DYNAINFO(77)	卖三价
DYNAINFO(78)	卖三量
DYNAINFO(79)	买四价
DYNAINFO(80)	买四量
DYNAINFO(81)	卖四价
DYNAINFO(82)	卖四量
DYNAINFO(83)	买五价
DYNAINFO(84)	买五量
DYNAINFO(85)	卖五价
DYNAINFO(86)	卖五量
DYNAINFO(88)	封单额
DYNAINFO(89)	年涨停天数
DYNAINFO(90)	连板天数
DYNAINFO(91)	几天
DYNAINFO(92)	几板
DYNAINFO(93)	[新]昨成交额
DYNAINFO(94)	[新]3日成交额
DYNAINFO(95)	[新]昨封单额
DYNAINFO(96)	[新]前封单额
DYNAINFO(99)	[新]主买净额
DYNAINFO(100)	[新]主力净额
DYNAINFO(101)	[新]量涨速
DYNAINFO(102)	[新]分钟换手率
DYNAINFO(103)	[新]2分钟金额
DYNAINFO(104)	[新]开盘抢筹
DYNAINFO(105)	[新]委比
DYNAINFO(106)	[新]总委买量
DYNAINFO(107)	[新]总委卖量
DYNAINFO(108)	[新]总撒买量
DYNAINFO(109)	[新]总撤卖量
DYNAINFO(110)	[新]L12逐笔成交数
DYNAINFO(111)	[新]L2逐笔委托数
DYNAINFO(117)	[新]量比(序列)
MAINZSHQ	[新]主要指数行情
TOTALMMPAMO	[新]沪深京买卖盘金额
ISBUYORDER	主动性买单
BETAVALUE	贝塔系数
SHAPE_SHORT	短期形态值
SHAPE_MID	中期形态值
SHAPE_LONG	长期形态值


************************************************************************************************************************
https://github.com/handsomejustin/easy_tdx
https://www.v2ex.com/t/1218903
通达信python SDK，支持在线获取数据及离线本地数据读取。全面优化接口

======================================================== 影视 =========================================================
https://www.btbtla.com/
影视下载站，原 btbtl.com 无法访问

https://www.movieffm.net
s在线影视站

Korean18x
https://korean18x.com/
韩国色情片


https://jubt13.xyz/cn/1fuli/20260512.html
https://github.com/thcp/stemdeck
音频分离工具，支持将音频分割成最多六个音轨（人声、鼓、贝斯、吉他、钢琴、其他），并在多轨混音器中播放


TVExplorer 全球直播电视浏览器
https://tvexplorer.live/

======================================================== 工具 =========================================================


Universal Video Downloader
https://github.com/Dinesh6777/Universal-Video-Downloader-GUI
基于 yt-dlp 的通用下载器


基于浏览器的 EPUB 阅读器，带有文本转语音功能
https://github.com/roy2100/readbook
https://jubt13.xyz/cn/books.html#%E7%94%B5%E5%AD%90%E4%B9%A6%E5%B7%A5%E5%85%B7



https://github.com/shidenggui
实时获取免费股票行情，支持新浪 / 腾讯(港股) / 集思录
 easyquotation  https://github.com/shidenggui/easyquotation

提供同花顺客户端/miniqmt/雪球的股票量化交易，支持跟踪 joinquant /ricequant 模拟交易 和 实盘雪球组合
 easytrader


How to Train Your GPT
https://github.com/raiyanyahya/how-to-train-your-gpt
从零开始构建 LLM 课程。每行代码都附有注释。讲解方式通俗易懂，就像给五岁小孩讲课一样。


天天磁力
https://www.xinxincilikp.top
https://www.cilishanc.top
https://www.xinxinciliwl.top
https://www.xinxincilikk.com

'''

'''
收藏网址 https://金坷垃.com

'''