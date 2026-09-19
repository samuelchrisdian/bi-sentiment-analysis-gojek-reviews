/* Pemeriksaan asap terhadap Definition of Done Fase 8.
 *
 *   1. npm run build && npx vite preview --port 4173
 *   2. pastikan API berjalan di :8000
 *   3. npm run smoke -- <folder-tangkapan-layar>
 *
 * Skrip inilah yang dipakai untuk memverifikasi butir DoD yang hanya bisa
 * dibuktikan di peramban nyata: konsistensi filter, drill-down, empty state,
 * kebersihan konsol, dan layout 768px. */
import { chromium } from "playwright";

const OUT = process.argv[2];
const URL = process.env.SMOKE_URL || "http://localhost:4173";
const b = await chromium.launch();
const page = await b.newPage({ viewport: { width: 1440, height: 1000 } });

/* Langkah "empty state" sengaja meminta rentang di luar korpus, dan API
   menjawabnya dengan 404. Peramban mencatat SETIAP respons 404 sebagai error
   konsol, jadi catatan itu dipisahkan dari error yang benar-benar berasal dari
   aplikasi — kalau digabung, butir DoD "konsol bersih" jadi mustahil diuji. */
let sedangMengujiKosong = false;
const errors = [];
const diharapkan = [];

const catat = (baris) =>
  (sedangMengujiKosong && /404/.test(baris) ? diharapkan : errors).push(baris);

page.on("console", (m) => {
  if (m.type() === "error" || m.type() === "warning") catat(`[${m.type()}] ${m.text()}`);
});
page.on("pageerror", (e) => errors.push(`[pageerror] ${e.message}`));

await page.goto(URL + "/", { waitUntil: "networkidle" });
await page.waitForTimeout(1500);

const step = async (nama, fn) => {
  try { await fn(); console.log(`PASS ${nama}`); }
  catch (e) { console.log(`FAIL ${nama}: ${e.message.split("\n")[0]}`); }
};

// 1. KPI terisi dari API
await step("KPI hero terisi", async () => {
  const t = await page.locator(".tile__hero").first().innerText();
  if (!/\d/.test(t)) throw new Error("hero kosong: " + t);
  console.log("      hero =", t);
});

// 2. Grafik ter-render (canvas ECharts)
await step("Grafik ter-render", async () => {
  const n = await page.locator("canvas").count();
  if (n < 4) throw new Error(`hanya ${n} canvas`);
  console.log("      canvas =", n);
});

// 3. Filter memengaruhi seluruh grafik
await step("Filter mengubah KPI + tren", async () => {
  const sebelumKpi = await page.locator(".tile__hero").first().innerText();
  const sebelumBaris = await page.locator("text=Bulanan").count();
  await page.locator('button:has-text("2025 saja")').click();
  await page.waitForTimeout(1800);
  const sesudahKpi = await page.locator(".tile__hero").first().innerText();
  if (sebelumKpi === sesudahKpi) throw new Error("KPI tidak berubah: " + sebelumKpi);
  console.log(`      ${sebelumKpi} -> ${sesudahKpi}`);
  // kembalikan ke default
  await page.locator('button:has-text("Seluruh periode penuh")').click();
  await page.waitForTimeout(1500);
});

// 4. Tabel twin
await step("Alih tabel tren", async () => {
  const kartu = page.locator(".panel", { hasText: "Tren sentimen antarwaktu" }).first();
  await kartu.locator('button:has-text("Tabel")').click();
  await page.waitForTimeout(400);
  const baris = await kartu.locator("tbody tr").count();
  if (baris < 5) throw new Error(`hanya ${baris} baris`);
  console.log("      baris tabel =", baris);
  await kartu.locator('button:has-text("Grafik")').click();
  await page.waitForTimeout(300);
});

// 5. Drill-down: klik batang topik
await step("Klik batang topik membuka ulasan", async () => {
  const kartu = page.locator(".panel", { hasText: "Kategori keluhan" }).first();
  const canvas = kartu.locator("canvas").first();
  await canvas.scrollIntoViewIfNeeded();
  await page.waitForTimeout(400);
  const box = await canvas.boundingBox();
  await page.mouse.click(box.x + box.width * 0.5, box.y + box.height * 0.08);
  await page.waitForTimeout(2500);

  const judul = await page.locator(".panel-ulasan .card__title").innerText();
  if (!judul.includes("—")) throw new Error("kategori tidak terpilih: " + judul);
  const n = await page.locator(".panel-ulasan .ulasan").count();
  if (n === 0) throw new Error("tabel ulasan kosong");

  // tabel harus ikut ter-scroll ke tampilan
  const terlihat = await page.locator(".panel-ulasan").evaluate((el) => {
    const r = el.getBoundingClientRect();
    return r.top < window.innerHeight && r.bottom > 0;
  });
  if (!terlihat) throw new Error("tabel ulasan tidak ter-scroll ke tampilan");

  // urutan likes desc
  const likes = await page.locator(".panel-ulasan .ulasan .meta").allInnerTexts();
  const angka = likes.map((t) => Number((t.match(/([\d.]+) likes/) || [])[1]?.replace(/\./g, "")));
  const turun = angka.every((v, i, a) => i === 0 || a[i - 1] >= v);
  if (!turun) throw new Error("tidak terurut likes desc: " + angka.join(","));
  console.log(`      ${judul.trim()} · ${n} ulasan · likes desc ok`);
});

// 6. Paginasi
await step("Paginasi ulasan", async () => {
  const sebelum = await page.locator(".panel-ulasan .ulasan .teks").first().innerText();
  await page.locator('.panel-ulasan button:has-text("Berikutnya")').click();
  await page.waitForTimeout(1500);
  const sesudah = await page.locator(".panel-ulasan .ulasan .teks").first().innerText();
  if (sebelum === sesudah) throw new Error("halaman tidak berubah");
});

// 7. Demo prediksi
await step("Demo prediksi", async () => {
  await page.locator("textarea").fill("driver batalin pesanan sepihak lagi lagi");
  await page.locator('button:has-text("Prediksi")').click();
  await page.waitForTimeout(2500);
  const label = await page.locator(".keluar .tag").innerText();
  const pre = await page.locator(".keluar .mono").innerText();
  console.log(`      ${label.trim()} · pre="${pre.trim()}"`);
});

// 8. Empty state via rentang tanpa data
await step("Empty state", async () => {
  sedangMengujiKosong = true;
  // rentang di luar korpus -> API mengembalikan 404 -> keadaan KOSONG
  await page.evaluate(() => document.querySelectorAll('input[type="date"]')
    .forEach((i) => i.removeAttribute("max")));
  await page.locator('input[type="date"]').nth(1).fill("2026-06-30");
  await page.locator('input[type="date"]').first().fill("2026-06-01");
  await page.waitForTimeout(2600);

  const pesan = await page.locator(".kosong .pesan").first().innerText();
  const tombol = await page.locator('.kosong button:has-text("Atur ulang filter")').count();
  if (!tombol) throw new Error("tombol reset tidak ada");
  console.log(`      "${pesan}" · ${tombol} tombol reset`);

  await page.locator('.kosong button:has-text("Atur ulang filter")').first().click();
  await page.waitForTimeout(2000);
  const pulih = await page.locator(".tile__hero").first().innerText();
  if (!/\d/.test(pulih)) throw new Error("tidak pulih setelah reset");
  console.log("      pulih ke " + pulih);
  sedangMengujiKosong = false;
});

// 9. Lebar 768
await step("Layout 768px", async () => {
  await page.setViewportSize({ width: 768, height: 1200 });
  await page.waitForTimeout(900);
  const overflow = await page.evaluate(() =>
    document.documentElement.scrollWidth - document.documentElement.clientWidth);
  if (overflow > 0) throw new Error(`scroll horizontal ${overflow}px`);
  if (OUT) await page.screenshot({ path: OUT + "/dashboard-768.png", fullPage: true });
});

// tangkapan layar utama
await page.setViewportSize({ width: 1440, height: 1000 });
await page.waitForTimeout(1200);
if (OUT) await page.screenshot({ path: OUT + "/dashboard-full.png", fullPage: true });

console.log("\n--- konsol ---");
console.log(errors.length
  ? "GAGAL — error/warning tak terduga:\n" + errors.join("\n")
  : "bersih: tidak ada error/warning aplikasi");
console.log(`(${diharapkan.length} catatan 404 yang diharapkan dari uji empty state, diabaikan)`);

await b.close();
process.exit(errors.length ? 1 : 0);
