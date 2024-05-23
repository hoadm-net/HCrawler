from os import getcwd, path, remove
import sqlite3
from hmd import HConsole


if __name__ == '__main__':
    base_dir = getcwd()
    data_file = path.join(base_dir, 'main.db')
    console = HConsole()

    if path.exists(data_file):
        console.warning('SQLite file is existed, do you want override it? Y/n')
        user_input = input()
        if user_input.lower() in ['y', 'yes']:
            remove(data_file)
            console.info('SQLite file was removed.')
        else:
            exit(1)

    console.info('Create SQLite file and Database schema.')
    con = sqlite3.connect("main.db")
    cur = con.cursor()
    cur.execute("CREATE TABLE posts(id INTEGER PRIMARY KEY, url VARCHAR UNIQUE, cat VARCHAR)")
    cur.execute("CREATE TABLE logs(url VARCHAR PRIMARY KEY)")
    console.success('Done...')
