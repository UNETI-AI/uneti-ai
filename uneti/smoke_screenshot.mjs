// Open the running app like a person would and save what it shows (uneti-smoke.yml).
import { chromium } from "playwright";

const base = "http://127.0.0.1:7777";
const out = process.env.OUT;
const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, locale: "vi-VN" });
const page = await context.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(String(error)));

await page.goto(base, { waitUntil: "load" });
await page.waitForTimeout(3000);
await page.screenshot({ path: `${out}/1-dang-nhap.png` });

const login = await context.request.post(`${base}/auth/login`, {
  form: { username: process.env.ADMIN_USER, password: process.env.ADMIN_PASS },
  headers: { Origin: base },
});
console.log("dang nhap:", login.status());

await page.goto(base, { waitUntil: "load" });
await page.waitForTimeout(6000);
await page.screenshot({ path: `${out}/2-sau-dang-nhap.png` });
console.log("tieu de:", await page.title());

const news = await (await context.request.get(`${base}/notifications`)).json();
console.log("tin:", (news.items || []).filter((item) => item.kind !== "update").map((item) => item.title));
console.log("loi tren trang:", errors.length ? errors.slice(0, 5) : "khong co");

await browser.close();
