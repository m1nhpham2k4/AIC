// frontend/scripts/make-manifest.mjs
import { promises as fs } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Root chứa ảnh keyframes (ngoài frontend)
const srcRoot = path.resolve(__dirname, '../../Data_extraction/Keyframes_test')

// Nơi ghi manifest (public)
const outFile = path.resolve(__dirname, '../public/keyframes-manifest.json')

// Nếu bạn đã tạo junction: public/keyframes -> Data_extraction/Keyframes_test
// thì base URL là /keyframes
const publicBase = '/keyframes'

// --- helpers ---
const isDir = async p => (await fs.lstat(p)).isDirectory()
const isFile = async p => (await fs.lstat(p)).isFile()
const isJpg = f => /\.jpe?g$/i.test(f)

function joinUrlEncoded(...segs) {
  // encode từng segment để giữ nguyên dấu '/'
  return segs.map(s => encodeURIComponent(s)).join('/')
}

// Duyệt đệ quy, gom các thư mục lá có ảnh .jpg
async function walk(dir, rel = '') {
  const entries = await fs.readdir(dir)
  const folders = []
  const files = []

  for (const name of entries) {
    const abs = path.join(dir, name)
    if (await isDir(abs)) folders.push(name)
    else if (await isFile(abs) && isJpg(name)) files.push(name)
  }

  // Nếu có ảnh .jpg ở thư mục hiện tại, coi đây là một leaf
  const leaf = files.length > 0 ? {
    relPath: rel, // ví dụ: "Keyframes_L01 keyframes/L01_V001"
    images: files.sort().map(f =>
      publicBase + '/' + joinUrlEncoded(...rel.split('/')) + '/' + encodeURIComponent(f)
    )
  } : null

  // Duyệt sâu hơn
  const kids = []
  for (const f of folders) {
    const child = await walk(path.join(dir, f), rel ? `${rel}/${f}` : f)
    kids.push(...child)
  }

  return leaf ? [leaf, ...kids] : kids
}

async function main() {
  // đảm bảo srcRoot tồn tại
  await fs.access(srcRoot)

  const leaves = await walk(srcRoot, '')
  const manifest = {}

  // key trong manifest là đường dẫn tương đối từ srcRoot, dùng dấu '/'
  for (const leaf of leaves) {
    if (!leaf.relPath) continue
    manifest[leaf.relPath] = leaf.images
  }

  await fs.mkdir(path.dirname(outFile), { recursive: true })
  await fs.writeFile(outFile, JSON.stringify(manifest, null, 2), 'utf8')
  console.log(`Wrote ${outFile} with ${Object.keys(manifest).length} folders`)
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
