from flask import Flask, request, Response
import os

app = Flask(__name__)

flag_path = "/app/flag.txt"

@app.route('/')
def index():
    return "I have a gift for you <a href=/source>/source</a>"

@app.get('/read')
def read_file():
    file = request.args.get("path")
    if file:
        try:
            return Response(open(file, 'r').read().strip(), mimetype='text/plain')
        except FileNotFoundError:
            return "file not found."
        except OSError:
            return "something went wrong!"
    else:
        return 'i bet this so called hackers think they have an LFI and they can just read the flag, guess what i deleted it!<br><br><img src="https://media.tenor.com/OCaZHb79uGAAAAAC/black-beard.gif" width="900" height="500"></img>'

@app.get('/source')
def read_source():
    return Response(open(__file__, 'r').read().strip(), mimetype='text/plain')

if __name__ == "__main__":
    file = open(flag_path, 'r')
    print(f"just for you admin, here is the flag: {file.read().strip()}")
    os.remove(flag_path) # totally gone
    app.run("0.0.0.0", 3000)