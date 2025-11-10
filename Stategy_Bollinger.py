import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime
from pymongo import MongoClient
import warnings
warnings.filterwarnings('ignore')

class BalancedBollingerRSIStrategy(bt.Strategy):
    params = (
        # 核心参数 - 轻微放宽以增加交易机会
        ('rsi_oversold', 32),      # 从30放宽到32
        ('rsi_overbought', 70),    
        ('bb_period', 20),
        ('bb_dev', 2),
        
        # 风险管理 - 保持相对严格
        ('stop_loss_pct', 0.08),           
        ('max_drawdown_threshold', 0.10),  
        ('position_size', 0.90),           # 稍微降低仓位到90%
        
        # 移动止盈 - 优化参数
        ('trailing_stop_trigger', 0.12),   # 从15%降到12%，更早保护利润
        ('trailing_stop_pct', 0.06),       # 从8%降到6%，收紧移动止盈
        
        # 新增：简单趋势过滤
        ('ma_fast', 10),
        ('ma_slow', 20),
        
        # 新增：波动率过滤
        ('min_volume_multiplier', 0.7),    # 成交量过滤
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        
        # 核心指标
        self.rsi = bt.indicators.RSI(self.datas[0], period=14)
        self.bb = bt.indicators.BollingerBands(
            self.datas[0], 
            period=self.params.bb_period,
            devfactor=self.params.bb_dev
        )
        
        # 趋势指标
        self.ma_fast = bt.indicators.SMA(self.datas[0], period=self.params.ma_fast)
        self.ma_slow = bt.indicators.SMA(self.datas[0], period=self.params.ma_slow)
        
        # 新增：成交量指标
        self.volume_sma = bt.indicators.SMA(self.datas[0].volume, period=20)
        
        # 跟踪变量
        self.entry_price = None
        self.peak_price = None
        self.stop_loss_level = None
        self.trailing_stop_level = None  # 新增：移动止盈位
        self.order = None
        self.trade_count = 0
        self.entry_bar = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
                self.entry_price = order.executed.price
                self.peak_price = order.executed.price
                self.trade_count += 1
                self.entry_bar = len(self)
                # 重置移动止盈
                self.trailing_stop_level = None
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
                self.trailing_stop_level = None
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            
        self.order = None

    def is_trend_positive(self):

        if len(self.ma_fast) < 5 or len(self.ma_slow) < 5:
            return True

        ma_condition = self.ma_fast[0] > self.ma_slow[0] * 0.90
        price_condition = self.dataclose[0] > self.ma_slow[0] * 0.88
        
        return ma_condition or price_condition

    def is_volume_adequate(self):
        """成交量过滤 - 避免在极度缩量时买入"""
        if len(self.volume_sma) < 5:
            return True
            
        return self.datas[0].volume[0] > self.volume_sma[0] * self.params.min_volume_multiplier

    def should_take_profit(self, current_return):
        """分级止盈条件"""
        if not self.position:
            return False
            
        current_rsi = self.rsi[0]
        price_at_upper = self.dataclose[0] >= self.bb.lines.top[0] * 0.98
        
        # 分级止盈策略
        if current_return > 0.60 and current_rsi > 75:
            return True, "超高收益止盈"
        elif current_return > 0.40 and current_rsi > 70 and price_at_upper:
            return True, "高收益+技术指标止盈"
        elif current_return > 0.25 and current_rsi > 75:
            return True, "收益+超买止盈"
            
        return False, ""

    def next(self):
        if self.order:
            return

        # 确保指标已就绪
        if (len(self.rsi) < 15 or len(self.bb.lines.bot) < 21 or 
            len(self.volume_sma) < 5):
            return

        if not self.position:
            # 买入条件 - 基于原始成功策略，增加简单趋势过滤
            price_at_lower = self.dataclose[0] <= self.bb.lines.bot[0]
            rsi_low = self.rsi[0] < self.params.rsi_oversold
            trend_ok = self.is_trend_positive()
            volume_ok = self.is_volume_adequate()
            
            if price_at_lower and rsi_low and trend_ok and volume_ok:
                cash = self.broker.getcash()
                size = int((cash * self.params.position_size) / self.dataclose[0])
                size = (size // 100) * 100

                if size > 0:
                    self.log(f'BUY: Close={self.dataclose[0]:.2f}, RSI={self.rsi[0]:.1f}, '
                           f'BB Lower={self.bb.lines.bot[0]:.2f}, Volume_OK={volume_ok}')
                    self.order = self.buy(size=size)
                    # 设置止损位
                    self.stop_loss_level = self.dataclose[0] * (1 - self.params.stop_loss_pct)
                
        else:
            # 更新最高价
            self.peak_price = max(self.peak_price, self.dataclose[0])
            
            current_return = (self.dataclose[0] - self.entry_price) / self.entry_price
            current_drawdown = (self.peak_price - self.dataclose[0]) / self.peak_price
            
            # 移动止盈逻辑
            if current_return >= self.params.trailing_stop_trigger:
                # 计算移动止盈位
                new_trailing_stop = self.peak_price * (1 - self.params.trailing_stop_pct)
                
                # 如果是第一次激活或者需要更新到更高的位置
                if self.trailing_stop_level is None or new_trailing_stop > self.trailing_stop_level:
                    self.trailing_stop_level = new_trailing_stop
                    self.log(f"移动止盈激活/更新: 当前收益率{current_return:+.2%}, 止盈位={self.trailing_stop_level:.2f}")

            # 卖出条件
            sell_signal = False
            reason = ""
            
            # 条件1: 主动止盈（分级）
            take_profit, profit_reason = self.should_take_profit(current_return)
            if take_profit:
                sell_signal = True
                reason = f"主动止盈: {profit_reason}, 收益率{current_return:+.2%}, RSI={self.rsi[0]:.1f}"
            
            # 条件2: 移动止盈触发
            elif (self.trailing_stop_level is not None and 
                  self.dataclose[0] <= self.trailing_stop_level):
                sell_signal = True
                reason = f"移动止盈: 价格{self.dataclose[0]:.2f} ≤ 止盈位{self.trailing_stop_level:.2f}, 收益率{current_return:+.2%}"
            
            # 条件3: 回撤止损
            elif current_drawdown >= self.params.max_drawdown_threshold:
                sell_signal = True
                reason = f"回撤止损: {current_drawdown:.2%}, 收益率{current_return:+.2%}"
            
            # 条件4: 固定止损
            elif self.dataclose[0] <= self.stop_loss_level:
                sell_signal = True
                reason = f"止损触发: {self.dataclose[0]:.2f}, 收益率{current_return:+.2%}"

            if sell_signal:
                self.log(f'SELL: {reason}')
                self.order = self.sell(size=self.position.size)

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}: {txt}')

    def stop(self):
        print(f"\n策略回测结束")
        print(f"总交易次数: {self.trade_count}")

def load_data_from_mongodb(collection, start_date=None, end_date=None, price_type='qfq'):
    query = {}
    if start_date or end_date:
        query['date'] = {}
        if start_date:
            query['date']['$gte'] = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            query['date']['$lte'] = datetime.strptime(end_date, '%Y-%m-%d')
    
    cursor = collection.find(query).sort('date', 1)
    data_list = []
    for doc in cursor:
        if price_type == 'normal':
            k_data = doc.get('k_data', {})
        elif price_type == 'qfq':
            k_data = doc.get('k_data_qfq', {})
        elif price_type == 'hfq':
            k_data = doc.get('k_data_hfq', {})
        else:
            k_data = doc.get('k_data_qfq', {})
        
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
    
    df = pd.DataFrame(data_list)
    df.set_index('date', inplace=True)
    df = df[(df['volume'] > 0) & (df['close'] > 0)]
    print(f"加载数据: {len(df)} 条记录, 时间范围: {df.index.min()} 到 {df.index.max()}")
    return df

def create_backtrader_data(df):
    data = bt.feeds.PandasData(
        dataname=df,
        datetime=None,
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        openinterest=-1
    )
    return data

def run_backtest_with_mongodb():
    MONGODB_URI = "mongodb://localhost:27017/"
    DATABASE_NAME = "my_stock"
    COLLECTION_NAME = "sz000001"
    
    try:
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        print("成功连接到MongoDB")
        
        df = load_data_from_mongodb(
            collection=collection,
            start_date='2020-01-01',
            end_date='2025-11-08',
            price_type='qfq'
        )
        
        if df is None or df.empty:
            print("没有加载到数据，请检查数据库连接和查询条件")
            return
        
        cerebro = bt.Cerebro()
        cerebro.addstrategy(BalancedBollingerRSIStrategy)
        data = create_backtrader_data(df)
        cerebro.adddata(data)
        
        initial_cash = 100000.0
        cerebro.broker.setcash(initial_cash)
        cerebro.broker.setcommission(commission=0.000182)
        cerebro.broker.set_slippage_perc(0.001)
        
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn')
        cerebro.addobserver(bt.observers.Value)
        cerebro.addobserver(bt.observers.DrawDown)
        cerebro.addobserver(bt.observers.BuySell)
        
        print(f'初始资金: {initial_cash:,.2f}')
        print(f'数据时间范围: {df.index.min()} 到 {df.index.max()}')
        print(f'数据条数: {len(df)}')
        
        print("正在运行回测...")
        results = cerebro.run()
        strat = results[0]
        
        final_value = cerebro.broker.getvalue()
        print(f'最终资金: {final_value:,.2f}')
        
        print("\n" + "="*50)
        print("回测结果汇总")
        print("="*50)
        
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
        
        sharpe_analysis = strat.analyzers.sharpe.get_analysis()
        if sharpe_analysis and 'sharperatio' in sharpe_analysis:
            sharpe_ratio = sharpe_analysis['sharperatio']
            if sharpe_ratio is not None:
                print(f"夏普比率: {sharpe_ratio:.2f}")
            else:
                print("夏普比率: 无数据")
        else:
            print("夏普比率: 无数据")
        
        drawdown_analysis = strat.analyzers.drawdown.get_analysis()
        if drawdown_analysis and 'max' in drawdown_analysis:
            max_drawdown = drawdown_analysis['max'].get('drawdown', 0)
            print(f"最大回撤: {max_drawdown}%")
        else:
            print("最大回撤: 无数据")
        
        try:
            trade_analysis = strat.analyzers.trades.get_analysis()
            if hasattr(trade_analysis, 'total') and hasattr(trade_analysis.total, 'closed'):
                total_closed = trade_analysis.total.closed
                if total_closed > 0:
                    print(f"\n交易统计:")
                    print(f"总交易次数: {total_closed}")
                    print(f"盈利交易: {trade_analysis.won.total}")
                    print(f"亏损交易: {trade_analysis.lost.total}")
                    win_rate = trade_analysis.won.total / total_closed
                    print(f"胜率: {win_rate:.2%}")
                    
                    if hasattr(trade_analysis, 'pnl') and hasattr(trade_analysis.pnl, 'net'):
                        avg_profit = trade_analysis.pnl.net.average
                        print(f"平均每笔收益: {avg_profit:.2f}")
                        
                    if hasattr(trade_analysis, 'won') and hasattr(trade_analysis.won, 'pnl'):
                        avg_win = trade_analysis.won.pnl.average
                        print(f"平均盈利: {avg_win:.2f}")
                    if hasattr(trade_analysis, 'lost') and hasattr(trade_analysis.lost, 'pnl'):
                        avg_loss = trade_analysis.lost.pnl.average
                        print(f"平均亏损: {avg_loss:.2f}")
                        if avg_loss != 0:
                            profit_factor = abs(avg_win / avg_loss)
                            print(f"盈亏比: {profit_factor:.2f}")
                else:
                    print(f"\n总交易次数: {strat.trade_count}")
                    print("没有产生完整交易")
            else:
                print(f"\n总交易次数: {strat.trade_count}")
                print("交易分析数据不完整")
        except Exception as e:
            print(f"\n交易统计错误: {e}")
            print(f"策略交易计数: {strat.trade_count}")
        
        if strat.trade_count > 0:
            print("\n生成回测图表...")
            cerebro.plot(style='candlestick', volume=False)
        else:
            print("\n无交易，跳过图表生成")
        
    except Exception as e:
        print(f"回测过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'client' in locals():
            client.close()


if __name__ == '__main__':
    run_backtest_with_mongodb()