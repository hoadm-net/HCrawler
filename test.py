import sqlite3


if __name__ == '__main__':
    con = sqlite3.connect("main.db")
    try:
        with con:
            cur = con.cursor()
            for row in cur.execute("SELECT * FROM posts LIMIT 10"):
                print(row)
                print("crawling...")
    except sqlite3.IntegrityError as e:
        print(e)
