from datetime import timedelta, datetime
from collections.abc import Callable
import traceback

# from pandas import DataFrame
import pandas as pd
from tqsdk import TqApi, TqAuth, TqBacktest, BacktestFinished

from vnpy.trader.datafeed import BaseDatafeed
from vnpy.trader.setting import SETTINGS
from vnpy.trader.constant import Interval
from vnpy.trader.object import BarData, HistoryRequest
from vnpy.trader.utility import ZoneInfo


INTERVAL_VT2TQ: dict[Interval, int] = {
    Interval.MINUTE: 60,
    Interval.HOUR: 60 * 60,
    Interval.DAILY: 60 * 60 * 24
}

CHINA_TZ = ZoneInfo("Asia/Shanghai")


class TqsdkDatafeed(BaseDatafeed):
    """天勤TQsdk数据服务接口"""

    def __init__(self) -> None:
        """"""
        self.username: str = SETTINGS["datafeed.username"]
        self.password: str = SETTINGS["datafeed.password"]

    def query_bar_history(self, req: HistoryRequest, output: Callable = print) -> list[BarData] | None:
        """查询k线数据"""
        # 初始化API
        try:
            api: TqApi = TqApi(backtest=TqBacktest(start_dt=req.start, end_dt=req.end),
                               auth=TqAuth(self.username, self.password))
        except Exception:
            output(traceback.format_exc())
            return None

        # 查询数据
        interval: int | None = INTERVAL_VT2TQ.get(req.interval, None)
        if not interval:
            output(f"Tqsdk查询K线数据失败：不支持的时间周期{req.interval.value}")
            return []
        
        # 解析数据
        bars: list[BarData] = []

        tq_symbol: str = f"{req.exchange.value}.{req.symbol}"

        df: pd.DataFrame = api.get_kline_serial(
            symbol=tq_symbol,
            duration_seconds=INTERVAL_VT2TQ[req.interval]
        )

        try:
            while api.wait_update():
                if api.is_changing(df.iloc[-1], "datetime"):
                    tp = df.iloc[-1]
                    bar: BarData = BarData(
                        symbol=req.symbol,
                        exchange=req.exchange,
                        interval=req.interval,
                        datetime=datetime.fromtimestamp(tp.datetime/1_000_000_000, tz=CHINA_TZ),    # type: ignore
                        open_price=tp.open if not pd.isna(tp.open) else 0.0,
                        high_price=tp.high if not pd.isna(tp.high) else 0.0,
                        low_price=tp.low if not pd.isna(tp.low) else 0.0,
                        close_price=tp.close if not pd.isna(tp.close) else 0.0,
                        volume=tp.volume,
                        open_interest=tp.open_oi,
                        gateway_name="TQ",
                    )
                    bars.append(bar)
                    
        except BacktestFinished as e:
            output(f"回测结束")
            api.close()

        return bars
