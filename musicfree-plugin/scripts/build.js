const fs = require("fs");
const path = require("path");

const src = path.join(__dirname, "..", "src", "plugin.js");
const dist = path.join(__dirname, "..", "dist", "plugin.js");

const content = fs.readFileSync(src, "utf-8");
fs.writeFileSync(dist, content, "utf-8");
console.log("✅ 插件构建完成:", dist);