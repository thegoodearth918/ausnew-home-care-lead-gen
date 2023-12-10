import sqlite3
import datetime

con = sqlite3.connect("extracted_data.db")

cur = con.cursor()

# cur.execute("""
#     INSERT INTO care_package VALUES
#         ('Monty Python and the Holy Grail', '1975', '8.2', '1975', '1975', '1975', '1975', '1975'),
#         ('abcd', '1975', '8.2', '1975', '1975', '1975', '1975', '1975')
# """)

res = cur.execute("SELECT rowid, * FROM care_package")
print(res.fetchall())

con.close()
