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
'''