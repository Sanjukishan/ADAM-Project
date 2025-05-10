import speech_recognition as sr
import pyttsx3
import os
import subprocess
import pyautogui
import psutil
import pyperclip
import keyboard
import time
import datetime
import platform
import cv2
import mediapipe as mp
import numpy as np

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Speed of speech
engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)

# Initialize speech recognizer
recognizer = sr.Recognizer()

# OS-specific settings
OS = platform.system()
if OS == "Windows":
    APP_OPEN_COMMAND = "start"
    FILE_EXPLORER = "explorer"
elif OS == "Darwin":  # macOS
    APP_OPEN_COMMAND = 连锁
    FILE_EXPLORER = "open"
else:  # Linux
    APP_OPEN_COMMAND = "xdg-open"
    FILE_EXPLORER = "nautilus"

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Get screen size for mouse mapping
screen_width, screen_height = pyautogui.size()


# Speak a response
def speak(text):
    engine.say(text)
    engine.runAndWait()


# Listen for voice commands
def listen():
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio).lower()
            print(f"Command: {command}")
            return command
        except sr.UnknownValueError:
            speak("Sorry, I didn't understand that.")
            return None
        except sr.RequestError:
            speak("Sorry, there was an issue with the speech recognition service.")
            return None


# Open an application
def open_application(app_name):
    try:
        if OS == "Windows":
            subprocess.run(f"{APP_OPEN_COMMAND} {app_name}", shell=True)
        elif OS == "Darwin":
            subprocess.run(f"{APP_OPEN_COMMAND} -a {app_name}", shell=True)
        else:
            subprocess.run(f"{APP_OPEN_COMMAND} {app_name}", shell=True)
        speak(f"Opening {app_name}")
    except Exception as e:
        speak(f"Failed to open {app_name}. Error: {str(e)}")


# Create a file
def create_file(filename):
    try:
        with open(filename, 'w') as f:
            f.write("Created by Personal Assistant")
        speak(f"File {filename} created")
    except Exception as e:
        speak(f"Failed to create file. Error: {str(e)}")


# Delete a file
def delete_file(filename):
    try:
        os.remove(filename)
        speak(f"File {filename} deleted")
    except Exception as e:
        speak(f"Failed to delete file. Error: {str(e)}")


# List files in current directory
def list_files():
    files = os.listdir('.')
    speak("Files in current directory: " + ", ".join(files))
    return files


# Take a screenshot
def take_screenshot():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    screenshot = pyautogui.screenshot()
    screenshot.save(filename)
    speak(f"Screenshot saved as {filename}")


# Get system stats
def system_stats():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    battery = psutil.sensors_battery()
    battery_info = f"Battery: {battery.percent}% remaining" if battery else "No battery info"
    stats = (f"CPU usage: {cpu_usage}%. "
             f"Memory usage: {memory.percent}%. "
             f"{battery_info}")
    speak(stats)
    return stats


# Type text
def type_text(text):
    pyautogui.write(text)
    speak("Text typed")


# Shutdown the laptop
def shutdown():
    speak("Shutting down in 10 seconds")
    time.sleep(10)
    if OS == "Windows":
        subprocess.run("shutdown /s /t 0", shell=True)
    elif OS == "Darwin" or OS == "Linux":
        subprocess.run("sudo shutdown -h now", shell=True)


# Hand-tracking mouse control
def hand_tracking_mouse():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        speak("Failed to access webcam")
        return

    speak(
        "Hand tracking mode started. Use index finger to move cursor, pinch thumb and index for click. Say 'stop hand tracking' or press Esc to exit.")

    # Variables for smoothing mouse movement
    prev_x, prev_y = 0, 0
    smoothing_factor = 0.2

    while True:
        # Check for voice command to stop
        if keyboard.is_pressed('esc'):
            speak("Hand tracking stopped")
            break

        # Non-blocking voice command check
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            try:
                audio = recognizer.listen(source, timeout=0.1, phrase_time_limit=2)
                command = recognizer.recognize_google(audio).lower()
                if "stop hand tracking" in command:
                    speak("Hand tracking stopped")
                    break
            except (sr.WaitTimeoutError, sr.UnknownValueError, sr.RequestError):
                pass

        success, frame = cap.read()
        if not success:
            speak("Failed to read from webcam")
            break

        # Flip frame horizontally for natural movement
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Get index finger tip (landmark 8) and thumb tip (landmark 4)
                index_tip = hand_landmarks.landmark[8]
                thumb_tip = hand_landmarks.landmark[4]

                # Convert to pixel coordinates
                h, w, _ = frame.shape
                index_x, index_y = int(index_tip.x * w), int(index_tip.y * h)
                thumb_x, thumb_y = int(thumb_tip.x * w), int(thumb_tip.y * h)

                # Map to screen coordinates
                screen_x = np.interp(index_x, [0, w], [0, screen_width])
                screen_y = np.interp(index_y, [0, h], [0, screen_height])

                # Smooth mouse movement
                screen_x = prev_x + (screen_x - prev_x) * smoothing_factor
                screen_y = prev_y + (screen_y - prev_y) * smoothing_factor
                prev_x, prev_y = screen_x, screen_y

                # Move mouse
                pyautogui.moveTo(screen_x, screen_y)

                # Detect pinch gesture for click (thumb and index finger close)
                distance = np.sqrt((index_x - thumb_x) ** 2 + (index_y - thumb_y) ** 2)
                if distance < 30:  # Adjust threshold as needed
                    pyautogui.click()
                    time.sleep(0.2)  # Prevent multiple clicks

        # Display webcam feed
        cv2.imshow("Hand Tracking", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # Esc key
            speak("Hand tracking stopped")
            break

    cap.release()
    cv2.destroyAllWindows()


# Command handler
def handle_command(command):
    if not command:
        return False
    if "stop" in command or "exit" in command:
        speak("Goodbye")
        return False
    elif "open" in command:
        app_name = command.replace("open", "").strip()
        open_application(app_name)
    elif "create file" in command:
        filename = command.replace("create file", "").strip() or "newfile.txt"
        create_file(filename)
    elif "delete file" in command:
        filename = command.replace("delete file", "").strip()
        if filename:
            delete_file(filename)
        else:
            speak("Please specify a file to delete")
    elif "list files" in command:
        list_files()
    elif "screenshot" in command:
        take_screenshot()
    elif "system stats" in command:
        system_stats()
    elif "type" in command:
        text = command.replace("type", "").strip()
        if text:
            type_text(text)
        else:
            speak("Please specify text to type")
    elif "shutdown" in command:
        shutdown()
    elif "start hand tracking" in command:
        hand_tracking_mouse()
    else:
        speak("Command not recognized")
    return True


# Main loop
def main():
    speak("Personal Assistant started. Say 'stop' to exit or 'start hand tracking' for mouse control.")
    running = True
    while running:
        if keyboard.is_pressed('esc'):  # Emergency stop
            speak("Emergency stop activated")
            break
        command = listen()
        running = handle_command(command)
        time.sleep(0.5)  # Prevent CPU overuse


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        speak("Assistant stopped")