import os
from time import sleep
import pandas as pd
import polars as pl
import prestodb
from tqdm import tqdm
from colorama import Fore
from concurrent.futures import ThreadPoolExecutor


class DataPipeLine:
    def __init__(self, query_or_dir):
        self.query = query_or_dir
        self.status = f'{Fore.LIGHTBLUE_EX}🐔 JDBC:{Fore.RESET}'

    def run_presto_to_df(self, polars=False, priority=25):
        # connection
        username, password = os.environ['PRESTO_USER'], os.environ['PRESTO_PASSWORD']
        conn = prestodb.dbapi.connect(
            host='presto-secure.data-infra.shopee.io',
            port=443,
            user=username,
            catalog='hive',
            http_scheme='https',
            source=f'({priority})-(vnbi-dev)-({username})-(jdbc)-({username})-(SG)',
            auth=prestodb.auth.BasicAuthentication(username, password)
        )
        cur = conn.cursor()
        cur.execute(self.query)

        # logging
        thread = ThreadPoolExecutor(1)
        async_result = thread.submit(cur.fetchall)

        bar_queue = tqdm()
        while not async_result.done():
            memory = cur.stats['peakMemoryBytes'] * 10 ** -9
            perc = 0
            if cur.stats['state'] == "RUNNING":
                perc = round((cur.stats['completedSplits'] * 100.0) / (cur.stats['totalSplits']), 2)
            status = (f"🤖 JDBC Status: {cur.stats['state']} {perc}%, Memory {memory:,.0f}GB")
            bar_queue.set_description(status)
            bar_queue.update(1)
            sleep(5)
        bar_queue.close()
        records = async_result.result()

        # result
        if polars:
            df = pl.DataFrame(records, schema=[i[0] for i in cur.description])
        else:
            df = pd.DataFrame(records, columns=[i[0] for i in cur.description])

        print(f"{self.status} Data Shape: {df.shape}")
        return df
