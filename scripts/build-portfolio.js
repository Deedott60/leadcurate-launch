#!/usr/bin/env node

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

function valueAfter(flag) {
  const index = process.argv.indexOf(flag);
  return index === -1 ? null : process.argv[index + 1];
}

const portfolioDir = path.join(os.homedir(), "Documents", "portfolio");
const sourcePath = path.resolve(valueAfter("--source") || path.join(portfolioDir, "template.html"));
const outputPath = path.resolve(valueAfter("--output") || path.join(portfolioDir, "index.html"));
const shotsDir = path.resolve(valueAfter("--shots") || path.join(path.dirname(sourcePath), "shots"));

const assets = {
  IMG_ROOTED: "rooted-desktop.jpg",
  IMG_ANN: "ann-reveal.jpg",
  IMG_LETTER: "ann-letter.jpg",
};

function dataUri(filePath) {
  const extension = path.extname(filePath).toLowerCase();
  const mimeType = extension === ".png" ? "image/png" : "image/jpeg";
  return `data:${mimeType};base64,${fs.readFileSync(filePath).toString("base64")}`;
}

let html = fs.readFileSync(sourcePath, "utf8");

for (const [token, fileName] of Object.entries(assets)) {
  const marker = `{{${token}}}`;
  if (!html.includes(marker)) {
    throw new Error(`Missing template marker: ${marker}`);
  }
  html = html.replaceAll(marker, dataUri(path.join(shotsDir, fileName)));
}

const unresolved = html.match(/\{\{IMG_[A-Z0-9_]+\}\}/g);
if (unresolved) {
  throw new Error(`Unresolved image markers: ${unresolved.join(", ")}`);
}

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, html, "utf8");

console.log(`Built ${outputPath}`);
