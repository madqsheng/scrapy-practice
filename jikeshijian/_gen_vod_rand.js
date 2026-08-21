// 生成阿里云 VOD 加密视频 GetPlayInfo 所需的 Rand 参数。
// Rand 不是随机字节：它是 Aliplayer 2.8.2 加密分支 _sce_lgtcaygl(_sce_r_skjhfnck())
// 的输出（64 字节随机数的加密结果，算法与密钥封装在阿里云 jsvm 虚拟机里，无法静态复现）。
// 因此这里在 Node + jsdom 环境里真实运行 Aliplayer 的加密模块来生成。
// 输出：一行 base64（88 字符），写到 stdout。
// 注意：不能加 "use strict"——strict 模式会让 eval 的 var/function 声明被隔离，
// webpack bundle 的模块注册表无法泄漏到外层，require 会报 Cannot find module。
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const dom = new JSDOM("<!doctype html><html><body></body></html>", {
  url: "https://example.com/",
  pretendToBeVisual: true,
});
const w = dom.window;
for (const k of Object.getOwnPropertyNames(w)) {
  if (!(k in global)) {
    try { global[k] = w[k]; } catch (e) { /* 忽略只读属性 */ }
  }
}
global.window = w;
global.self = w;

const base = __dirname;
eval(fs.readFileSync(path.join(base, "_aliplayer_282.js"), "utf8"));
eval(fs.readFileSync(path.join(base, "_aliplayer_vod_282.js"), "utf8"));
// UMD 在 Node 里走 CommonJS 分支，posdk 挂在 exports 上；补挂到全局
if (typeof posdk === "undefined" && exports.posdk) {
  global.posdk = exports.posdk;
}
process.stdout.write(_sce_lgtcaygl(_sce_r_skjhfnck()));
