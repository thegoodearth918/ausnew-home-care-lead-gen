import sqlite3
con = sqlite3.connect("extracted_data.db")

cur = con.cursor()
cur.execute("CREATE TABLE sessions(session_id, status, created_at)")
cur.execute("CREATE TABLE care_package(session_id, who_is_this_care_for, type_of_service, ndis_registered, hrs_per_day, days_per_week, how_long, when_to_start, created_at)")
cur.execute("CREATE TABLE accommodation(session_id, who_is_this_care_for, ndis_registered, type_of_accommodation, how_long, supported_living_services, how_pay_for_rent, when_to_start, created_at)")
cur.execute("CREATE TABLE lead_info(session_id, name, email, postcode)")


con.commit()

con.close()
