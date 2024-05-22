from os import path, mkdir, remove
import shutil
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
import time
import sqlite3
from .h_console import HConsole


class HApp(object):
    def __init__(self, base_dir: str, scan: bool | None, clean: bool | None):
        self.base_dir = base_dir
        self.clean = clean
        self.scan = scan
        self.max_page = 2
        self.delay_time = 1  # delay for 1 second

        self.data_dir = path.join(self.base_dir, 'data')
        self.hnews_2_t_path = path.join(self.data_dir, 'hnews_2_t')
        self.hnews_2_td_path = path.join(self.data_dir, 'hnews_2_td')
        self.hnews_2_f_path = path.join(self.data_dir, 'hnews_2_f')
        self.hnews_8_t_path = path.join(self.data_dir, 'hnews_8_t')
        self.hnews_8_td_path = path.join(self.data_dir, 'hnews_8_td')
        self.hnews_8_f_path = path.join(self.data_dir, 'hnews_8_f')

        self.console = HConsole()
        self.categories = {
            'thoisu': '1854',
            'kinhte': '18549',
            'thegioi': '18566',
            'doisong': '18517',
            'suckhoe': '18565',
            'thethao': '185318',
            'giaoduc': '18526',
            'congnghe': '185315',
        }

        self.slug = {
            'thoisu': 'thời sự',
            'kinhte': 'kinh tế',
            'thegioi': 'thế giới',
            'doisong': 'đời sống',
            'suckhoe': 'sức khỏe',
            'thethao': 'thể thao',
            'giaoduc': 'giáo dục',
            'congnghe': 'công nghệ',
        }

        self.current_page = 1
        self.sqlite_conn = sqlite3.connect(path.join(base_dir, 'main.db'))

    def setup(self) -> None:

        if path.exists(self.data_dir):
            if self.clean:
                shutil.rmtree(self.data_dir)
                self.console.info("Old data were removed!")
                self.console.info("="*50)

                remove(path.join(self.base_dir, 'log.txt'))
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

        if path.exists(path.join(self.base_dir, 'log.txt')):
            with open(path.join(self.base_dir, 'log.txt'), 'r') as fp:
                self.current_page = int(fp.read())

    def _get_link_by_cat(self, cat: str, page: int) -> str:
        cat_id = self.categories[cat]
        return f"https://thanhnien.vn/timelinelist/{cat_id}/{page}.htm"

    def _get_posts(self) -> None:
        for page in tqdm(range(self.current_page, self.max_page)):
            for cat in self.categories:
                link = self._get_link_by_cat(cat, page)
                response = requests.get(link)

                if not response.text or response.status_code != 200:
                    return

                soup = BeautifulSoup(response.text, 'html.parser')
                articles = soup.find_all('div', class_='box-category-item')
                for art in articles:
                    cat_tag = art.find_all('a', class_='box-category-category')
                    link_tag = art.find_all('a', class_='box-category-related-link-title')

                    if not cat_tag or not link_tag:
                        continue

                    cat_text = cat_tag[0].text.lower()
                    # filter not clear article (belong to sub-cat)
                    if cat_text != self.slug[cat]:
                        continue

                    link = link_tag[0]['href'].strip()
                    try:
                        with self.sqlite_conn:
                            self.sqlite_conn.execute(
                                "INSERT INTO posts(url, cat) VALUES(?, ?)",
                                (link, cat)
                            )
                    except sqlite3.IntegrityError:
                        continue
                time.sleep(self.delay_time)
            self.current_page += 1

    def _delete_row(self, row_id) -> None:
        self.sqlite_conn.execute("DELETE FROM posts WHERE id = (?)", (row_id,))

    @staticmethod
    def _clean_str(inp: str) -> str:
        return bytes(inp, 'utf-8').decode('utf-8', 'ignore')

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

    def _get_data(self):
        i = 1
        with self.sqlite_conn:
            cursor = self.sqlite_conn.cursor()
            counter = cursor.execute("SELECT COUNT(*) FROM posts").fetchone()
            posts = cursor.execute("SELECT * FROM posts LIMIT 10").fetchall()

        while posts:
            for post in tqdm(posts, desc=f"Iter {i}/{counter[0]//10}"):
                file_mame = f"{post[0]:07}"
                post_url = f"https://thanhnien.vn/{post[1]}"
                cat_name = post[2]

                resp = requests.get(post_url)

                if resp.status_code == 200 and resp.text != "":
                    # parse
                    soup = BeautifulSoup(resp.text, 'html.parser')

                    post_title = soup.find_all(class_='detail-title')
                    post_desc = soup.find_all(class_='detail-sapo')
                    post_content = soup.find_all(class_='detail-cmain')

                    if post_title and post_desc and post_content:
                        post_title_tag = post_title[0]
                        post_desc_tag = post_desc[0]
                        post_content_tag = post_content[0]

                        title = self._clean_str(post_title_tag.text.strip())
                        desc = self._clean_str(post_desc_tag.text.strip())
                        content = self._clean_str(post_content_tag.text.strip())

                        if cat_name in ['kinh tế', 'thời sự']:
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

    def run(self):
        if self.scan:
            self.console.info("Crawling post info...")
            self._get_posts()

        self.console.info("Crawling post data...")
        self._get_data()

        self.console.success("Done...")

    def quit(self):
        with open(path.join(self.base_dir, 'log.txt'), mode='w+') as fp:
            fp.write(f"{self.current_page}")
        self.console.info("Quiting...")
