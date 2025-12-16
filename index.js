const path = require("path");

const express = require("express");
const fs = require("fs");

const app = express();
app.engine("html", require("ejs").renderFile);
app.set("view engine", "html");
app.set("views", __dirname);

app.get("/", function (req, res) {
  res.sendFile(path.join(__dirname, "/main.html"));
});

app.get("/data/:uuid", function (req, res) {
  let data = JSON.parse(fs.readFileSync(`./data/${req.params.uuid}.json`));
  let { mileage } = JSON.parse(fs.readFileSync(`./mileage.json`));
  mileage = (mileage * 2).toFixed(2) + " miles"
  res.render(path.join(__dirname, "/index.html"), { data, mileage });
});

app.get("/isready/:uuid", function (req, res) {
  const path = `./data/${req.params.uuid}.json`;

  if (fs.existsSync(path)) {
    res.send({ ready: true });
  } else {
    res.send({ ready: false });
  }
});

const { spawn } = require("child_process");

app.get("/generate/:mileage", function (req, res) {
  let uuid = crypto.randomUUID();
  let mileage = Number(req.params.mileage);

  const process = spawn("python3", ["algorithm.py", uuid, mileage]);

  process.stdout.on("data", (data) => {
    console.log(`Output: ${data}`);
  });

  process.stderr.on("data", (data) => {
    console.error(`Error: ${data}`);
  });

  process.on("close", (code) => {
    console.log(`Exited w/ ${code}`);
  });

  res.send({ uuid });
});

app.listen(3000);
