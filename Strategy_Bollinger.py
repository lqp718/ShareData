import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime
from pymongo import MongoClient
import warnings
import optuna

warnings.filterwarnings('ignore')

class BalancedBollingerRSIStrategy(bt.Strategy):
    params = (
        # 核心参数
        ('min_buy_score', 0.4),        # 最低买入分数阈值
        ('rsi_oversold', 30),          # 标准超卖阈值
        ('bb_period', 20),
        ('bb_dev', 2.0),               # 标准布林带宽度
        
        # 风险管理
        ('stop_loss_pct', 0.12),           
        ('max_drawdown_threshold', 0.05),  # 比固定止损更敏感
        ('position_size_base', 0.90),      # 基础仓位
        
        # 移动止盈
        ('trailing_stop_trigger', 0.05),   # 收益5%激活
        ('trailing_stop_pct', 0.03),       # 回撤3%止损
        
        # 趋势过滤
        ('ma_fast', 5),
        ('ma_slow', 30),
        
        # 波动率控制
        ('use_atr_filter', True),
        ('atr_period', 14),
        ('max_volatility_ratio', 0.08),    # 波动率>6%不交易
        
        # 动态仓位（可选）
        ('use_dynamic_position', False),   # 默认关闭，可开启
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
        self.ma200 = bt.indicators.SMA(self.datas[0], period=200)
        
        # 成交量 & 波动率
        self.volume_sma = bt.indicators.SMA(self.datas[0].volume, period=20)
        self.atr = bt.indicators.ATR(self.datas[0], period=self.params.atr_period)
        
        # 跟踪变量
        self.entry_price = None
        self.peak_price = None
        self.stop_loss_level = None
        self.trailing_stop_level = None
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

    def has_core_conditions(self):
        """核心条件：价格触及布林下轨 + RSI 超卖"""
        price_at_lower = self.dataclose[0] <= self.bb.lines.bot[0]
        rsi_low = self.rsi[0] < self.params.rsi_oversold  # 如 35
        volume_ok = self.datas[0].volume[0] > self.volume_sma[0] * 0.3  # 非零成交
        return price_at_lower and rsi_low and volume_ok


    def calculate_buy_score(self):
        score = 0.0
        max_score = 0.0

        # 1. 趋势位置加分：在 MA200 上方 +0.5，下方不扣分
        max_score += 0.5
        if len(self.ma200) >= 200 and self.dataclose[0] > self.ma200[0]:
            score += 0.5

        # 2. 波动率适中加分：ATR/Close 在 2%~8% 之间最理想
        max_score += 0.2
        if len(self.atr) >= self.params.atr_period:
            vol_ratio = self.atr[0] / self.dataclose[0]
            if 0.02 <= vol_ratio <= 0.08:
                score += 0.2
            elif vol_ratio > 0.15:
                # 极高波动不加分也不减分（恐慌可能是机会）
                pass

        # 3. 成交量放大加分：当日量 > 20日均量 * 0.8
        max_score += 0.2
        if len(self.volume_sma) >= 20:
            if self.datas[0].volume[0] > self.volume_sma[0] * 0.8:
                score += 0.2

        # 4. RSI 越低分越高（30以下满分，35以上0分）
        max_score += 0.3
        rsi = self.rsi[0]
        if rsi <= 30:
            score += 0.3
        elif rsi < 35:
            score += 0.3 * (35 - rsi) / 5  # 线性插值

        return score / max_score if max_score > 0 else 0.0

    def calculate_position_size(self, cash):
        """动态仓位：波动率越高，仓位越低"""
        if not self.params.use_dynamic_position:
            return int((cash * self.params.position_size_base) / self.dataclose[0])
        
        if len(self.atr) < self.params.atr_period:
            vol_factor = 1.0
        else:
            volatility_ratio = self.atr[0] / self.dataclose[0]
            vol_factor = max(0.5, min(1.0, 1.0 - (volatility_ratio / self.params.max_volatility_ratio)))
        
        size = int((cash * self.params.position_size_base * vol_factor) / self.dataclose[0])
        return (size // 100) * 100

    def is_bounce_possible(self):
        """价格不能连续N天下跌"""
        closes = [self.dataclose[i] for i in range(-3, 1)]  # 最近4根K线收盘价
        # 如果最近3天都在跌，跳过
        declines = sum(1 for i in range(1, len(closes)) if closes[i] < closes[i-1])
        return declines < 3

    def should_take_profit(self, current_return):
        """精简止盈：只保留25%+超买条件"""
        if not self.position:
            return False, ""
            
        current_rsi = self.rsi[0]
        if current_return > 0.25 and current_rsi > 75:
            return True, "收益+超买止盈"
            
        return False, ""

    def should_buy(self):
        # 第一层：核心条件必须满足
        if not self.has_core_conditions():
            return False

        # 第二层：计算信心分数
        buy_score = self.calculate_buy_score()

        # 第三层：动态阈值（可参数化）
        min_score = self.params.min_buy_score  # 比如 0.4

        if buy_score >= min_score:
            self.log(f"✅ 买入信号: Score={buy_score:.2f} "
                     f"(RSI={self.rsi[0]:.1f}, Close={self.dataclose[0]:.2f})")
            return True
        else:
            # self.log(f"⚠️ 潜在信号但分数不足: Score={buy_score:.2f}")
            return False

    def next(self):
        if self.order:
            return

        # 确保指标就绪
        min_len = max(15, self.params.bb_period + 1, self.params.ma_slow, self.params.atr_period)
        if len(self) < min_len:
            return

        if not self.position:
            if self.should_buy():
                cash = self.broker.getcash()
                size = self.calculate_position_size(cash)
                size = (size // 100) * 100  # A股100股整数倍

                if size > 0:
                    self.log(f'BUY: Close={self.dataclose[0]:.2f}, RSI={self.rsi[0]:.1f}, '
                           f'BB Lower={self.bb.lines.bot[0]:.2f}')
                    self.order = self.buy(size=size)
                    self.stop_loss_level = self.dataclose[0] * (1 - self.params.stop_loss_pct)
                
        else:
            self.peak_price = max(self.peak_price, self.dataclose[0])
            current_return = (self.dataclose[0] - self.entry_price) / self.entry_price
            current_drawdown = (self.peak_price - self.dataclose[0]) / self.peak_price
            
            # 移动止盈
            if current_return >= self.params.trailing_stop_trigger:
                new_trailing_stop = self.peak_price * (1 - self.params.trailing_stop_pct)
                if self.trailing_stop_level is None or new_trailing_stop > self.trailing_stop_level:
                    self.trailing_stop_level = new_trailing_stop
                    self.log(f"移动止盈激活/更新: 收益率{current_return:+.2%}, 止盈位={self.trailing_stop_level:.2f}")

            sell_signal = False
            reason = ""
            
            # 条件1: 主动止盈
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


# ==================== 数据加载 & 回测运行 ====================
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
        k_data = doc.get(f'k_data_{price_type}', {}) if price_type != 'normal' else doc.get('k_data', {})
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
    return bt.feeds.PandasData(
        dataname=df,
        datetime=None,
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        openinterest=-1
    )

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
            start_date='2015-01-01',
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
        cerebro.broker.setcommission(commission=0.000182)  # 万1.82
        cerebro.broker.set_slippage_perc(0.001)           # 0.1%滑点
        
        # 分析器
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.02)
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        cerebro.addobserver(bt.observers.Value)
        cerebro.addobserver(bt.observers.BuySell)
        
        print(f'初始资金: {initial_cash:,.2f}')
        print(f'数据时间范围: {df.index.min()} 到 {df.index.max()}')
        
        results = cerebro.run()
        strat = results[0]
        
        final_value = cerebro.broker.getvalue()
        print(f'\n最终资金: {final_value:,.2f}')
        
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


# ==================== Optuna 优化（目标：夏普比率）====================
def objective(trial):
    # 参数搜索空间
    rsi_oversold = trial.suggest_int('rsi_oversold', 25, 35)
    bb_dev = trial.suggest_float('bb_dev', 1.8, 2.3)
    trailing_stop_trigger = trial.suggest_float('trailing_stop_trigger', 0.03, 0.08)
    trailing_stop_pct = trial.suggest_float('trailing_stop_pct', 0.02, 0.05)
    stop_loss_pct = trial.suggest_float('stop_loss_pct', 0.08, 0.15)
    max_drawdown_threshold = trial.suggest_float('max_drawdown_threshold', 0.03, 0.07)
    
    # 加载数据（复用函数）
    client = MongoClient("mongodb://localhost:27017/")
    db = client["my_stock"]
    collection = db["sz002371"]
    df = load_data_from_mongodb(collection, '2015-01-01', '2025-11-08', 'qfq')
    client.close()
    
    # 运行回测
    cerebro = bt.Cerebro()
    cerebro.addstrategy(
        BalancedBollingerRSIStrategy,
        rsi_oversold=rsi_oversold,
        bb_dev=bb_dev,
        trailing_stop_trigger=trailing_stop_trigger,
        trailing_stop_pct=trailing_stop_pct,
        stop_loss_pct=stop_loss_pct,
        max_drawdown_threshold=max_drawdown_threshold,
        ma_fast=5,
        ma_slow=30,
        use_atr_filter=True,
        use_dynamic_position=False  # 优化时关闭动态仓位
    )
    cerebro.adddata(create_backtrader_data(df))
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(0.000182)
    cerebro.broker.set_slippage_perc(0.001)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    
    try:
        results = cerebro.run()
        sharpe = results[0].analyzers.sharpe.get_analysis().get('sharperatio', -1)
        return sharpe if sharpe is not None else -1
    except:
        return -1

if __name__ == '__main__':
    # 运行基础回测
    run_backtest_with_mongodb()
    
    # 如需自动优化，取消注释以下代码：
    #study = optuna.create_study(direction='maximize')
    #study.optimize(objective, n_trials=50)
    #print("最佳参数:", study.best_params)