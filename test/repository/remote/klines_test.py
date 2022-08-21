"""
    def job():
        now = pendulum.now()
        open_time = now.add(minutes=-1).start_of("minute")
        close_time = now.add(minutes=-1).end_of("minute")
        klines = client.get_klines_data(
            TradingPair(CryptoAsset.BNB, CryptoAsset.BUSD), Interval.M_1, open_time, close_time, 5
        )
        print(f"{now=} {open_time.minute=}{open_time.second=} {close_time.minute=}{close_time.second=} {klines=}")

    def job_same():
        now = pendulum.now()
        open_time = now.start_of("minute")
        close_time = now.end_of("minute")

        print(f"{now=} {open_time.minute=}{open_time.second=} {close_time.minute=}{close_time.second=} {klines=}")

    schedule.every().minute.at(":40").do(job_same)
    schedule.every().minute.at(":58").do(job_same)
    schedule.every().minute.at(":59").do(job_same)
    schedule.every().minute.at(":00").do(job)
    schedule.every().minute.at(":01").do(job)
    # schedule.every().minute.at(":30").do(job)
    # schedule.every().minute.at(":50").do(job)

    while True:
        schedule.run_pending()
        time.sleep(0.5)
"""
import asyncio

import pendulum

from consts import CryptoAsset
from repository import TradingPair, Interval
from repository.remote import BinanceClient

if __name__ == "__main__":

    class KlineProducer:
        now = pendulum.now()
        queue = asyncio.Queue(10_000)
        client = BinanceClient()

        last_stime = now.subtract(minutes=1).start_of("minute")
        last_etime = now.subtract(minutes=1).end_of("minute")

        @staticmethod
        async def get_pending():
            print(f"running _get_pending_klines at: {pendulum.now().format('m:s:SSSS')}")
            #print(f"{KlineProducer.last_stime=} {KlineProducer.last_etime}")
            period = pendulum.period(KlineProducer.last_stime.add(minutes=1), pendulum.now().start_of("minute"))
            kl_times = [t for t in period.range("minutes")]

            stime = kl_times[0]
            etime = kl_times[-1].end_of("minute")

            #print(f"get_klines_data arguments: {stime=} {etime=} {kl_times=}")
            klines = KlineProducer.client.get_klines_data(
                TradingPair(CryptoAsset.BNB, CryptoAsset.BUSD),
                Interval.M_1,
                start_time=stime,
                end_time=etime,
                limit=len(kl_times)
            )
            print(f"got {klines=} from api at {pendulum.now().format('m:s:SSSS')}")

            KlineProducer.last_stime = stime
            KlineProducer.last_etime = etime

            for kl in klines:
                #print(f"putting {kl} in queue")
                await KlineProducer.queue.put(kl)

            #print(f"Is queue empty ? {KlineProducer.queue.empty()}")

    async def schedule_job():
        now = pendulum.now()
        next_job = now.at(now.hour, now.minute, 59)
        wait_time = pendulum.now().diff(next_job).total_seconds()

        while True:
            print(f"{wait_time=}")
            if wait_time > 0:
                print(f"sleeping for {wait_time} seconds")
                await asyncio.sleep(wait_time)
            print(f"Running pending job at {pendulum.now().format('m:s:SSSS')}")
            await KlineProducer.get_pending()

            next_job = next_job.add(minutes=1)
            wait_time = pendulum.now().diff(next_job).total_seconds()

    async def get_kline():
        while True:
            yield await KlineProducer.queue.get()

    async def main():
        background_tasks = set()

        job_task = asyncio.create_task(schedule_job())
        background_tasks.add(job_task)  # Create strong reference to prevent task from being garbage collected

        async for kline in get_kline():
            print(f"run got {kline=} at {pendulum.now().format('m:s:SSSS')}")
            #time.sleep(10)

    asyncio.run(main())


    """async def run():
        async for e in get_element():
            print(f"run got element {e} at {pendulum.now().format('m:s:SSSS')}")
            print(f"run starts heavy computation at {pendulum.now().format('m:s:SSSS')}.")
            time.sleep(10)
            print(f"run heavy computation is finished at {pendulum.now().format('m:s:SSSS')}.")

    asyncio.run(run())"""



