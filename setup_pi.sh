# Creating a new venv environment and activate it
python -m venv /home/jun/Desktop/environment
cd environment
source bin/activate

# Install text-to-speech
sudo apt update && sudo apt install espeak ffmpeg libespeak1
pip install pyttsx3 flask flask-socketio

# Clone the working directory
git clone https://github.com/Jhewu/raspberry.git
cd raspberry