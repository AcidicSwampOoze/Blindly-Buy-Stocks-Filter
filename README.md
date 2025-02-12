# Blindly-Buy-Stocks-Filter

股票筛选工具

打包命令: python -m PyInstaller --onefile --noconsole --add-data="stock_cache;stock_cache" --add-data="icon.ico;." stock_screener_low.py

运行命令: python stock_screener_low.py

打包后路径：dist/stock_screener_low.exe

tushare的API接口token: 875009d14db5d6a06510f8546df96257fbcd29ab5b35534454abe3a0

相关网站： 

股票API： https://tushare.pro/webclient/

1.0版本 
由DeepSeek生成简单调试后发布
更新时间：2025-02-04
by DeepSeek

1.1版本 
新增缓存股票数据功能
新增中证500成分股
修改判断策略为60线
更新时间：2025-02-06
by aka乱破

1.2版本
新增使用说明
新增付费接口，可以获取更多数据
新增获取最近交易日
新增股票基础信息
优化缓存读写逻辑，比对最近交易日确定是否更新数据
优化股票池筛选逻辑
优化运行速度
优化从api接口获取最新股票池
优化缓存读写方案不再使用.cxv
删除了自定义股票池输入框
更新时间：2025-02-12
by aka乱破