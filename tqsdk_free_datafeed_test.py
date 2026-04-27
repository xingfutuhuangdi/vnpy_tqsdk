# 配置好vt_setting.json里的datafeed字段后，运行测试
from vnpy_tqsdk.tqsdk_datafeed import TqsdkDatafeed
from vnpy.trader.object import HistoryRequest
from vnpy.trader.constant import Exchange, Interval
from datetime import datetime, timedelta

test_day_len = 366


def main():
    data_feed = TqsdkDatafeed()
    req = HistoryRequest(symbol="i2605",
                         exchange=Exchange.DCE,
                         start=datetime.now() - timedelta(days=test_day_len),
                         end=datetime.now(),
                         interval=Interval.HOUR)

    bars = data_feed.query_bar_history(req=req)

    for bar in bars:
        print("================")
        print(bar.close_price)
        print(bar.open_price)
        print(bar.high_price)
        print(bar.low_price)


if __name__ == "__main__":
    main()
