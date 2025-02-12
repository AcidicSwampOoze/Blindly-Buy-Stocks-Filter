import pandas as pd
import tushare as ts
import os
import sys
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import time

# 初始化日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 初始化（token）
ts.set_token('875009d14db5d6a06510f8546df96257fbcd29ab5b35534454abe3a0')
pro = ts.pro_api()
def resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class StockScreener:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("股票筛选器(2000分版)v1.2 by aka乱破 肯德基疯狂星期四v我50我代你吃")
        self.window.iconbitmap(resource_path('icon.ico'))   # 设置窗口图标
        self.cache_dir = "stock_cache"
        # self.small_cap_cache_file = os.path.join(self.cache_dir, 'small_cap_stocks_cache.parquet')  # 使用 Parquet 文件 股票盘缓存文件
        os.makedirs(self.cache_dir, exist_ok=True)
        self.recent_trading_day = self.get_recent_trading_day()  # 初始化获取最近的交易日并保存到公共变量
        self.create_widgets()  # 确保属性初始化后再调用 create_widgets

    def create_widgets(self):
        """创建界面组件"""
        frame = ttk.Frame(self.window, padding=20)
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # 设置字体
        font_large = ('Helvetica', 12)  # 你可以根据需要调整字体和大小

        ttk.Button(frame, text="开始筛选", command=self.run_screening).grid(row=1, column=0)
        ttk.Button(frame, text="导出结果", command=self.export_results).grid(row=1, column=1)
        ttk.Button(frame, text="更新股票池", command=self.update_stock_basic).grid(row=1, column=2)  # 添加更新按钮
        ttk.Button(frame, text="使用说明", command=self.show_instructions).grid(row=1, column=3)  # 添加更新按钮
        # ttk.Button(frame, text="更新股票池", command=self.update_small_cap_stocks).grid(row=1, column=2)  # 添加更新按钮

        self.tree = ttk.Treeview(self.window, columns=('代码', '名称', '信号日期', '回撤率', '最近一日涨幅'), show='headings')
        self.tree.heading('代码', text='股票代码')
        self.tree.heading('名称', text='股票名称')
        self.tree.heading('信号日期', text='信号日期')
        self.tree.heading('回撤率', text='回撤率(%)')
        self.tree.heading('最近一日涨幅', text='最近一日涨幅(%)')
        self.tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=1)

        # 设置Treeview的字体
        style = ttk.Style()
        style.configure("Treeview.Heading", font=font_large)
        style.configure("Treeview", font=font_large)

        # 设置按钮的字体
        style.configure("TButton", font=font_large)
    def show_instructions(self):
        """显示使用说明"""
        instructions = (
            "当前筛选方案：\n"
            "1. 近30交易日回撤百分之7-百分之35。 \n"
            "2. 近1交易日收盘价大于5日均价。\n"
            "3. 近1交易日交易量大于5日均量。\n"
            "4. 流通市值小于50亿。 \n"
            "使用说明：\n"
            "1. 第一次筛选需要先更新股票池。 \n"
            "2. 首次筛选较慢每分钟只能请求200只股票数据。\n"
            "3. 符合条件的股票可以点击按钮导出为表格，文件路径和软件同级。 \n"
            "4. 如需修改或有任何疑问请联系我。 \n"
        )
        tk.messagebox.showinfo("使用说明", instructions)

    def update_stock_basic(self):
        """获取股票基本信息并缓存"""
        cache_path = os.path.join(self.cache_dir, 'stock_basic_cache.parquet')
        try:
            stock_basic = pro.stock_basic(list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
            logging.info(f"获取股票基本信息成功，数量: {len(stock_basic)}")
            stock_basic.to_parquet(cache_path, index=False)
            logging.info(f"股票基本信息已保存到缓存")
            messagebox.showinfo("更新完成", "股票池已更新")
            return stock_basic
        except Exception as e:
            logging.error(f"获取股票基本信息失败: {e}")
            return pd.DataFrame()
        
    def get_stock_basic(self):
        """获取所有股票的基本信息，优先使用缓存"""
        cache_path = os.path.join(self.cache_dir, 'stock_basic_cache.parquet')
        
        # 优先使用缓存
        if os.path.exists(cache_path):
            try:
                stock_basic = pd.read_parquet(cache_path)
                logging.info(f"从缓存中获取股票基本信息成功，数量: {len(stock_basic)}")
                return stock_basic
            except Exception as e:
                logging.error(f"读取股票基本信息缓存失败: {e}")

        # 如果缓存不可用，重新请求数据
        return self.update_stock_basic()
    def get_recent_trading_day(self):
        """通过 trade_cal 接口获取过去最近的一个交易日"""
        try:
            # 获取当前日期
            today = datetime.now().strftime('%Y%m%d')
            today_15 = (datetime.now() - timedelta(days=15)).strftime('%Y%m%d')

            # 调用 trade_cal 接口获取交易日历
            trade_cal = pro.trade_cal(is_open='1', start_date=today_15, end_date=today, fields='cal_date')
            logging.info(f"获取交易日历成功，数量: {len(trade_cal)}")

            # 过滤出已经结束的交易日
            past_trading_days = trade_cal[trade_cal['cal_date'] < today]
            logging.info(f"过滤出过去交易日，数量: {len(past_trading_days)}")

            # 获取最近一个交易日
            recent_trading_day = past_trading_days['cal_date'].max()
            logging.info(f"最近一个交易日: {recent_trading_day}")

            return recent_trading_day
        except Exception as e:
            logging.error(f"获取最近交易日失败: {e}")
            return None
        
    def get_small_cap_stocks(self):
        """获取流通市值小于1e10的股票代码"""
        try:
            # 获取所有股票的基本信息
            stock_basic = self.get_stock_basic()
            if stock_basic.empty:
                logging.error("无法获取股票基本信息")
                return ""

            # 获取最近一个交易日
            recent_trading_day = self.recent_trading_day
            if not recent_trading_day:
                logging.error("无法获取最近交易日")
                return ""

            logging.info(f"最近一个交易日: {recent_trading_day}")

            # 获取每日基本面数据（包含流通市值）
            daily_basic = pro.daily_basic(trade_date=recent_trading_day, fields='ts_code,circ_mv')
            logging.info(f"获取每日基本面数据成功，数量: {len(daily_basic)}")

            # 合并数据
            merged_data = pd.merge(stock_basic, daily_basic, on='ts_code')
            logging.info(f"合并数据成功，数量: {len(merged_data)}")

            # 过滤出流通市值小于1e9的股票
            small_cap_stocks = merged_data[merged_data['circ_mv'] < 500000]
            logging.info(f"过滤出流通市值小于1e10的股票，数量: {len(small_cap_stocks)}")

            # 返回股票代码列表
            return ','.join(small_cap_stocks['ts_code'].tolist())
        except Exception as e:
            logging.error(f"获取小盘股数据失败: {e}")
            return ""
    
    # def update_small_cap_stocks(self):
    #     """更新股票池"""
    #     small_cap_stocks = self.get_small_cap_stocks()
    #     if not small_cap_stocks:
    #         messagebox.showwarning("更新失败", "未获取到符合条件的股票代码")
    #         return

    #     self.stock_entry.delete(0, tk.END)
    #     self.stock_entry.insert(0, small_cap_stocks)
    #     self.save_small_cap_stocks_to_cache(small_cap_stocks)
    #     messagebox.showinfo("更新完成", "股票池已更新")

    def get_cached_data(self, ts_code):
        """获取缓存数据"""
        cache_path = os.path.join(self.cache_dir, f"{ts_code}.parquet")  # 使用 Parquet 文件
        if os.path.exists(cache_path):
            try:
                df = pd.read_parquet(cache_path)  # 从 Parquet 文件读取
                df['trade_date'] = df['trade_date'].astype(str)
                logging.info(f"股票代码缓存数据获取成功: {ts_code}")
                return df
            except Exception as e:
                logging.error(f"读取缓存文件失败: {e}")
        return None

    def save_to_cache(self, ts_code, df):
        """保存数据到缓存"""
        cache_path = os.path.join(self.cache_dir, f"{ts_code}.parquet")  # 使用 Parquet 文件
        try:
            df.to_parquet(cache_path, index=False)  # 保存为 Parquet 文件
            logging.info(f"股票数据已保存到缓存: {ts_code}")
        except Exception as e:
            logging.error(f"保存缓存文件失败: {e}")

    def get_stock_data(self, ts_code):
        """带缓存的股票数据获取"""
        # 优先使用缓存
        cached_df = self.get_cached_data(ts_code)
        
        if cached_df is not None:
            # 校验缓存数据的最近一个交易日是否是最新的交易日
            cached_recent_trading_day = cached_df['trade_date'].max()
            recent_trading_day = self.recent_trading_day
            
            if cached_recent_trading_day == recent_trading_day:
                logging.info(f"股票代码 {ts_code} 的缓存数据是最新的，无需请求接口")
                return cached_df
            else:
                logging.info(f"股票代码 {ts_code} 的缓存数据不是最新的，更新缓存数据")

        # 获取最新30天数据
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
        
        try:
            time.sleep(0.25)  # 添加延迟以确保每分钟最多访问200次
            logging.info(f"从接口获取最新数据中, 冷却0.25s")
            df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if not df.empty:
                self.save_to_cache(ts_code, df)
                logging.info(f"股票代码 {ts_code} 的数据获取成功并已缓存")
            else:
                logging.warning(f"股票代码 {ts_code} 的数据为空")
            
            return df
        except Exception as e:
            logging.error(f"获取{ts_code}数据失败: {str(e)}")
            return pd.DataFrame()

    def check_conditions(self, df):
        """策略条件检查"""
        results = []
        
        # 数据校验
        if len(df) < 30:
            logging.warning("数据不足30天")
            return results

        # 按日期排序并截取最新30天
        df = df.sort_values('trade_date')
        latest_30 = df.iloc[-30:].copy()  # 取最后30条 创建副本
        latest_30.loc[:, 'ma5'] = latest_30['close'].rolling(5).mean() # 计算5日均线
        latest_30.loc[:, 'vol5'] = latest_30['vol'].rolling(5).mean() # 计算5日均量
        
        # 条件1：计算30天内最高回撤
        max_high = latest_30['high'].max()
        min_low = latest_30['low'].min()
        drawdown = (max_high - min_low) / max_high
        last_close = latest_30.iloc[-1]['close']
        last_vol = latest_30.iloc[-1]['vol']
        
        # 条件2：计算5日均线
        current_ma5 = latest_30['ma5'].iloc[-1]  # 最后一天的5日均线值

        current_vol5 = latest_30['vol5'].iloc[-1]  # 最后一天的5日均成交量
        
        # 条件3：计算当日涨幅
        prev_close = latest_30.iloc[-2]['close']  # 前一日收盘价
        pct_change = (last_close - prev_close) / prev_close

        if all([
            0.07 <= drawdown <= 0.35,       # 近30交易日回撤7%-35%
            last_close > current_ma5,       # 收盘价在5日线上
            # min_low > current_ma5,         # 最低价在5日线上
            last_vol > current_vol5,        # 成交量大于5日均量
            0.00 <= pct_change <= 0.05      # 最近一交易日涨幅0%-5%
        ]):
            results.append({
                'date':  latest_30.iloc[-1]['trade_date'],
                'drawdown': round(drawdown * 100, 1),
                'pct_change': round(pct_change * 100, 1)
            })
            logging.info(f"找到符合条件的信号: {results[-1]}")
        return results
    def run_screening(self):
        """执行筛选"""
        stock_basic = self.get_stock_basic()  # 获取所有股票的基本信息
        stock_codes = self.get_small_cap_stocks().split(',')
        results = []
        
        # 进度窗口
        progress = tk.Toplevel(self.window)
        progress.title("处理进度")
        tk.Label(progress, text=f"正在遍历 {len(stock_codes)} 只股票的交易数据...").pack()
        pb = ttk.Progressbar(progress, length=300, maximum=len(stock_codes))
        pb.pack(padx=10, pady=5)

        for idx, code in enumerate(stock_codes):
            logging.info(f"开始处理股票代码: {code}")
            pb['value'] = idx + 1
            progress.update()
            self.window.update()  # 确保主窗口也更新
            
            try:
                df = self.get_stock_data(code)
                if df.empty:
                    logging.warning(f"股票代码 {code} 的数据为空")
                    continue

                logging.info(f"股票代码 {code} 的数据获取成功")
                        # 获取所有股票的基本信息
                stock_name = stock_basic.loc[stock_basic['ts_code'] == code, 'name'].values[0]
                signals = self.check_conditions(df)
                
                for sig in signals:
                    results.append((code, stock_name, sig['date'], sig['drawdown'], sig['pct_change']))
                    logging.info(f"找到符合条件的信号: {sig}")
            except Exception as e:
                logging.error(f"处理股票代码 {code} 时出错: {str(e)}")
        
        time.sleep(0.1)  # 控制请求频率

        progress.destroy()
        self.update_results(results)
        logging.info(f"完成筛选，找到 {len(results)} 条符合条件的记录")
        messagebox.showinfo("完成", f"找到{len(results)}条符合条件记录")

    def update_results(self, data):
        """更新结果列表"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in data:
            self.tree.insert('', 'end', values=row)

    def export_results(self):
        """导出结果"""
        df = pd.DataFrame([self.tree.item(i)['values'] for i in self.tree.get_children()],
                         columns=['代码','名称','日期','回撤率','次日涨幅'])
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"筛选结果_{timestamp}.csv"
        df.to_csv(filename, index=False)
        messagebox.showinfo("导出成功", "结果已保存为 筛选结果.csv")

if __name__ == "__main__":
    app = StockScreener()
    app.window.mainloop()