from mysql.connector import connect, Error


class Repo:
    ROLE_PASSENGER = 0
    ROLE_DISPATCHER = 1
    ROLE_ADMINISTRATOR = 2

    def __init__(self, host, user, password, db):
        self.connection = None
        self.cursor = None
        self.connect_to_db(host, user, password, db)
        if self.connection is not None and self.cursor is not None:
            self.select_db(db)
            self.get_tables = lambda: self.raw_query("SHOW TABLES")

            self.get_user = lambda username: self.get_query("SELECT * FROM user WHERE username='%s'" % username)
            self.get_all_users = lambda: self.raw_query("SELECT * FROM user JOIN role, document d WHERE user.role_id=role.id AND user.document_id=d.id")
            self.login_user = lambda username, password: self.get_query(
                "SELECT * FROM user WHERE username='%s' AND password='%s'" % (username, password))
            self.add_u = lambda username, password, fio, d_id, d_n, role: self.write_query(
                f"INSERT INTO user SET username='{username}', fio='{fio}', password='{password}', document_id='{d_id}', document_number='{d_n}', role_id='{role}'")
            self.rm_user = lambda id: self.write_query(f"DELETE FROM user WHERE id='{id}'")

            self.get_roles = lambda: self.raw_query("SELECT * from role")

            self.select_documents = lambda: self.raw_query("SELECT * FROM document")

            self.add_aircraft = lambda name, capacity, plate: self.write_query(
                f"INSERT INTO aircraft SET name='{name}', capacity='{capacity}', plate='{plate}'")
            self.get_aircrafts = lambda: self.raw_query("SELECT * FROM aircraft WHERE hidden='0'")
            self.select_aircrafts = lambda: self.raw_query("SELECT id, name FROM aircraft WHERE hidden='0'")
            self.get_aircraft = lambda id: self.get_query(f"SELECT * FROM aircraft WHERE id='{id}'")
            self.get_aircraft_by_plate = lambda plate: self.get_query(f"SELECT * FROM aircraft WHERE plate='{plate}' AND hidden='0'")
            self.rm_aircraft = lambda id: self.write_query(f"DELETE FROM aircraft WHERE id='{id}'")
            self.hide_aircraft = lambda id: self.write_query(f"UPDATE aircraft SET hidden='1' WHERE id='{id}'")

            self.add_airport = lambda name, city, address: self.write_query(f"INSERT INTO airport SET name='{name}', city='{city}', address='{address}'")
            self.get_airports = lambda: self.raw_query("SELECT * FROM airport")
            self.select_airports = lambda: self.raw_query("SELECT id, name FROM airport")
            self.get_airport = lambda id: self.raw_query(f"SELECT * FROM airport WHERE id='{id}'")
            self.get_airport_by_name = lambda name: self.get_query(f"SELECT * FROM airport WHERE name='{name}'")
            self.rm_airport = lambda id: self.raw_query(f"DELETE FROM airport WHERE id='{id}'")

            self.add_route = lambda number, a1, a2, price, flight_time: self.write_query(f"INSERT INTO route SET number='{number}', departure_airport_id='{a1}', destination_airport_id='{a2}', price='{price}', flight_time='{flight_time}'")
            self.get_routes = lambda: self.raw_query("SELECT r.*, a1.name, a2.name FROM route r JOIN airport a1, airport a2 WHERE r.departure_airport_id=a1.id AND r.destination_airport_id=a2.id")
            self.select_routes = lambda: self.raw_query("SELECT id, number FROM route")
            self.rm_route = lambda id: self.write_query(f"DELETE FROM route WHERE id='{id}'")
            self.get_airport_routes = lambda id: self.raw_query(f"SELECT * FROM route WHERE departure_airport_id='{id}' OR destination_airport_id='{id}'")
            self.get_route_by_number = lambda number: self.get_query(f"SELECT * FROM route WHERE number='{number}'")

            self.add_flight = lambda route_id, aircraft_id, date: self.write_query(f"INSERT INTO flight SET route_id='{route_id}', aircraft_id='{aircraft_id}', departure_date='{date}'")
            self.get_flights = lambda: self.raw_query("SELECT f.id, f.departure_date, CONCAT('(', r.number, ') ', a1.name, ' - ', a2.name), CONCAT(a.name, ' (', a.plate, ')'), (SELECT COUNT(*) FROM seat WHERE flight_id=f.id), a.capacity FROM flight f JOIN route r, aircraft a, airport a1, airport a2 WHERE f.route_id=r.id AND f.aircraft_id=a.id AND r.departure_airport_id=a1.id AND r.destination_airport_id=a2.id ORDER BY f.departure_date")
            self.get_aircraft_capacity = lambda flight_id: self.get_one_query(f"SELECT a.capacity FROM flight f JOIN aircraft a ON f.aircraft_id=a.id WHERE f.id='{flight_id}'")
            self.get_flight = lambda id: self.raw_query(f"SELECT f.id, f.departure_date, CONCAT(a1.name, ' - ', a2.name), CONCAT(a.name, ' (', a.plate, ')'), (SELECT COUNT(*) FROM seat WHERE flight_id=f.id), a.capacity FROM flight f JOIN route r, aircraft a, airport a1, airport a2 WHERE f.route_id=r.id AND f.aircraft_id=a.id AND r.departure_airport_id=a1.id AND r.destination_airport_id=a2.id AND f.id='{id}'")
            self.rm_flight = lambda id: self.write_query(f"DELETE FROM flight WHERE id='{id}'")
            self.get_aircraft_flights = lambda id: self.raw_query(f"SELECT * FROM flight WHERE aircraft_id='{id}'")
            self.get_route_flights = lambda id: self.raw_query(f"SELECT * FROM flight WHERE route_id='{id}'")

            self.add_seat = lambda flight_id, user_id, date: self.write_query(f"INSERT INTO seat SET flight_id='{flight_id}', user_id={user_id}, purchase_date='{date}'")
            self.get_seats_amount = lambda flight_id: self.get_one_query(f"SELECT COUNT(*) FROM seat WHERE flight_id='{flight_id}'")
            self.get_seat_by_user_and_flight = lambda fid, uid: self.raw_query(f"SELECT * FROM seat WHERE flight_id='{fid}' AND user_id='{uid}'")
            self.get_seats_of_user = lambda id: self.raw_query(f"SELECT flight_id, departure_date, flight_time, CONCAT(a.name, ' ', plate), CONCAT(a1.name, ' - ', a2.name) FROM seat JOIN flight f, route r, aircraft a, airport a1, airport a2 WHERE seat.flight_id=f.id AND f.route_id=r.id AND f.aircraft_id=a.id AND r.departure_airport_id=a1.id AND r.destination_airport_id=a2.id AND seat.user_id='{id}'")
            self.rm_seat = lambda fid, uid: self.write_query(f"DELETE FROM seat WHERE flight_id='{fid}' AND user_id='{uid}'")
            self.get_seats_of_flight = lambda id: self.raw_query(f"SELECT * FROM seat s JOIN user u, document d WHERE s.user_id=u.id AND u.document_id=d.id AND s.flight_id='{id}'")
            self.rm_seats_of_flight = lambda id: self.write_query(f"DELETE FROM seat WHERE flight_id='{id}'")
            self.rm_seats_of_user = lambda id: self.write_query(f"DELETE FROM seat WHERE user_id='{id}'")

            self.get_profit_by_month = lambda: self.raw_query("SELECT DATE_FORMAT(departure_date, '%Y-%c'), SUM(price) FROM avia.seat JOIN flight f, route r WHERE flight_id=f.id AND f.route_id=r.id GROUP BY YEAR(departure_date), MONTH(departure_date)")

    def connect_to_db(self, host, user, password, db):
        try:
            self.connection = connect(host=host, user=user, password=password)
            self.cursor = self.connection.cursor()
            self.cursor.execute("SHOW DATABASES")
            for res in self.cursor:
                if res[0] == db:
                    self.cursor.fetchall()
                    return
            for line in open('dump.sql'):
                self.cursor.execute(line)
            self.connection.commit()
            print('dump loaded successfully')
        except Error as e:
            print(e)

    def select_db(self, db):
        self.cursor.execute(f"USE {db}")

    def raw_query(self, query):
        if self.cursor and query:
            self.cursor.execute(query)
            return self.cursor.fetchall()

    def write_query(self, query):
        if self.cursor and query:
            self.cursor.execute(query)
            self.connection.commit()
            return self.cursor.fetchall()

    def get_query(self, query):
        if self.cursor and query:
            self.cursor.execute(query)
            return self.cursor.fetchone()

    def get_one_query(self, query):
        if self.cursor and query:
            self.cursor.execute(query)
            return self.cursor.fetchone()[0]

    def add_user(self, username, password, fio, document_id, document_number, role):
        if not self.get_user(username):
            self.add_u(username, password, fio, document_id, document_number, role)
            return True
        else:
            return False

    def add_aircraft_check(self, name, capacity, plate):
        if not self.get_aircraft_by_plate(plate):
            self.add_aircraft(name, capacity, plate)
            return True
        return False

    def add_airport_check(self, name, city, address):
        if not self.get_airport_by_name(name):
            self.add_airport(name, city, address)
            return True
        return False

    def add_route_check(self, number, a1, a2, price, flight_time):
        if not self.get_route_by_number(number):
            self.add_route(number, a1, a2, price, flight_time)
            return True
        return False

    def check_flight_date(self, aircraft_id, new_date):
        dates = self.raw_query(f"SELECT departure_date, flight_time FROM flight JOIN route ON flight.route_id=route.id WHERE aircraft_id='{aircraft_id}'")
        for date in dates:
            print(date, new_date)
            if abs((new_date - date[0]).total_seconds()) < date[1].total_seconds():
                return False
        return True

    def add_flight_with_check(self, route_id, aircraft_id, date):
        if self.check_flight_date(aircraft_id, date):
            self.add_flight(route_id, aircraft_id, date)
            return True
        return False

    def buy_ticket(self, flight_id, user_id, date):
        a = self.get_seats_amount(flight_id)
        c = self.get_aircraft_capacity(flight_id)
        if a < c and len(self.get_seat_by_user_and_flight(flight_id, user_id)) == 0:
            self.add_seat(flight_id, user_id, date)
            return True
        return False

    def get_flights_sorted(self, departure_airport, destination_airport, date):
        q = "SELECT f.id, f.departure_date, CONCAT('(', r.number, ') ', a1.name, ' - ', a2.name), CONCAT(a.name, ' (', a.plate, ')'), (SELECT COUNT(*) FROM seat WHERE flight_id=f.id), a.capacity FROM flight f JOIN route r, aircraft a, airport a1, airport a2 WHERE f.route_id=r.id AND f.aircraft_id=a.id AND r.departure_airport_id=a1.id AND r.destination_airport_id=a2.id"
        if departure_airport:
            q = q + f" AND r.departure_airport_id='{departure_airport}'"
        if destination_airport:
            q = q + f" AND r.destination_airport_id='{destination_airport}'"
        if date:
            q = q + f" AND DATE(f.departure_date)='{date}'"
        q = q + ' ORDER BY f.departure_date'
        return self.raw_query(q)

    def remove_user(self, id):
        self.rm_seats_of_user(id)
        self.rm_user(id)

    def remove_flight(self, id):
        self.rm_seats_of_flight(id)
        self.rm_flight(id)
        return True

    def remove_aircraft(self, id):
        flights = self.get_aircraft_flights(id)
        for f in flights:
            self.remove_flight(f[0])
        self.rm_aircraft(id)

    def remove_route(self, id):
        flights = self.get_route_flights(id)
        for f in flights:
            self.remove_flight(f[0])
        self.rm_route(id)

    def remove_airport(self, id):
        routes = self.get_airport_routes(id)
        for r in routes:
            self.remove_route(r[0])
        self.rm_airport(id)
