from datetime import datetime, timedelta
from os import path, mkdir, remove
import shutil
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
import time
import sqlite3
import re
from .h_console import HConsole


class HApp(object):
    def __init__(self, base_dir: str, scan: bool | None, clean: bool | None, delay_time=1, from_date='01_01_2024', days=365, verbose=False):
        self.base_dir = base_dir
        self.clean = clean
        self.scan = scan
        self.delay_time = delay_time  # delay for 1 second
        self.verbose = verbose
        self.errors = 0
        self.from_date = datetime.strptime(from_date, "%d_%m_%Y").date()
        self.days = days

        self.data_dir = path.join(self.base_dir, 'data')
        self.hnews_2_t_path = path.join(self.data_dir, 'hnews_2_t')
        self.hnews_2_td_path = path.join(self.data_dir, 'hnews_2_td')
        self.hnews_2_f_path = path.join(self.data_dir, 'hnews_2_f')
        self.hnews_8_t_path = path.join(self.data_dir, 'hnews_8_t')
        self.hnews_8_td_path = path.join(self.data_dir, 'hnews_8_td')
        self.hnews_8_f_path = path.join(self.data_dir, 'hnews_8_f')

        self.console = HConsole()
        self.categories = {
            'thoisu': '1001005',
            'kinhte': '1003159',
            'thegioi': '1001002',
            'doisong': '1002966',
            'suckhoe': '1003750',
            'thethao': '1002565',
            'giaoduc': '1003497',
            'khoahoc': '1001009',
        }
        self.sqlite_conn = sqlite3.connect(path.join(base_dir, 'main.db'))

    @staticmethod
    def _clean_str(inp: str) -> str:
        output = bytes(inp, 'utf-8').decode('utf-8', 'ignore').strip()
        output = re.sub(r'\n', ' ', output)
        output = re.sub(' +', ' ', output)
        return output

    def _debug(self, msg) -> None:
        if not self.verbose:
            return
        self.console.warning(msg)

    # Helpers
    def _get_link_by_cat(self, cat: str, dtime: str) -> str:
        cat_id = self.categories[cat]
        return f"https://vnexpress.net/category/day/cateid/{cat_id}/fromdate/{dtime}/todate/{dtime}"

    # Database
    def _delete_row(self, row_id: str) -> None:
        self.sqlite_conn.execute("DELETE FROM posts WHERE id = (?)", (row_id,))

    def _is_exists(self, url: str) -> bool:
        try:
            with self.sqlite_conn:
                self.sqlite_conn.execute(
                    "INSERT INTO logs(url) VALUES(?)", (url,)
                )
            return False
        except sqlite3.IntegrityError as e:
            self._debug(e)
            return True

    # Write files
    def _write_t(self, file_name: str, title: str, cat: str, ver=2):
        folder_path = self.hnews_2_t_path
        if ver == 8:
            folder_path = self.hnews_8_t_path
        file_path = path.join(folder_path, cat, file_name)
        with open(file_path, 'w+') as f:
            f.write(title)

    def _write_td(self, file_name: str, title: str, desc: str, cat: str, ver=2):
        folder_path = self.hnews_2_td_path
        if ver == 8:
            folder_path = self.hnews_8_td_path
        file_path = path.join(folder_path, cat, file_name)
        with open(file_path, 'w+') as f:
            f.write(title + '\n')
            f.write(desc)

    def _write_f(self, file_name: str, title: str, desc: str, content, cat: str, ver=2):
        folder_path = self.hnews_2_f_path
        if ver == 8:
            folder_path = self.hnews_8_f_path
        file_path = path.join(folder_path, cat, file_name)
        with open(file_path, 'w+') as f:
            f.write(title + '\n')
            f.write(desc + '\n')
            f.write(content)

    # Main logic
    def _get_posts(self) -> None:
        for i in tqdm(range(self.days)):
            calculating_date = self.from_date + timedelta(days=i)
            ts = str(int(time.mktime(calculating_date.timetuple())))

            for cat, cat_id in self.categories.items():
                post_url = self._get_link_by_cat(cat, ts)

                response = requests.get(post_url)
                if response.status_code == 200 and response.text:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    articles = soup.find_all('article', class_='item-news item-news-common')
                    for article in articles:
                        anchorTags = article.find_all('a')
                        if anchorTags:
                            link = anchorTags[0]['href']
                            try:
                                with self.sqlite_conn:
                                    self.sqlite_conn.execute(
                                        "INSERT INTO posts(url, cat) VALUES(?, ?)",
                                        (link, cat)
                                    )
                                self.errors = 0
                            except sqlite3.IntegrityError as e:
                                self._debug(e)
                time.sleep(self.delay_time)

    def _get_data(self):
        i = 1
        with self.sqlite_conn:
            cursor = self.sqlite_conn.cursor()
            counter = cursor.execute("SELECT COUNT(*) FROM posts").fetchone()
            posts = cursor.execute("SELECT * FROM posts LIMIT 10").fetchall()

        while posts:
            for post in tqdm(posts, desc=f"Iter {i}/{counter[0]//10}"):
                file_mame = f"{post[0]:07}"
                post_url = post[1]
                cat_name = post[2]

                response = requests.get(post_url)

                if response.status_code == 200 and response.text:
                    # parse
                    soup = BeautifulSoup(response.text, 'html.parser')

                    title_e = soup.find('h1', class_='title-detail')
                    desc_e = soup.find('p', class_='description')
                    content_e = soup.find('article', class_='fck_detail')

                    if title_e and desc_e and content_e:
                        title = self._clean_str(title_e.text)

                        location_stamp = desc_e.find('span', class_='location-stamp')
                        if location_stamp:
                            location_stamp.decompose()

                        desc = self._clean_str(desc_e.text)
                        content = self._clean_str(content_e.text)

                        if cat_name in ['kinhte', 'thoisu']:
                            self._write_t(file_mame, title, cat_name, 2)
                            self._write_td(file_mame, title, desc, cat_name, 2)
                            self._write_f(file_mame, title, desc, content, cat_name, 2)

                        self._write_t(file_mame, title, cat_name, 8)
                        self._write_td(file_mame, title, desc, cat_name, 8)
                        self._write_f(file_mame, title, desc, content, cat_name, 8)

                self._delete_row(post[0])
                time.sleep(self.delay_time)

            i += 1
            with self.sqlite_conn:
                cursor = self.sqlite_conn.cursor()
                posts = cursor.execute("SELECT * FROM posts LIMIT 10").fetchall()

    # App flow: setup -> run -> quit
    def setup(self) -> None:

        if path.exists(self.data_dir):
            if self.clean:
                shutil.rmtree(self.data_dir)
                self.console.info("Old data were removed!")
                self.console.info("="*50)
            else:
                return

        mkdir(self.data_dir)
        datasets_2 = [
            self.hnews_2_t_path,
            self.hnews_2_td_path,
            self.hnews_2_f_path,
        ]

        datasets_8 = [
            self.hnews_8_t_path,
            self.hnews_8_td_path,
            self.hnews_8_f_path,
        ]

        for ds in datasets_2:
            mkdir(ds)
            for cat in ['thoisu', 'kinhte']:
                mkdir(path.join(ds, cat))

        for ds in datasets_8:
            mkdir(ds)
            for cat in self.categories:
                mkdir(path.join(ds, cat))

    def run(self):
        if self.scan:
            self.console.info("Crawling post info...")
            self._get_posts()

        self.console.info("Crawling post data...")
        self._get_data()

        self.console.success("Done...")

    def quit(self):
        self.console.info("Quiting...")
