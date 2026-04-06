import fs from "fs";
import path from "path";
import OpenAI from "openai";

function loadEnvFile(envPath = ".env") {
  if (!fs.existsSync(envPath)) return;
  const raw = fs.readFileSync(envPath, "utf8");
  for (const line of raw.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    let value = trimmed.slice(eq + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    if (!(key in process.env)) {
      process.env[key] = value;
    }
  }
}

function parseArgs(argv) {
  const args = { manifest: null, only: null };
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === "--manifest") {
      args.manifest = argv[i + 1];
      i += 1;
    } else if (token === "--only") {
      args.only = argv[i + 1];
      i += 1;
    } else if (!args.manifest && !token.startsWith("--")) {
      args.manifest = token;
    }
  }
  return args;
}

function ensureDir(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function decodeAndWritePng(base64Data, outputPath) {
  const buffer = Buffer.from(base64Data, "base64");
  ensureDir(outputPath);
  fs.writeFileSync(outputPath, buffer);
}

function writeMetadata(outputPath, metadata) {
  const metadataPath = `${outputPath}.json`;
  fs.writeFileSync(metadataPath, JSON.stringify(metadata, null, 2) + "\n");
}

function usage() {
  console.log(
    [
      "Usage:",
      "  node scripts/generate_illustrations.mjs --manifest data/illustrations/ch-001.json",
      "  node scripts/generate_illustrations.mjs --manifest data/illustrations/ch-001.json --only hero"
    ].join("\n")
  );
}

loadEnvFile();

const { manifest, only } = parseArgs(process.argv.slice(2));

if (!manifest) {
  usage();
  process.exit(1);
}

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and set your key.");
  process.exit(1);
}

const manifestPath = path.resolve(manifest);
const manifestData = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
const model = process.env.OPENAI_MODEL || manifestData.model || "gpt-5";

const selected = only
  ? manifestData.images.filter((image) => image.id === only)
  : manifestData.images;

if (selected.length === 0) {
  console.error(`No images selected from ${manifest}.`);
  process.exit(1);
}

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

for (const image of selected) {
  const outputPath = path.resolve(image.output);
  console.log(`Generating ${image.id} -> ${image.output}`);

  const response = await client.responses.create({
    model,
    input: image.prompt,
    tools: [{ type: "image_generation" }]
  });

  const generation = response.output.find(
    (item) => item.type === "image_generation_call" && item.result
  );

  if (!generation) {
    console.error(`No image_generation_call result returned for ${image.id}.`);
    process.exit(1);
  }

  decodeAndWritePng(generation.result, outputPath);
  writeMetadata(outputPath, {
    chapter: manifestData.chapter,
    id: image.id,
    model,
    output: image.output,
    prompt: image.prompt,
    response_id: response.id,
    revised_prompt: generation.revised_prompt || null,
    generated_at: new Date().toISOString()
  });

  console.log(`Saved ${image.output}`);
}
