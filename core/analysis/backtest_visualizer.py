import matplotlib
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd


class BacktestVisualizer:
    """AdvancedBacktestEngine 结果可视化工具"""

    def __init__(self):
        self._setup_chinese_font()

    def _setup_chinese_font(self):
        """设置matplotlib支持中文字体"""
        # 使用系统默认中文字体
        plt.rcParams["font.family"] = [
            "Arial Unicode MS",
            "SimHei",
            "Microsoft YaHei",
            "sans-serif",
        ]
        # 解决负号显示问题
        matplotlib.rcParams["axes.unicode_minus"] = False

    def visualize_backtest(
        self, backtest_result, kl_data, title=None, days=300, show=True, save_path=None
    ):
        """可视化回测结果

        Args:
            backtest_result: AdvancedBacktestEngine的回测结果
            kl_data: 原始K线数据
            title: 图表标题
            days: 展示最近的天数，默认300天，None表示展示所有数据
            show: 是否立即显示图表
            save_path: 保存图表的路径，None表示不保存

        Returns:
            matplotlib figure对象
        """
        # 转换K线数据为DataFrame，并设置日期索引
        df = pd.DataFrame(kl_data)

        # 添加索引列，便于控制x轴显示
        df["index"] = np.arange(0, len(df))
        df["date"] = pd.to_datetime(df["time_key"])
        df.set_index("date", inplace=True)

        # 获取交易信号和交易记录
        pos_data = backtest_result["pos_data"]
        trades = backtest_result["trades"]

        # 获取资金曲线
        equity_data = pd.DataFrame(backtest_result["equity_curve"])
        equity_data["date"] = pd.to_datetime(equity_data["date"])
        equity_data.set_index("date", inplace=True)

        # 确定显示范围
        length = len(df)
        start = length - days if days is not None and length - days > 0 else 0

        # 限制数据量
        if days is not None and days < len(df):
            df = df.iloc[-days:]
            pos_data = pos_data[-days:] if len(pos_data) > days else pos_data
            equity_data = (
                equity_data.iloc[-days:] if len(equity_data) > days else equity_data
            )

        # 设置图表布局 (3个子图) - 适配14寸笔记本的屏幕尺寸
        fig = plt.figure(figsize=(12, 10))

        # 比例: K线图(3) + 成交量(1) + 资金曲线(2) + 仓位(1)
        gs = fig.add_gridspec(7, 1)
        ax1 = fig.add_subplot(gs[0:3, 0])  # K线图
        ax2 = fig.add_subplot(gs[3, 0], sharex=ax1)  # 成交量
        ax3 = fig.add_subplot(gs[4:6, 0], sharex=ax1)  # 资金曲线
        ax4 = fig.add_subplot(gs[6, 0], sharex=ax1)  # 仓位

        # 使用与TickerAnalysisHandler相似的配置绘制K线图
        mpf.plot(
            df,
            ax=ax1,
            volume=ax2,
            mav=(13, 21, 144),
            type="candle",
            style="binance",
            warn_too_much_data=900,
            datetime_format="%Y-%m-%d",
            show_nontrading=False,
        )
        ax1.grid(True)
        ax2.grid(True)

        # 准备买入和卖出标记
        # 使用索引值而不是日期来标记，避免重叠
        buys_idx = []
        buys_price = []
        buy_colors = []
        sells_idx = []
        sells_price = []
        sell_colors = []

        index_map = {
            date.strftime("%Y-%m-%d"): idx for idx, date in zip(df["index"], df.index)
        }

        for trade in trades:
            # 买入
            entry_date_str = pd.to_datetime(trade["entry_date"]).strftime("%Y-%m-%d")
            if entry_date_str in index_map:
                idx = index_map[entry_date_str]
                buys_idx.append(idx)
                buys_price.append(trade["entry_price"])
                # 根据方向设置颜色
                if trade["direction"] == 1:
                    buy_colors.append("red")  # 做多
                else:
                    buy_colors.append("green")  # 做空

            # 卖出
            exit_date_str = pd.to_datetime(trade["exit_date"]).strftime("%Y-%m-%d")
            if exit_date_str in index_map:
                idx = index_map[exit_date_str]
                sells_idx.append(idx)
                sells_price.append(trade["exit_price"])
                # 根据盈利情况设置颜色
                if trade["profit"] > 0:
                    sell_colors.append("green")  # 盈利
                else:
                    sell_colors.append("red")  # 亏损

        # 绘制买入和卖出标记
        if buys_idx:
            ax1.scatter(
                buys_idx,
                buys_price,
                s=100,
                marker="^",
                color=buy_colors,
                zorder=5,
                label="买入",
            )

        if sells_idx:
            ax1.scatter(
                sells_idx,
                sells_price,
                s=100,
                marker="v",
                color=sell_colors,
                zorder=5,
                label="卖出",
            )

        # 绘制资金曲线和仓位信息 (使用索引值)
        equity_idx = []
        for date in equity_data.index:
            date_str = date.strftime("%Y-%m-%d")
            if date_str in index_map:
                equity_idx.append(index_map[date_str])
            else:
                # 如果日期不在索引映射中，找最近的索引
                closest_date = min(
                    index_map.keys(), key=lambda x: abs(pd.to_datetime(x) - date)
                )
                equity_idx.append(index_map[closest_date])

        # 确保长度匹配
        equity_idx = equity_idx[: len(equity_data)]

        if len(equity_idx) > 0:
            # 绘制资金曲线
            ax3.plot(
                equity_idx,
                equity_data["total_value"].values,
                label="总资产",
                color="blue",
                linewidth=2,
            )
            ax3.plot(
                equity_idx,
                equity_data["capital"].values,
                label="现金",
                color="green",
                linewidth=1,
                alpha=0.7,
            )
            ax3.set_ylabel("资产价值")
            ax3.legend()
            ax3.grid(True)

            # 绘制仓位信息
            ax4.plot(
                equity_idx,
                equity_data["holdings"].values,
                label="持仓量",
                color="purple",
                linewidth=1.5,
            )
            ax4.set_ylabel("持仓量")
            ax4.grid(True)

        # 设置x轴范围和标签
        if start < len(df["index"]):
            xlim_min = (
                df["index"].values[0] if start == 0 else df["index"].values[start]
            )
            xlim_max = df["index"].values[-1] + 1

            for ax in [ax1, ax2, ax3, ax4]:
                ax.set_xlim(xlim_min, xlim_max)

            # 设置x轴日期标签 (每隔适当的距离显示一个)
            shown_dates = df.index[:: max(1, len(df) // 10)]  # 最多显示10个日期标签
            shown_indices = df.loc[shown_dates]["index"].values

            # 应用日期标签
            ax4.set_xticks(shown_indices)
            ax4.set_xticklabels(
                [date.strftime("%Y-%m-%d") for date in shown_dates], rotation=30
            )

        ax1.set_title(title or "回测结果分析图")
        ax1.legend()

        plt.tight_layout()
        fig.subplots_adjust(hspace=0.1)

        # 保存图表
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        # 显示图表
        if show:
            plt.show()

        return fig

    def visualize_performance(
        self, backtest_result, title=None, show=True, save_path=None
    ):
        """可视化策略性能指标

        Args:
            backtest_result: AdvancedBacktestEngine的回测结果
            title: 图表标题
            show: 是否立即显示图表
            save_path: 保存图表的路径，None表示不保存

        Returns:
            matplotlib figure对象
        """
        metrics = backtest_result["metrics"]

        # 设置图表 - 调整尺寸适配14寸笔记本
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))

        # 1. 收益分析扇形图
        labels = ["毛收益", "毛损失", "交易成本"]
        values = [
            metrics["returns"]["gross_profit"],
            abs(metrics["returns"]["gross_loss"]),
            backtest_result["costs"]["total_slippage"]
            + backtest_result["costs"]["total_commission"],
        ]

        ax1.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            colors=["green", "red", "gray"],
        )
        ax1.set_title("收益构成分析")

        # 2. 交易胜负比例
        labels = ["盈利交易", "亏损交易"]
        values = [
            metrics["summary"]["winning_trades"],
            metrics["summary"]["losing_trades"],
        ]

        ax2.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            colors=["green", "red"],
        )
        ax2.set_title(f'交易胜率: {metrics["summary"]["win_rate"]:.1%}')

        # 3. 关键指标条形图
        metrics_to_show = [
            ("年化收益", metrics["returns"]["annual_return"]),
            ("最大回撤", metrics["risk"]["max_drawdown"]),
            ("夏普比率", metrics["risk"]["sharpe_ratio"]),
            ("索提诺比率", metrics["risk"]["sortino_ratio"]),
            ("盈亏比", metrics["summary"]["profit_loss_ratio"]),
        ]

        names, values = zip(*metrics_to_show)
        y_pos = np.arange(len(names))

        bars = ax3.barh(y_pos, values, align="center")
        ax3.set_yticks(y_pos)
        ax3.set_yticklabels(names)
        ax3.invert_yaxis()  # 标签从上到下
        ax3.set_title("关键绩效指标")

        # 为条形图设置颜色
        for i, bar in enumerate(bars):
            if i == 1:  # 最大回撤
                bar.set_color("red")
            else:
                bar.set_color("green")

        # 为每个条形添加数值标签
        for i, v in enumerate(values):
            if abs(v) < 0.01:
                ax3.text(v + 0.01, i, f"{v:.4f}", va="center")
            else:
                ax3.text(v + 0.01, i, f"{v:.2f}", va="center")

        # 4. 总结表格
        summary_data = [
            ["总交易次数", f"{metrics['summary']['total_trades']}"],
            ["平均持仓天数", f"{metrics['summary']['avg_trade_duration']:.1f}"],
            ["总收益率", f"{metrics['returns']['profit_pct']:.2%}"],
            ["年化收益率", f"{metrics['returns']['annual_return']:.2%}"],
            ["最大回撤", f"{metrics['risk']['max_drawdown']:.2%}"],
            ["胜率", f"{metrics['summary']['win_rate']:.2%}"],
            ["平均盈利", f"{metrics['efficiency']['avg_win']:.2f}"],
            ["平均亏损", f"{metrics['efficiency']['avg_loss']:.2f}"],
            ["盈亏比", f"{metrics['summary']['profit_loss_ratio']:.2f}"],
            ["夏普比率", f"{metrics['risk']['sharpe_ratio']:.2f}"],
            ["索提诺比率", f"{metrics['risk']['sortino_ratio']:.2f}"],
            ["波动率", f"{metrics['risk']['volatility']:.2%}"],
        ]

        ax4.axis("tight")
        ax4.axis("off")
        table = ax4.table(
            cellText=summary_data, loc="center", cellLoc="left", colWidths=[0.3, 0.2]
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)

        plt.suptitle(title or "策略性能评估", fontsize=16)
        plt.tight_layout()

        # 保存图表
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        # 显示图表
        if show:
            plt.show()

        return fig

    def visualize_trades_analysis(
        self, backtest_result, title=None, show=True, save_path=None
    ):
        """可视化交易分析

        Args:
            backtest_result: AdvancedBacktestEngine的回测结果
            title: 图表标题
            show: 是否立即显示图表
            save_path: 保存图表的路径，None表示不保存

        Returns:
            matplotlib figure对象
        """
        trades = backtest_result["trades"]
        if not trades:
            print("没有交易记录可供分析")
            return None

        # 转换交易记录为DataFrame
        df_trades = pd.DataFrame(trades)
        df_trades["entry_date"] = pd.to_datetime(df_trades["entry_date"])
        df_trades["exit_date"] = pd.to_datetime(df_trades["exit_date"])
        df_trades["hold_days"] = (
            df_trades["exit_date"] - df_trades["entry_date"]
        ).dt.days
        df_trades["month"] = df_trades["entry_date"].dt.strftime("%Y-%m")

        # 计算每月交易盈亏
        monthly_profit = df_trades.groupby("month")["profit"].sum()

        # 设置图表 - 调整尺寸适配14寸笔记本
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12))

        # 1. 交易盈亏散点图
        scatter = ax1.scatter(
            df_trades["entry_date"],
            df_trades["profit"],
            s=df_trades["hold_days"] * 5 + 30,  # 根据持仓天数调整点大小
            c=df_trades["profit"],  # 根据盈亏着色
            cmap="RdYlGn",  # 红黄绿色图，红色表示亏损，绿色表示盈利
            alpha=0.7,
        )

        ax1.axhline(y=0, color="black", linestyle="-", alpha=0.3)
        ax1.set_ylabel("交易盈亏")
        ax1.set_title("每笔交易盈亏分析 (点大小表示持仓天数)")

        # 添加颜色条
        cbar = plt.colorbar(scatter, ax=ax1)
        cbar.set_label("盈亏金额")

        # 2. 每月盈亏柱状图
        bars = ax2.bar(monthly_profit.index, monthly_profit.values)
        for i, bar in enumerate(bars):
            if monthly_profit.values[i] > 0:
                bar.set_color("green")
            else:
                bar.set_color("red")

        ax2.axhline(y=0, color="black", linestyle="-", alpha=0.3)
        ax2.set_ylabel("月度盈亏")
        ax2.set_title("月度盈亏分析")
        ax2.set_xticklabels(monthly_profit.index, rotation=45)

        # 3. 持仓分布直方图
        # 左边：持仓天数分布
        ax3_1 = ax3.twinx()
        ax3.hist(
            df_trades[df_trades["profit"] > 0]["hold_days"],
            bins=10,
            alpha=0.5,
            color="green",
            label="盈利交易",
        )
        ax3.hist(
            df_trades[df_trades["profit"] < 0]["hold_days"],
            bins=10,
            alpha=0.5,
            color="red",
            label="亏损交易",
        )
        ax3.set_xlabel("持仓天数")
        ax3.set_ylabel("交易次数")
        ax3.set_title("盈亏交易的持仓天数分布")
        ax3.legend()

        # 右边：盈亏金额分布
        ax3_1.hist(df_trades["profit"], bins=20, alpha=0.3, color="blue", label="盈亏分布")
        ax3_1.set_ylabel("盈亏频率")
        ax3_1.legend(loc="upper right")

        plt.suptitle(title or "交易明细分析", fontsize=16)
        plt.tight_layout()

        # 保存图表
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        # 显示图表
        if show:
            plt.show()

        return fig


def create_example():
    """创建示例代码，展示如何使用BacktestVisualizer"""
    from core.analysis.advanced_backtest_engine import AdvancedBacktestEngine
    from core.strategy.ma_base_strategy import MACrossStrategy

    # 假设我们已经有K线数据
    # kl_data = [...]
    # 创建策略实例
    MACrossStrategy()

    # 创建回测引擎
    AdvancedBacktestEngine()

    # 运行回测
    # result = backtest_engine.run_backtest(strategy, kl_data)

    # 创建可视化实例
    BacktestVisualizer()

    # 可视化回测结果
    # visualizer.visualize_backtest(result, kl_data, title='MA交叉策略回测')

    # 可视化性能指标
    # visualizer.visualize_performance(result, title='MA交叉策略性能')

    # 可视化交易分析
    # visualizer.visualize_trades_analysis(result, title='MA交叉策略交易分析')


if __name__ == "__main__":
    # 如果直接运行脚本，可以创建示例
    # create_example()
    print("回测可视化工具已准备就绪。请导入并使用BacktestVisualizer类。")
