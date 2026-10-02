import fs from "node:fs/promises";
const artifactModule = process.env.ARTIFACT_TOOL_MODULE || `${process.cwd()}/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs`;
const { Presentation, PresentationFile } = await import(artifactModule);

const out = new URL("../tests/fixtures/", import.meta.url).pathname;
const W = 1280, H = 720;
const addText = (slide, value, x, y, w, h, size, color = "#162326", typeface = "DejaVu Sans") => {
  const box = slide.shapes.add({ geometry: "textbox", position: { left: x, top: y, width: w, height: h }, fill: "none", line: { style: "solid", fill: "none", width: 0 } });
  box.text = value;
  box.text.style = { fontSize: size / 0.75, color, typeface, insets: { top: 0, right: 0, bottom: 0, left: 0 } };
};
const addSlide = (pres, bg = "#F7FAF9") => {
  const slide = pres.slides.add();
  slide.background.fill = bg;
  return slide;
};
const save = async (pres, name) => {
  const pptx = await PresentationFile.exportPptx(pres);
  await pptx.save(`${out}${name}`);
};

await fs.mkdir(out, { recursive: true });
let p = Presentation.create({ slideSize: { width: W, height: H } });
let s = addSlide(p); addText(s, "Good fixture", 80, 70, 700, 60, 34); addText(s, "Readable clinical teaching point\nOne concise supporting line.", 80, 180, 700, 150, 24); await save(p, "good.pptx");
p = Presentation.create({ slideSize: { width: W, height: H } });
s = addSlide(p); addText(s, "Overflow fixture", 80, 70, 700, 60, 34); addText(s, "This deliberately long sentence is placed in a very short text box so the preflight and render checks have a known hard failure to detect.", 80, 180, 480, 45, 24); await save(p, "overflow.pptx");
p = Presentation.create({ slideSize: { width: W, height: H } });
s = addSlide(p, "#EAF3F1"); addText(s, "Contrast fixture", 80, 70, 700, 60, 34, "#EAF3F1"); await save(p, "contrast.pptx");
p = Presentation.create({ slideSize: { width: W, height: H } });
s = addSlide(p); addText(s, "Clinical lint fixture", 80, 70, 700, 60, 34); addText(s, "FDA-approved product; use 5U daily and double the dose if needed.", 80, 180, 900, 100, 24); await save(p, "clinical_bad.pptx");
p = Presentation.create({ slideSize: { width: W, height: H } });
s = addSlide(p); addText(s, "Missing font fixture", 80, 70, 700, 60, 34, "#162326", "Papyrus"); addText(s, "Font substitution should be reported.", 80, 180, 700, 80, 24, "#162326", "Papyrus"); await save(p, "missing_font.pptx");
p = Presentation.create({ slideSize: { width: W, height: H } });
s = addSlide(p); addText(s, "Dense citations fixture", 80, 70, 900, 60, 34); addText(s, "1. Trial A. Journal. 2022;1:1. 2. Trial B. Journal. 2023;2:2. 3. Guideline C. Society. 2024. 4. Review D. Journal. 2025;4:4. 5. Label E. Manufacturer. 2026. 6. Meta-analysis F. Journal. 2026;6:6.", 80, 180, 1080, 100, 12, "#536366"); await save(p, "dense_citations.pptx");
