import speech_recognition as sr
import pyttsx3
import pywhatkit
import webbrowser
import subprocess
import threading
import requests
import smtplib
import imaplib
import email
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import scrolledtext
import random
import os
import psutil  # For battery percentage
import pyjokes
import schedule
import time
import re
from geopy.geocoders import Nominatim
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Initialize the recognizer and the text-to-speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# List to store tasks
todo_list = []

# Email credentials (use environment variables for security)
EMAIL_ADDRESS = "senudajayathilaka0@gmail.com"
EMAIL_PASSWORD = "smov dopq lrvi ihas"

# API keys (use environment variables for security)
WEATHER_API_KEY = "ee7f02ba25283a4ab7e813d71803146c"
NEWS_API_KEY = "f5d6b457e0e44a99a063b1203adb832e"

# Google Calendar API setup
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google_calendar():
    """Authenticate and return the Google Calendar service."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('calendar', 'v3', credentials=creds)
    return service

def create_calendar_event(summary, start_time, end_time):
    """Create a calendar event."""
    service = authenticate_google_calendar()
    event = {
        'summary': summary,
        'start': {
            'dateTime': start_time,
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'UTC',
        },
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    speak(f"Event created: {event.get('htmlLink')}")

def list_calendar_events():
    """List upcoming calendar events."""
    service = authenticate_google_calendar()
    now = datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    if not events:
        speak('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        speak(f"{start} - {event['summary']}")

    webbrowser.open("https://calendar.google.com")

def list_events_for_today():
    """List today's calendar events."""
    service = authenticate_google_calendar()
    now = datetime.datetime.utcnow()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'
    try:
        events_result = service.events().list(calendarId='primary', timeMin=start_of_day,
                                              timeMax=end_of_day, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])
        if not events:
            speak('No events found for today.')
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            speak(f"{start} - {event['summary']}")
    except Exception as e:
        speak(f"An error occurred: {e}")
        print(f"Error: {e}")

    webbrowser.open("https://calendar.google.com")

def speak(text):
    """Function to convert text to speech."""
    engine.say(text)
    engine.runAndWait()
    output_text.insert(tk.END, f"{text}\n")
    output_text.see(tk.END)

def speak(text):
    """Function to convert text to speech."""
    engine.say(text)
    engine.runAndWait()
    output_text.insert(tk.END, f"{text}\n")
    output_text.see(tk.END)

def add_to_todo(task):
    """Add a task to the to-do list."""
    todo_list.append(task)
    speak(f"Task '{task}' added to your to-do list.")

def show_todo():
    """Show all tasks in the to-do list."""
    if todo_list:
        tasks = "\n".join(todo_list)
        speak(f"Your to-do list:\n{tasks}")
    else:
        speak("Your to-do list is empty.")

def get_location():
    """Get the user's current location based on their IP address."""
    try:
        response = requests.get('https://ipinfo.io')
        data = response.json()
        loc = data['loc'].split(',')
        latitude = loc[0]
        longitude = loc[1]
        return latitude, longitude
    except Exception as e:
        speak("Failed to get location. Please check your internet connection.")
        print(f"Error: {e}")
        return None, None

def get_weather(city, forecast=False):
    """Fetch weather information for a city or based on the user's location."""
    if not city:
        latitude, longitude = get_location()
        if latitude and longitude:
            if forecast:
                base_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&appid={WEATHER_API_KEY}&units=metric"
            else:
                base_url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={WEATHER_API_KEY}&units=metric"
        else:
            speak("Unable to determine location. Please specify a city name.")
            return
    else:
        if forecast:
            base_url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric"
        else:
            base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"

    print(f"API URL: {base_url}")  # Debugging

    try:
        response = requests.get(base_url)
        data = response.json()
        print(f"Weather API Response: {data}")  # Debugging
        if response.status_code == 200:
            if forecast:
                # Find the forecast for tomorrow
                tomorrow = datetime.utcnow() + timedelta(days=1)
                forecast_data = None
                for entry in data['list']:
                    forecast_time = datetime.strptime(entry['dt_txt'], '%Y-%m-%d %H:%M:%S')
                    if forecast_time.date() == tomorrow.date() and forecast_time.hour == 12:
                        forecast_data = entry
                        break
                if forecast_data:
                    main = forecast_data["main"]
                    weather = forecast_data["weather"][0]
                    temperature = main["temp"]
                    description = weather["description"]
                    location_name = data["city"]["name"]
                    speak(f"The forecast for tomorrow in {location_name} is {temperature}°C with {description}.")
                else:
                    speak("Unable to fetch the weather forecast for tomorrow.")
            else:
                main = data["main"]
                weather = data["weather"][0]
                temperature = main["temp"]
                description = weather["description"]
                location_name = data["name"]
                speak(f"The temperature in {location_name} is {temperature}°C with {description}.")
        else:
            speak("City not found or unable to fetch weather data.")
    except Exception as e:
        speak("Failed to fetch weather data. Please check your internet connection.")
        print(f"Error: {e}")

def is_valid_email(email):
    """Check if the email address is valid."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def get_news():
    """Fetch the latest news headlines."""
    base_url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(base_url)
        data = response.json()
        print(f"News API Response: {data}")  # Debugging
        if data["status"] == "ok":
            articles = data["articles"]
            headlines = [article["title"] for article in articles[:5]]
            news = "\n".join(headlines)
            speak(f"Here are the top news headlines:\n{news}")
        else:
            speak("Unable to fetch news.")
    except Exception as e:
        speak("Failed to fetch news. Please check your internet connection.")
        print(f"Error: {e}")

def play_youtube(video):
    """Play a YouTube video."""
    pywhatkit.playonyt(video)
    speak(f"Playing {video} on YouTube.")

def convert_to_24_hour_format(time_str):
    """Convert 12-hour time format to 24-hour time format."""
    try:
        in_time = datetime.strptime(time_str, "%I:%M %p")
        out_time = datetime.strftime(in_time, "%H:%M")
        return out_time
    except ValueError as e:
        speak("Invalid time format. Please use 'HH:MM AM/PM'.")
        print(f"Error: {e}")
        return None

def set_reminder(date_time, task):
    """Function to set a reminder."""
    try:
        reminder_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M")
        now = datetime.now()
        delay = (reminder_time - now).total_seconds()
        if delay > 0:
            schedule.every(delay).seconds.do(speak, f"Reminder: {task}")
            speak(f"Reminder set for {date_time}.")
        else:
            speak("The specified time is in the past. Please try again.")
    except ValueError as e:
        speak("Failed to set reminder. Please check the date and time format.")
        print(f"Error: {e}")

def set_reminder_interactive():
    """Interactive function to set a reminder."""
    try:
        speak("For which date? (say 'today' or 'tomorrow')")
        reminder_date = take_command()
        if reminder_date == "today":
            reminder_date = datetime.now().strftime("%Y-%m-%d")
        elif reminder_date == "tomorrow":
            reminder_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            speak("Please provide the date in YYYY-MM-DD format.")
            reminder_date = take_command()

        speak("At what time? (e.g., 3:00 PM)")
        reminder_time = take_command()
        reminder_time_24 = convert_to_24_hour_format(reminder_time)
        if reminder_time_24 is None:
            return  # Exit if the time format is invalid

        speak("What should I remind you about?")
        reminder_task = take_command()

        reminder_date_time = f"{reminder_date} {reminder_time_24}"
        set_reminder(reminder_date_time, reminder_task)
    except Exception as e:
        speak("An error occurred while setting the reminder.")
        print(f"Error: {e}")

def take_command():
    """Function to take a voice command using Google Web Speech API."""
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening...")
            audio = recognizer.listen(source, timeout=5)  # Add timeout
    except sr.WaitTimeoutError:
        speak("I didn't hear anything. Please try again.")
        return ""  # Return an empty string instead of None
    except sr.UnknownValueError:
        speak("Sorry, I didn't understand that.")
        return ""  # Return an empty string instead of None
    except sr.RequestError:
        speak("Network error. Please check your connection.")
        return ""  # Return an empty string instead of None
    except Exception as e:
        speak("An error occurred. Please check your microphone.")
        print(f"Error: {e}")
        return ""  # Return an empty string instead of None

    try:
        command = recognizer.recognize_google(audio)
        print(f"You said: {command}")
        return command.lower()
    except Exception as e:
        speak("Sorry, I couldn't process your command.")
        print(f"Error: {e}")
        return ""  # Return an empty string instead of None

def get_current_time():
    """Function to get the current time."""
    now = datetime.now().strftime("%H:%M")
    speak(f"The current time is {now}.")

def send_email_command():
    """Function to handle sending an email."""
    try:
        # Get recipient email from keyboard input
        recipient = input("Please type the recipient's email address: ")
        
        # Validate email address
        while not is_valid_email(recipient):
            print("Invalid email address. Please type it again.")
            recipient = input("Please type the recipient's email address: ")

        # Get email subject from keyboard input
        subject = input("Please type the subject of the email: ")

        # Get email body from keyboard input
        body = input("Please type the body of the email: ")

        # Send the email
        send_email(recipient, subject, body)
    except Exception as ex:
        print("Error sending email:", ex)
        speak("An error occurred while sending the email. Please try again.")

def send_email(to, subject, body):
    """Function to send an email."""
    if not is_valid_email(to):
        speak("The recipient's email address is invalid. Please check and try again.")
        return

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(EMAIL_ADDRESS, to, message)
        speak("Email sent successfully.")
    except smtplib.SMTPAuthenticationError:
        speak("Failed to send email. Please check your email credentials.")
    except Exception as e:
        speak("Failed to send email. Please check your internet connection.")
        print(f"Error: {e}")

def read_emails():
    """Function to read emails."""
    try:
        # Debugging: Print email credentials
        print(f"EMAIL_ADDRESS: {EMAIL_ADDRESS}")
        print(f"EMAIL_PASSWORD: {'*' * len(EMAIL_PASSWORD) if EMAIL_PASSWORD else None}")

        if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
            raise ValueError("Email credentials are not set properly.")

        with imaplib.IMAP4_SSL("imap.gmail.com") as mail:
            mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            mail.select("inbox")
            status, messages = mail.search(None, "UNSEEN")
            email_ids = messages[0].split()
            if email_ids:
                for email_id in email_ids:
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject = msg["subject"]
                            from_ = msg["from"]
                            speak(f"New email from {from_} with subject: {subject}")
            else:
                speak("No new emails.")
    except imaplib.IMAP4.error as e:
        speak("Failed to authenticate with the email server. Please check your credentials.")
        print(f"IMAP4 error: {e}")
    except ValueError as e:
        speak(str(e))
        print(f"ValueError: {e}")
    except Exception as e:
        speak("Failed to read emails.")
        print(f"Error: {e}")

def tell_joke():
    """Function to tell a joke."""
    joke = pyjokes.get_joke()
    speak(joke)

def open_website(website):
    """Open a website in the default web browser."""
    url_map = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "wikipedia": "https://www.wikipedia.org",
        "facebook": "https://www.facebook.com",
        "twitter": "https://www.twitter.com",
        "gmail": "https://mail.google.com",
    }
    if website in url_map:
        webbrowser.open(url_map[website])
        speak(f"Opening {website}.")
    else:
        # Check if the website is a valid URL
        if not website.startswith("http://") and not website.startswith("https://"):
            website = "http://" + website
        try:
            webbrowser.open(website)
            speak(f"Opening {website}.")
        except Exception as e:
            speak(f"Failed to open {website}. Please specify a valid website.")
            print(f"Error: {e}")

def open_application(app_name):
    """Open a common application."""
    app_map = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "command prompt": "cmd.exe",
        "file explorer": "explorer.exe",
    }
    if app_name in app_map:
        subprocess.run(app_map[app_name], shell=True)
        speak(f"Opening {app_name}.")
    else:
        speak("I don't know that application.")

def get_battery_status():
    """Get the current battery percentage."""
    try:
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            speak(f"Your device is at {percent} percent battery.")
        else:
            speak("Battery information is not available on this system.")
    except Exception as e:
        speak("Failed to retrieve battery status.")
        print(f"Error: {e}")

# Command processing logic
commands = {
    "hi": lambda cmd: speak("Hello! How can I assist you today?"),
    "hello": lambda cmd: speak("Hello! How can I assist you today?"),
    "how are you": lambda cmd: speak("I'm just a program, but I'm here to help you!"),
    "who made you": lambda cmd: speak("I was created by a developer who loves AI and automation."),
    "who created you": lambda cmd: speak("I was created by a developer who loves AI and automation."),
    "are you a robot": lambda cmd: speak("Yes, I am an AI assistant, but I try to be as helpful as possible!"),
    "shutdown": lambda cmd: (speak("Shutting down the system. Goodbye!"), os.system("shutdown /s /t 5")),
    "restart": lambda cmd: (speak("Restarting the system. Please wait."), os.system("shutdown /r /t 5")),
    "log off": lambda cmd: (speak("Logging out of your account."), os.system("shutdown -l")),
    "sign out": lambda cmd: (speak("Logging out of your account."), os.system("shutdown -l")),
    "open google": lambda cmd: open_website("google"),
    "open youtube": lambda cmd: open_website("youtube"),
    "open wikipedia": lambda cmd: open_website("wikipedia"),
    "open facebook": lambda cmd: open_website("facebook"),
    "open twitter": lambda cmd: open_website("twitter"),
    "open gmail": lambda cmd: open_website("gmail"),
    "open notepad": lambda cmd: open_application("notepad"),
    "open calculator": lambda cmd: open_application("calculator"),
    "open command prompt": lambda cmd: open_application("command prompt"),
    "open file explorer": lambda cmd: open_application("file explorer"),
    "battery percentage": lambda cmd: get_battery_status(),
    "tell me a joke": lambda cmd: tell_joke(),
    "joke": lambda cmd: tell_joke(),
    "time": lambda cmd: get_current_time(),
    "read emails": lambda cmd: read_emails(),
    "read email": lambda cmd: read_emails(),
    "add task": lambda cmd: add_to_todo(cmd.replace("add task", "").strip()),
    "show tasks": lambda cmd: show_todo(),
    "show to-do list": lambda cmd: show_todo(),
    "show to-do": lambda cmd: show_todo(),
    "show reminders": lambda cmd: show_todo(),
    "show task": lambda cmd: show_todo(),
    "send email": lambda cmd: send_email_command(),
    "exit": lambda cmd: (speak("Thank you. Goodbye!"), root.quit()),
    "open": lambda cmd: open_website(cmd.replace("open", "").strip()),
    "set reminder": lambda cmd: set_reminder_interactive(),
    "how is the weather in": lambda cmd: get_weather(cmd.replace("how is the weather in", "").strip()),
    "how is the weather now": lambda cmd: get_weather(cmd.replace("how is the weather now", "").strip()),
    "how is the weather tomorrow": lambda cmd: get_weather(cmd.replace("how is the weather tomorrow", "").strip(), forecast=True),
    "news": lambda cmd: get_news(),
    "play": lambda cmd: play_youtube(cmd.replace("play", "").strip()),
    "reminder": lambda cmd: set_reminder_interactive(),
    "reminder for": lambda cmd: set_reminder_interactive(),
    "reminder at": lambda cmd: set_reminder_interactive(),
    "reminder on": lambda cmd: set_reminder_interactive(),
    "reminder to": lambda cmd: set_reminder_interactive(),
    "reminder tomorrow": lambda cmd: set_reminder_interactive(),
    "reminder today": lambda cmd: set_reminder_interactive(),
    "create event": lambda cmd: create_calendar_event_interactive(),
    "list events": lambda cmd: list_calendar_events(),
    "list calendar events": lambda cmd: list_calendar_events(),
    "list event for today": lambda cmd: list_events_for_today(),
    "open": lambda cmd: open_website(cmd.replace("open", "").strip()),
}

def create_calendar_event_interactive():
    """Interactive function to create a calendar event."""
    try:
        speak("What is the event title?")
        summary = input("Please type the event title: ")

        speak("When does the event start? (YYYY-MM-DD HH:MM)")
        start_time = input("Please type the start time (YYYY-MM-DD HH:MM): ")

        speak("When does the event end? (YYYY-MM-DD HH:MM)")
        end_time = input("Please type the end time (YYYY-MM-DD HH:MM): ")

        create_calendar_event(summary, start_time, end_time)
    except Exception as e:
        speak("An error occurred while creating the event.")
        print(f"Error: {e}")

def process_command(command):
    """Process the command using NLP."""
    if not command:  # Check if the command is empty
        speak("I didn't catch that. Please try again.")
        return

    print(f"Processing command: {command}")
    for key, func in commands.items():
        if key in command:
            func(command)  # Pass 'command' to the lambda function
            return
    speak("Sorry, I didn't understand that command. Can you please rephrase?")

def cmd():
    """Function to recognize speech and execute commands."""
    command = take_command()
    if command:
        process_command(command)

# Tkinter UI
def start_listening():
    listen_button.config(text="Listening...", state=tk.DISABLED)
    cmd()
    listen_button.config(text="Start Listening", state=tk.NORMAL)

root = tk.Tk()
root.title("Personal Assistant")

frame = tk.Frame(root)
frame.pack(pady=10)

output_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=50, height=20)
output_text.pack(padx=10, pady=10)

listen_button = tk.Button(frame, text="Start Listening", command=start_listening)
listen_button.pack(pady=10)

# Speak greeting only once at the beginning
speak("Hello, I am your personal assistant. How can I help you today?")

# Run the scheduler in a separate thread
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

root.mainloop()