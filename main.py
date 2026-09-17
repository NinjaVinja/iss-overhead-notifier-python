"""
ISS Overhead Notifier
---------------------
Checks every 60 seconds whether the International Space Station (ISS) is
currently overhead (within ±5° latitude/longitude of your location) AND
whether it's currently dark at your location. If both are true, it sends
you an email telling you to look up.
"""

import os
import time
import smtplib
from datetime import datetime

import requests
from dotenv import load_dotenv

# Load credentials from a local .env file (never commit this file!)
load_dotenv()

MY_LAT = 30.820663   # Your latitude
MY_LONG = 73.442467  # Your longitude

MY_EMAIL = os.getenv("MY_EMAIL")
MY_EMAIL_PASSWORD = os.getenv("MY_EMAIL_PASSWORD")


def is_iss_overhead():
    """Return True if the ISS is within ±5 degrees of MY_LAT/MY_LONG."""
    response = requests.get(url="http://api.open-notify.org/iss-now.json")
    response.raise_for_status()
    data = response.json()

    iss_latitude = float(data["iss_position"]["latitude"])
    iss_longitude = float(data["iss_position"]["longitude"])

    lat_in_range = MY_LAT - 5 <= iss_latitude <= MY_LAT + 5
    long_in_range = MY_LONG - 5 <= iss_longitude <= MY_LONG + 5

    return lat_in_range and long_in_range


def is_dark():
    """Return True if it's currently dark (before sunrise or after sunset)."""
    parameters = {
        "lat": MY_LAT,
        "lng": MY_LONG,
        "formatted": 0,
    }
    response = requests.get("https://api.sunrise-sunset.org/json", params=parameters)
    response.raise_for_status()
    data = response.json()

    sunrise = int(data["results"]["sunrise"].split("T")[1].split(":")[0])
    sunset = int(data["results"]["sunset"].split("T")[1].split(":")[0])

    current_hour = datetime.now().hour

    return current_hour >= sunset or current_hour <= sunrise


def send_alert_email():
    """Send an email telling the user to look up."""
    if not MY_EMAIL or not MY_EMAIL_PASSWORD:
        raise EnvironmentError(
            "MY_EMAIL and MY_EMAIL_PASSWORD must be set (see .env.example)."
        )

    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.starttls()
        connection.login(user=MY_EMAIL, password=MY_EMAIL_PASSWORD)
        connection.sendmail(
            from_addr=MY_EMAIL,
            to_addrs=MY_EMAIL,
            msg=(
                "Subject: Look Up! The ISS is overhead\n\n"
                "The International Space Station is currently near your "
                "location and it's dark outside. Go look up!"
            ),
        )


def main():
    print("ISS Overhead Notifier started. Checking every 60 seconds...")
    while True:
        try:
            if is_iss_overhead() and is_dark():
                send_alert_email()
                print(f"[{datetime.now()}] Alert sent — ISS is overhead and it's dark!")
            else:
                print(f"[{datetime.now()}] No match yet — still watching the sky.")
        except requests.RequestException as e:
            print(f"[{datetime.now()}] Network error, will retry: {e}")
        except EnvironmentError as e:
            print(f"[{datetime.now()}] Config error: {e}")
            break

        time.sleep(60)


if __name__ == "__main__":
    main()
