/* Tangkapan layar dashboard resolusi tinggi untuk naskah (docs/figures/).
 *
 *   docker compose up -d   # API + dashboard dengan data dan artefak model
 *   node scripts/screenshots.mjs <folder-keluaran>
 */
import { chromium } from "playwright";

const OUT = process.argv[2] || "../docs/figures";
const URL = process.env.SHOT_URL || "http://localhost:5173";
const b = await chromium.launch();
const page = await b.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 2 });
const tunggu = (ms) => page.waitForTimeout(ms);
const panel = (judul) => page.locator(".panel", { hasText: judul }).first();
const simpan = async (loc, nama) => {
  await loc.scrollIntoViewIfNeeded();
  await tunggu(800);
  await loc.screenshot({ path: `${OUT}/${nama}.png` });
  console.log("ditulis", nama);
};

await page.goto(URL + "/", { waitUntil: "networkidle" });
await tunggu(2500);
await page.screenshot({ path: `${OUT}/gambar-13a-dashboard-ringkasan.png`, fullPage: true });
console.log("ditulis gambar-13a-dashboard-ringkasan");

await simpan(page.locator("section.blok").first(), "gambar-13b-kpi");
await simpan(panel("Tren sentimen antarwaktu"), "gambar-13c-tren");
await simpan(panel("Sentimen per versi aplikasi"), "gambar-13d-versi");

// Drill-down: kategori teratas -> teks ulasan asli
const canvas = panel("Kategori keluhan").locator("canvas").first();
await canvas.scrollIntoViewIfNeeded();
await tunggu(500);
const box = await canvas.boundingBox();
await page.mouse.click(box.x + box.width * 0.5, box.y + box.height * 0.08);
await tunggu(2500);
await simpan(panel("Kategori keluhan"), "gambar-13e-kategori");
await simpan(page.locator(".panel-ulasan"), "gambar-13f-ulasan");
await page.screenshot({ path: `${OUT}/gambar-13-dashboard.png`, fullPage: true });
console.log("ditulis gambar-13-dashboard");

await simpan(panel("Perbandingan model"), "gambar-13g-model");
await page.locator("textarea").fill("driver batalin pesanan sepihak, saldo gopay juga belum masuk");
await page.locator('button:has-text("Prediksi")').click();
await tunggu(2500);
await simpan(page.locator("section.card", { hasText: "Coba prediksi" }), "gambar-13h-prediksi");

await b.close();
