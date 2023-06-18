const express = require('express');
const app = express();
const bodyParser = require('body-parser');
const { v4: uuidv4 } = require('uuid');
const puppeteer = require('puppeteer');
const fs = require('fs');

app.use(bodyParser.urlencoded({ extended: false }));
app.use(express.static('public'));
app.set('debug', false);

notes = {}
reports = []

FLAG = process.env.FLAG || "akasec{ssss}"

async function reportNote(url) {
    try {
        const browser = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: "new", args: ['--no-sandbox', '--disable-setuid-sandbox'] });
        const page = await browser.newPage();
  
        await page.setCookie({
            name: 'flag',
            value: FLAG,
            domain: 'localhost:3000'
        });
        await page.goto(`http://localhost:3000`);
        await page.evaluate((url) => {
            location.href = url;
        }, url);
        await new Promise(resolve => setTimeout(resolve, 5000));
        await browser.close();
    } catch (err) {
        console.log("?:", err);
    }
}

app.get('/', (req, res) => {
    res.sendFile(__dirname + '/public/index.html');
});

app.post('/save', (req, res) => {
    if (Object.keys(notes).length > 100)
        notes = {}
    text = req.body.text;
    if (text.length > 1000)
        res.send('Note too long!');
    else {
        uid = uuidv4();
        notes[uid] = text;
        res.send(`note saved successfully, <a href=/notes/${uid}>link</a>.`);
    }
});

app.get('/notes/:uid', (req, res) => {
    const { uid } = req.params;
    const uidPattern = /^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-4[a-fA-F0-9]{3}-[89aAbB][a-fA-F0-9]{3}-[a-fA-F0-9]{12}$/;
  
    if (uidPattern.test(uid)) {
        if (uid in notes) {
            html = `
            <table>
              <thead>
                <tr>
                  <th>UID</th>
                  <th>Note</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>${uid}</td>
                  <td>${notes[uid]}</td>
                  <td>
                    <button onclick="fetch('/report/${uid}').then(response => response.text()).then(data => alert(data)).catch(error => alert(error));">share with admin</button>
                  </td>
                </tr>
              </tbody>
            </table>
          `;
          res.send(html);
        } else {
            res.send('Note not found.');
        }
    } else {
        res.send('Invalid UID.');
    }
});


app.get('/report/:uid', (req, res) => {
    if (reports.length > 100)
        reports = []
    const { uid } = req.params;
    const uidPattern = /^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-4[a-fA-F0-9]{3}-[89aAbB][a-fA-F0-9]{3}-[a-fA-F0-9]{12}$/;

    if (uidPattern.test(uid))
    {
        if (reports.indexOf(uid) != -1)
            res.send("this note has already been shared with admin!");
        else
        {
            reportNote(`/notes/${uid}`);
            reports.push(uid);
            res.send("note has been sent to the admin!");
        }
    }
});

app.get('/source', (req, res) => {
    fs.readFile('index.js', 'utf8', (err, data) => {
      if (err) {
        console.error(`Error reading file: ${err}`);
        return res.status(500).send('Internal Server Error');
      }
      res.set('Content-Type', 'text/plain');
      res.send(data);
    });
});


const port = 3000;
app.listen(port, () => {
    console.log(`Server is listening on port ${port}`);
});
