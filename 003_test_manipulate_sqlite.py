import sqlite3
con = sqlite3.connect("extracted_data.db")

cur = con.cursor()
# cur.execute("CREATE TABLE sessions(session_id, status, date)")
# cur.execute("CREATE TABLE care_package(session_id, who_will_use_service, type_of_service, ndis_registered, hrs_per_day, days_per_week, how_long, when_to_start)")
# cur.execute("CREATE TABLE accommodation(session_id, who_will_use_service, ndis_registered, type_of_accommodation, how_long, supported_living_services, how_pay_for_rent, when_to_start)")
# cur.execute("CREATE TABLE lead_info(session_id, name, email, postcode)")

# res = cur.execute("SELECT name FROM sqlite_master")
# res.fetchone()

# res = cur.execute("SELECT name FROM sqlite_master WHERE name='spam'")
# res.fetchone() is None

# res = cur.execute("SELECT score FROM movie")
# res.fetchall()

# for row in cur.execute("SELECT year, title FROM movie ORDER BY year"):
#     print(row)

cur.execute("""
    INSERT INTO movie VALUES
        ('Monty Python and the Holy Grail', 1975, 8.2),
        ('And Now for Something Completely Different', 1971, 7.5)
""")

con.commit()

# data = [
#     ("Monty Python Live at the Hollywood Bowl", 1982, 7.9),
#     ("Monty Python's The Meaning of Life", 1983, 7.5),
#     ("Monty Python's Life of Brian", 1979, 8.0),
# ]
# cur.executemany("INSERT INTO movie VALUES(?, ?, ?)", data)
# con.commit()  # Remember to commit the transaction after executing INSERT.

con.close()
# new_con = sqlite3.connect("tutorial.db")
# new_cur = new_con.cursor()
# res = new_cur.execute("SELECT title, year FROM movie ORDER BY score DESC")
# title, year = res.fetchone()
# print(f'The highest scoring Monty Python movie is {title!r}, released in {year}')




