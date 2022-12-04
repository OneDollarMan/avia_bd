from mysql.connector import connect, Error


class Repo:
    ROLE_PASSENGER = 0
    ROLE_SELLER = 1
    ROLE_ADMINISTRATOR = 2

    def __init__(self, host, user, password, db):
        self.connection = None
        self.cursor = None
        self.connect_to_db(host, user, password, db)
        if self.connection is not None and self.cursor is not None:
            self.select_db(db)
            self.get_tables = lambda: self.raw_query("SHOW TABLES")

            self.get_user = lambda username: self.get_query("SELECT * FROM user WHERE username='%s'" % username)
            self.get_all_users = lambda: self.raw_query("SELECT * FROM user JOIN role ON user.role_id=role.id")
            self.login_user = lambda username, password: self.get_query(
                "SELECT * FROM user WHERE username='%s' AND password='%s'" % (username, password))
            self.add_u = lambda username, password, fio, d_id, d_n, role: self.write_query(
                f"INSERT INTO user SET username='{username}', fio='{fio}', password='{password}', document_id='{d_id}', document_number='{d_n}', role_id='{role}'")
            self.get_all_zero_users = lambda: self.raw_query("SELECT * FROM user WHERE role=0")
            self.rm_user = lambda id: self.write_query(f"DELETE FROM user WHERE id='{id}'")

            self.get_roles = lambda: self.raw_query("SELECT * from role")

            self.select_documents = lambda: self.raw_query("SELECT * FROM document")

            self.add_aircraft = lambda name, capacity, plate: self.write_query(
                f"INSERT INTO aircraft SET name='{name}', capacity='{capacity}', plate='{plate}'")
            self.get_aircrafts = lambda: self.raw_query("SELECT * FROM aircraft")
            self.select_aircrafts = lambda: self.raw_query("SELECT id, name FROM aircraft")
            self.get_aircraft = lambda id: self.get_query(f"SELECT * FROM aircraft WHERE id='{id}'")
            self.rm_aircraft = lambda id: self.write_query(f"DELETE FROM aircraft WHERE id='{id}'")

            self.add_airport = lambda name, city, address: self.write_query(f"INSERT INTO airport SET name='{name}', city='{city}', address='{address}'")
            self.get_airports = lambda: self.raw_query("SELECT * FROM airport")
            self.select_airports = lambda: self.raw_query("SELECT id, name FROM airport")
            self.get_airport = lambda id: self.raw_query(f"SELECT * FROM airport WHERE id='{id}'")
            self.rm_airport = lambda id: self.raw_query(f"DELETE FROM airport WHERE id='{id}'")

            self.add_route = lambda number, a1, a2, price, flight_time: self.write_query(f"INSERT INTO route SET number='{number}', departure_airport_id='{a1}', destination_airport_id='{a2}', price='{price}', flight_time='{flight_time}'")
            self.get_routes = lambda: self.raw_query("SELECT r.*, a1.name, a2.name FROM route r JOIN airport a1, airport a2 WHERE r.departure_airport_id=a1.id AND r.destination_airport_id=a2.id")
            self.select_routes = lambda: self.raw_query("SELECT id, number FROM route")

            self.add_flight = lambda route_id, aircraft_id, date: self.write_query(f"INSERT INTO flight SET route_id='{route_id}', aircraft_id='{aircraft_id}', departure_date='{date}'")
            self.get_flights = lambda: self.raw_query("SELECT f.id, f.departure_date, CONCAT(a1.name, ' - ', a2.name), CONCAT(a.name, ' (', a.plate, ')'), (SELECT COUNT(*) FROM seat WHERE flight_id=f.id), a.capacity FROM flight f JOIN route r, aircraft a, airport a1, airport a2 WHERE f.route_id=r.id AND f.aircraft_id=a.id AND r.departure_airport_id=a1.id AND r.destination_airport_id=a2.id")
            self.get_flight = lambda id: self.raw_query(f"SELECT * FROM flight WHERE id='{id}'")
            self.get_aircraft_capacity = lambda flight_id: self.get_one_query(f"SELECT a.capacity FROM flight f JOIN aircraft a ON f.aircraft_id=a.id WHERE f.id='{flight_id}'")

            self.add_seat = lambda flight_id, user_id, date: self.write_query(f"INSERT INTO seat SET flight_id='{flight_id}', user_id={user_id}, purchase_date='{date}'")
            self.get_seats_amount = lambda flight_id: self.get_one_query(f"SELECT COUNT(*) FROM seat WHERE flight_id='{flight_id}'")
            self.get_seat_by_user_and_flight = lambda fid, uid: self.raw_query(f"SELECT * FROM seat WHERE flight_id='{fid}' AND user_id='{uid}'")
            self.get_seats_of_user = lambda id: self.raw_query(f"SELECT seat.id, departure_date, flight_time, CONCAT(a.name, ' ', plate), CONCAT(a1.name, ' - ', a2.name) FROM seat JOIN flight f, route r, aircraft a, airport a1, airport a2 WHERE seat.flight_id=f.id AND f.route_id=r.id AND f.aircraft_id=a.id AND r.departure_airport_id=a1.id AND r.destination_airport_id=a2.id AND seat.user_id='1'")
            self.rm_seat = lambda id, uid: self.write_query(f"DELETE FROM seat WHERE id='{id}' AND user_id='{uid}'")

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

    def buy_ticket(self, flight_id, user_id, date):
        a = self.get_seats_amount(flight_id)
        c = self.get_aircraft_capacity(flight_id)
        if a < c and len(self.get_seat_by_user_and_flight(flight_id, user_id)) == 0:
            self.add_seat(flight_id, user_id, date)
            return True
        return False

    def get_contract_sorted(self, start_date, end_date, customer, status):
        q = "SELECT * FROM contract c LEFT JOIN (SELECT f.contract_id, SUM(f.amount * price) FROM food_has_contract f JOIN food ON f.food_id=food.id GROUP BY f.contract_id) s ON c.id=s.contract_id INNER JOIN customer cs, status st WHERE c.customer_id=cs.id AND c.status_id=st.id"
        if start_date:
            q = q + f" AND delivery_date > '{start_date}'"
        if end_date:
            q = q + f" AND delivery_date < '{end_date}'"
        if customer:
            q = q + f" AND customer_id = '{customer}'"
        if status:
            q = q + f" AND status_id = '{status}'"
        q = q + ' ORDER BY date'
        return self.raw_query(q)

