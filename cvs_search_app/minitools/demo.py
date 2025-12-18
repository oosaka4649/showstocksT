'''
https://juejin.cn/post/7281089570375893053

1 根据csv，显示 k线图，可以显示均线，后续，根据周，月均线等 看能否显示到一个图里面
2 结合均线，指标，等

3 这tools文件夹，后面作为我小工具的文件夹

https://pyecharts.org/#/zh-cn/donate   中文文档
https://gallery.pyecharts.org/#/Candlestick/professional_kline_chart  代码示例
https://github.com/pyecharts/pyecharts  代码库
https://bbs.huaweicloud.com/blogs/421186   一个实例

生成的html文件，只能用edge打开

https://blog.csdn.net/qiuxiaodu/article/details/145389009   将浏览器中的图形全屏宽显示
\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyecharts\render\templates
macro 文件里面的 第 二行  width:100% 修改成下面一样
    <div id="{{ c.chart_id }}" class="chart-container" style="width:100%; height:{{ c.height }}; {{ c.horizontal_center }}"></div>



https://ta-lib-python.transdocs.org/
https://zxdd.com/TA-Lib
https://zhuanlan.zhihu.com/p/683857187
'''