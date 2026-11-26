from flask import Flask, render_template
import threading
from geopy.distance import geodesic
import mysql.connector
import random

app = Flask(__name__)

# --------------------------------
# DATABASE SETTINGS
# --------------------------------

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "Leosaa07",
    "database": "europe_airport_game"
}


def create_connection():
    return mysql.connector.connect(**DB_CONFIG)


try:
    connection = create_connection()
    cursor = connection.cursor()
    print("CONNECTED!")

except mysql.connector.Error as error:
    print("MYSQL ERROR:")
    print(error)
    raise


# --------------------------------
# FLASK LEADERBOARD
# --------------------------------

@app.route("/")
def leaderboard():

    web_connection = None
    web_cursor = None

    try:
        web_connection = create_connection()
        web_cursor = web_connection.cursor()

        web_cursor.execute("""
            SELECT
                screen_name,
                Goal_points,
                Flights_completed,
                distance
            FROM player
            ORDER BY Goal_points DESC
            LIMIT 15
        """)

        players = web_cursor.fetchall()

        return render_template(
            "leaderboard.html",
            scores=players
        )

    except mysql.connector.Error as error:
        return f"Database error: {error}", 500

    finally:
        if web_cursor:
            web_cursor.close()

        if web_connection and web_connection.is_connected():
            web_connection.close()


def start_website():
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )


# --------------------------------
# CHECK USERNAME
# --------------------------------

def get_username(username):

    cursor.execute(
        "SELECT id FROM player WHERE id = %s",
        (username,)
    )

    return cursor.fetchone() is not None


# --------------------------------
# GET 4 AIRPORTS
# --------------------------------

def hae_lentokentat(current_airport):

    cursor.execute("""
        SELECT name, ident
        FROM airport
        WHERE type = 'large_airport'
        AND continent = 'EU'
        AND ident != %s
    """, (current_airport,))

    lentokentat = cursor.fetchall()

    if len(lentokentat) < 4:
        raise ValueError("Not enough airports found in database.")

    return random.sample(lentokentat, 4)


# --------------------------------
# FIND AIRPORT COORDINATES
# --------------------------------

def find_destination(destination):

    cursor.execute("""
        SELECT latitude_deg, longitude_deg
        FROM airport
        WHERE ident = %s
    """, (destination,))

    result = cursor.fetchone()

    if result is None:
        raise ValueError(f"Airport not found: {destination}")

    return result


# --------------------------------
# CALCULATE DISTANCE
# --------------------------------

def calculate_distance(departure, destination):

    return geodesic(departure, destination).kilometers


# --------------------------------
# CALCULATE FUEL
# --------------------------------

def fuel_consumed(distance, weather):

    fuel = distance

    if weather == "Cloudy":
        fuel *= 1.05

    elif weather == "Storm":
        fuel *= 1.15

    return fuel


# --------------------------------
# CALCULATE CO2
# --------------------------------

def co2_consumed(fuel):

    return fuel * 0.5


# --------------------------------
# CALCULATE POINTS
# --------------------------------

def calculate_points(distance, co2):

    if co2 <= 500:
        points = distance * 0.1 + 20

    elif co2 <= 1000:
        points = distance * 0.1

    else:
        points = distance * 0.1 - 10

    return points


# --------------------------------
# UPDATE DATABASE
# --------------------------------

def update_data(
    username,
    destination,
    distance,
    fuel,
    co2,
    points
):

    cursor.execute("""
        UPDATE player
        SET
            current_airport = %s,
            Destination = %s,
            distance = distance + %s,
            Total_fuel = Total_fuel - %s,
            Total_fuel_consumed = Total_fuel_consumed + %s,
            Co2_consumed = Co2_consumed + %s,
            Goal_points = Goal_points + %s,
            Flights_completed = Flights_completed + 1
        WHERE id = %s
    """, (
        destination,
        destination,
        distance,
        fuel,
        fuel,
        co2,
        points,
        username
    ))

    connection.commit()


# --------------------------------
# REFILL FUEL
# --------------------------------

def refill_fuel(username):

    cursor.execute("""
        UPDATE player
        SET
            Total_fuel = Total_fuel + 2000,
            Goal_points = Goal_points - 20
        WHERE id = %s
        AND Goal_points >= 20
    """, (username,))

    connection.commit()

    if cursor.rowcount > 0:

        print("\nYou bought 2000 litres of fuel.")
        print("20 points were deducted.")

        return True

    print("\nYou do not have enough points.")
    return False


# --------------------------------
# SHOW PLAYER
# --------------------------------

def show_player(username):

    cursor.execute("""
        SELECT
            current_airport,
            Total_fuel,
            Total_fuel_consumed,
            Co2_consumed,
            Goal_points,
            Flights_completed,
            distance
        FROM player
        WHERE id = %s
    """, (username,))

    player = cursor.fetchone()

    if player is None:
        raise ValueError("Player not found.")

    print("\n")
    print("------------------------------")
    print("PLAYER INFORMATION")
    print("------------------------------")

    print("Current airport:", player[0])
    print("Fuel remaining:", round(player[1] or 0, 2), "litres")
    print("Fuel consumed:", round(player[2] or 0, 2), "litres")
    print("CO2 produced:", round(player[3] or 0, 2), "kg")
    print("Points:", round(player[4] or 0, 2))
    print("Flights completed:", player[5])
    print("Total distance:", round(player[6] or 0, 2), "km")


# --------------------------------
# SHOW CONSOLE LEADERBOARD
# --------------------------------

def show_leaderboard():

    cursor.execute("""
        SELECT
            screen_name,
            Goal_points,
            Flights_completed,
            distance
        FROM player
        ORDER BY Goal_points DESC
        LIMIT 15
    """)

    players = cursor.fetchall()

    print("\n")
    print("==============================")
    print("        LEADERBOARD")
    print("==============================")

    for number, player in enumerate(players, start=1):

        print(
            number,
            player[0],
            "-",
            round(player[1] or 0, 2),
            "points",
            "-",
            player[2],
            "flights",
            "-",
            round(player[3] or 0, 2),
            "km"
        )

    print("==============================")


# --------------------------------
# START WEBSITE IN BACKGROUND
# --------------------------------

web_thread = threading.Thread(
    target=start_website,
    daemon=True
)

web_thread.start()


# --------------------------------
# ACTUAL GAME
# --------------------------------

username = input(
    "Enter your username\nNote: User name should be unique: "
)

if get_username(username):

    print("Welcome back!")

else:

    print("New player!")
    screen_name = input("Enter your name: ")

    cursor.execute("""
        INSERT INTO player (
            id,
            screen_name,
            current_airport
        )
        VALUES (%s, %s, %s)
    """, (
        username,
        screen_name,
        "LFPK"
    ))

    connection.commit()

    print("Player created successfully.")
    print("Starting GAME EUROPE AIRPORT SIMULATOR.")
    print("======================")
    print("Starting game from LFPK airport.")


# --------------------------------
# GAME LOOP
# --------------------------------

while True:

    cursor.execute("""
        SELECT
            current_airport,
            Total_fuel,
            Total_fuel_consumed,
            Co2_consumed,
            Goal_points,
            Flights_completed,
            distance,
            Co2_Max
        FROM player
        WHERE id = %s
    """, (username,))

    player = cursor.fetchone()

    if player is None:
        print("Player not found.")
        break

    current_airport = player[0]
    total_fuel = player[1] or 0
    total_fuel_consumed = player[2] or 0
    total_co2 = player[3] or 0
    points = player[4] or 0
    flights = player[5] or 0
    total_distance = player[6] or 0
    maximum_co2_limit = player[7]

    show_player(username)

    # CHECK WINNING CONDITION

    if points >= 500 and total_co2 < maximum_co2_limit:

        print("\n==============================")
        print("       CONGRATULATIONS!")
        print("==============================")

        print("You reached 500 points and won the game.")
        print("Flights completed:", flights)
        print("Total distance:", round(total_distance, 2), "km")
        print("Total fuel consumed:", round(total_fuel_consumed, 2), "litres")
        print("Total CO2 produced:", round(total_co2, 2), "kg")
        print("Final points:", round(points, 2))

        show_leaderboard()
        break

    elif total_co2 >= maximum_co2_limit:

        print("Caught By the Activists.")
        break

    # GET AIRPORTS

    airports = hae_lentokentat(current_airport)

    print("\nChoose your destination Airport:")

    for i, airport in enumerate(airports, start=1):

        print(
            i,
            airport[0],
            "(" + airport[1] + ")"
        )

    print("5. Show leaderboard")
    print("6. Quit")

    choice = input("Choose an option from 1 - 6: ")

    if choice == "5":

        show_leaderboard()
        continue

    if choice == "6":

        print("Game is quit.")
        print(f"You have completed {flights} flights.")
        break

    if not choice.isdigit():

        print("Please enter a number from 1 - 6.")
        continue

    choice = int(choice)

    if choice < 1 or choice > 4:

        print("Invalid choice.")
        continue

    # SELECT DESTINATION

    destination = airports[choice - 1]

    destination_name = destination[0]
    destination_ident = destination[1]

    departure_coordinates = find_destination(current_airport)
    destination_coordinates = find_destination(destination_ident)

    distance = calculate_distance(
        departure_coordinates,
        destination_coordinates
    )

    weather = random.choice([
        "Clear",
        "Cloudy",
        "Storm"
    ])

    fuel = fuel_consumed(distance, weather)

    co2 = co2_consumed(fuel)

    flight_points = calculate_points(distance, co2)

    print("\n")
    print("==============================")
    print("       FLIGHT INFORMATION")
    print("==============================")

    print("From:", current_airport)
    print("To:", destination_name)
    print("Weather:", weather)
    print("Distance:", round(distance, 2), "km")
    print("Fuel needed:", round(fuel, 2), "litres")
    print("CO2:", round(co2, 2), "kg")
    print("Points:", round(flight_points, 2))

    print("==============================")

    # CHECK FUEL

    if total_fuel < fuel:

        print("\nYou don't have enough fuel.")

        print("Fuel available:", round(total_fuel, 2), "litres")
        print("Fuel needed:", round(fuel, 2), "litres")

        refill = input(
            "\nBuy 2000 litres for 20 points? (y/n): "
        )

        if refill.lower() == "y":

            if refill_fuel(username):

                print("Fuel refilled.")
                print("Please select the flight again.")

            continue

        else:

            print("Flight cancelled.")
            continue

    # CONFIRM FLIGHT

    fly = input("\nDo you want to take this flight (y/n): ")

    if fly.lower() != "y":

        print("Flight is cancelled.")
        continue

    # UPDATE DATABASE

    update_data(
        username,
        destination_ident,
        distance,
        fuel,
        co2,
        flight_points
    )

    cursor.execute("""
        SELECT Flights_completed
        FROM player
        WHERE id = %s
    """, (username,))

    completed_flights = cursor.fetchone()[0]

    print("\n==============================")
    print("       FLIGHT COMPLETED")
    print("==============================")

    print("You earned", round(flight_points, 2), "points.")
    print("Flights completed:", completed_flights)


# --------------------------------
# CLOSE DATABASE
# --------------------------------

cursor.close()
connection.close()

print("Game ended.")
