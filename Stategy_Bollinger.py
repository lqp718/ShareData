import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime
from pymongo import MongoClient
import warnings
warnings.filterwarnings('ignore')

class BollingerRSIStrategy(bt.Strategy):
    params = (
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
        ('bb_period', 20),
        ('bb_dev', 2),
        ('stop_loss_pct', 0.08),
        ('max_drawdown_threshold', 0.10),
        ('position_size', 0.90),
    )
    
    def __init__(self):
        # 保存数据引用
        self.dataclose = self.datas[0].close
        
        # 计算技术指标
        self.rsi = bt.indicators.RSI(self.datas[0], period=14)
        self.bb = bt.indicators.BollingerBands(self.datas[0], 
                                             period=self.params.bb_period,
                                             devfactor=self.params.bb_dev)
        
        # 跟踪变量
        self.entry_price = None
        self.peak_price = None
        self.stop_loss_level = None
        self.order = None
        self.trade_count = 0  # 交易计数
        
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
                self.entry_price = order.executed.price
                self.peak_price = order.executed.price
                self.stop_loss_level = self.entry_price * (1 - self.params.stop_loss_pct)
                self.trade_count += 1
            elif order.issell():
                if self.entry_price:
                    trade_return = (order.executed.price - self.entry_price) / self.entry_price
                    trade_duration = len(self) - self.entry_bar
                    self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, '
                           f'收益率: {trade_return:+.2%}, 持仓周期: {trade_duration}天')
                else:
                    self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')
                
                self.entry_price = None
                self.peak_price = None
                self.stop_loss_level = None
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            
        self.order = None

    def next(self):

        # 如果有订单未完成，跳过
        if self.order:
            return
            
        # 检查是否持仓
        if not self.position:
            # 无持仓，检查买入条件
            # 确保指标已经计算完成（有足够的历史数据）
            if len(self.rsi) < 15 or len(self.bb.lines.bot) < 21:
                return
                
            price_at_lower = (self.dataclose[0] <= self.bb.lines.bot[0])
            rsi_low = (self.rsi[0] < self.params.rsi_oversold)
            
            if price_at_lower and rsi_low:
                cash = self.broker.getcash()
                size = int((cash * self.params.position_size) / self.dataclose[0])
                size = (size // 100) * 100  # A股手数限制

                if size > 0:
                    self.log(f'BUY SIGNAL: Close={self.dataclose[0]:.2f}, 买入{size}股')
                    self.order = self.buy(size=size)
                    self.entry_bar = len(self)
                
        else:
            # 有持仓，更新最高价
            self.peak_price = max(self.peak_price, self.dataclose[0])
            
            # 计算当前回撤
            current_drawdown = (self.peak_price - self.dataclose[0]) / self.peak_price
            
            # 计算当前浮动收益率
            if self.entry_price:
                current_return = (self.dataclose[0] - self.entry_price) / self.entry_price
            else:
                current_return = 0
            
            # 检查卖出条件
            sell_signal = False
            reason = ""
            
            if current_drawdown >= self.params.max_drawdown_threshold:
                sell_signal = True
                reason = f"Max Drawdown: {current_drawdown:.2%}, 当前收盘价：{self.dataclose[0]}, 当前收益率: {current_return:+.2%}"
            elif self.dataclose[0] <= self.stop_loss_level:
                sell_signal = True
                reason = f"Stop Loss: {self.dataclose[0]:.2f}, 当前收盘价：{self.dataclose[0]}, 当前收益率: {current_return:+.2%}"
                
            if sell_signal:
                self.log(f'SELL SIGNAL: {reason}')
                self.order = self.sell(size=self.position.size)
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}: {txt}')

    def stop(self):
        """回测结束时调用"""
        print(f"\n策略回测结束")
        print(f"总交易次数: {self.trade_count}")

def load_data_from_mongodb(collection, start_date=None, end_date=None, price_type='qfq'):
    """
    从MongoDB加载股票数据
    
    Parameters:
    -----------
    collection: MongoDB集合
    start_date: 开始日期，格式 'YYYY-MM-DD'
    end_date: 结束日期，格式 'YYYY-MM-DD'
    price_type: 价格类型 
        'normal' - 不复权
        'qfq' - 前复权 (推荐)
        'hfq' - 后复权
    """
    
    # 构建查询条件
    query = {}

    if start_date or end_date:
        query['date'] = {}
        if start_date:
            query['date']['$gte'] = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            query['date']['$lte'] = datetime.strptime(end_date, '%Y-%m-%d')
    
    # 执行查询
    cursor = collection.find(query).sort('date', 1)
    
    data_list = []
    for doc in cursor:
        # 根据价格类型选择数据源
        if price_type == 'normal':
            k_data = doc.get('k_data', {})
        elif price_type == 'qfq':
            k_data = doc.get('k_data_qfq', {})
        elif price_type == 'hfq':
            k_data = doc.get('k_data_hfq', {})
        else:
            k_data = doc.get('k_data_qfq', {})  # 默认使用前复权
        
        # 确保数据完整
        if not k_data or 'open' not in k_data:
            continue
            
        date = doc['date']
        data_list.append({
            'date': date,
            'open': k_data.get('open', 0),
            'high': k_data.get('high', 0),
            'low': k_data.get('low', 0),
            'close': k_data.get('close', 0),
            'volume': k_data.get('volume', 0),
            'amount': k_data.get('amount', 0),
            'outstanding_share': k_data.get('outstanding_share', 0),
            'turnover': k_data.get('turnover', 0)
        })
    
    if not data_list:
        print("未找到数据，请检查查询条件")
        return None
    
    # 转换为DataFrame
    df = pd.DataFrame(data_list)
    df.set_index('date', inplace=True)
    
    # 数据清洗
    df = df[(df['volume'] > 0) & (df['close'] > 0)]
    
    print(f"加载数据: {len(df)} 条记录, 时间范围: {df.index.min()} 到 {df.index.max()}")
    return df

def create_backtrader_data(df):
    """将DataFrame转换为Backtrader数据格式"""
    data = bt.feeds.PandasData(
        dataname=df,
        datetime=None,  # 使用index作为datetime
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        openinterest=-1  # 没有持仓量数据
    )
    return data

def run_backtest_with_mongodb():
    # MongoDB连接配置
    MONGODB_URI = "mongodb://localhost:27017/"  # 修改为你的MongoDB连接字符串
    DATABASE_NAME = "my_stock"  # 修改为你的数据库名
    COLLECTION_NAME = "sz000001"  # 修改为你的集合名
    
    try:
        # 连接MongoDB
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        print("成功连接到MongoDB")
        
        # 加载数据 - 修改这些参数来测试不同的股票和时间范围
        df = load_data_from_mongodb(
            collection=collection,
            start_date='2015-01-01',
            end_date='2025-11-08',
            price_type='qfq'  # 推荐使用前复权
        )
        
        if df is None or df.empty:
            print("没有加载到数据，请检查数据库连接和查询条件")
            return
        
        # 创建回测引擎
        cerebro = bt.Cerebro()
        
        # 添加策略
        cerebro.addstrategy(BollingerRSIStrategy)
        
        # 添加数据
        data = create_backtrader_data(df)
        cerebro.adddata(data)
        
        # 设置初始资金
        initial_cash = 50000.0
        cerebro.broker.setcash(initial_cash)
        
        # 设置手续费
        cerebro.broker.setcommission(commission=0.000182)
        cerebro.broker.set_slippage_perc(0.001)
        
        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn')
        cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
        
        # 添加观察器
        cerebro.addobserver(bt.observers.Value)
        cerebro.addobserver(bt.observers.DrawDown)
        cerebro.addobserver(bt.observers.BuySell)  # 显示买卖点
        
        print(f'初始资金: {initial_cash:,.2f}')
        print(f'数据时间范围: {df.index.min()} 到 {df.index.max()}')
        print(f'数据条数: {len(df)}')
        
        # 运行回测
        print("正在运行回测...")
        results = cerebro.run()
        strat = results[0]
        
        # 获取最终资金
        final_value = cerebro.broker.getvalue()
        print(f'最终资金: {final_value:,.2f}')
        
        # 安全地获取分析器结果
        print("\n" + "="*50)
        print("回测结果汇总")
        print("="*50)
        
        # 总收益率
        returns_analysis = strat.analyzers.returns.get_analysis()
        if returns_analysis:
            total_return = returns_analysis.get('rtot', 0)
            annual_return = returns_analysis.get('rnorm', 0)
            print(f"策略总收益率: {total_return:.2%}")
            print(f"年化收益率: {annual_return:.2%}")
        else:
            total_return = (final_value - initial_cash) / initial_cash
            print(f"策略总收益率: {total_return:.2%}")
            print("年化收益率: 无完整年度数据")
        
        # 夏普比率
        sharpe_analysis = strat.analyzers.sharpe.get_analysis()
        if sharpe_analysis and 'sharperatio' in sharpe_analysis:
            sharpe_ratio = sharpe_analysis['sharperatio']
            if sharpe_ratio is not None:
                print(f"夏普比率: {sharpe_ratio:.2f}")
            else:
                print(f"夏普比率: is None")
        else:
            print("夏普比率: 无数据")
        
        # 最大回撤
        drawdown_analysis = strat.analyzers.drawdown.get_analysis()
        if drawdown_analysis and 'max' in drawdown_analysis:
            max_drawdown = drawdown_analysis['max'].get('drawdown', 0)
            print(f"最大回撤: {max_drawdown}%")
        else:
            print("最大回撤: 无数据")
        
        # 交易统计
        trade_analysis = strat.analyzers.trades.get_analysis()
        if trade_analysis and hasattr(trade_analysis, 'total') and trade_analysis.total.closed > 0:
            print(f"\n交易统计:")
            print(f"总交易次数: {trade_analysis.total.closed}")
            print(f"盈利交易: {trade_analysis.won.total}")
            print(f"亏损交易: {trade_analysis.lost.total}")
            win_rate = trade_analysis.won.total / trade_analysis.total.closed
            print(f"胜率: {win_rate:.2%}")
            
            # 平均盈亏
            if 'pnl' in trade_analysis and 'net' in trade_analysis.pnl:
                avg_profit = trade_analysis.pnl.net.average
                print(f"平均每笔收益: {avg_profit:.2f}")
                
            # 盈亏统计
            if hasattr(trade_analysis, 'won'):
                avg_win = trade_analysis.won.pnl.average if trade_analysis.won.total > 0 else 0
                avg_loss = trade_analysis.lost.pnl.average if trade_analysis.lost.total > 0 else 0
                print(f"平均盈利: {avg_win:.2f}")
                print(f"平均亏损: {avg_loss:.2f}")
                if avg_loss != 0:
                    profit_factor = abs(avg_win / avg_loss)
                    print(f"盈亏比: {profit_factor:.2f}")
        else:
            print(f"\n总交易次数: {strat.trade_count}")
            print("没有产生完整交易，可能原因:")
            print("- 数据波动性不足")
            print("- 策略参数过于严格")
            print("- 数据时间范围太短")
        
        # 绘制图表
        print("\n生成回测图表...")
        cerebro.plot(style='candlestick', volume=False)
        
    except Exception as e:
        print(f"回测过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭数据库连接
        if 'client' in locals():
            client.close()


if __name__ == '__main__':
    run_backtest_with_mongodb()