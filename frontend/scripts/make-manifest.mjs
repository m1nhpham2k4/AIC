import { writeFile, mkdir } from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import 'dotenv/config';
import {
  S3Client,
  ListObjectsV2Command,
  HeadObjectCommand,
} from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';

const __filename = fileURLToPath(import.meta.url);
const __dirname  = path.dirname(__filename);

// ========= ENV =========
const REGION   = process.env.AWS_REGION || 'ap-southeast-1';
const BUCKET   = process.env.AWS_BUCKET_NAME;
const ROOT     = (process.env.S3_ROOT_PREFIX || 'Keyframes_test/').replace(/^\/+/, '');
const USE_PRESIGN = String(process.env.USE_PRESIGN || 'true').toLowerCase() === 'true';
const PRESIGN_TTL = Number(process.env.PRESIGN_TTL || 3600);

// File output (public folder của FE)
const OUT_FILE = path.resolve(__dirname, '../public/keyframes-manifest.json');

// ========= S3 CLIENT =========
const s3 = new S3Client({ region: REGION });

// ========= Helpers =========
const isImage = (key) => /\.(jpe?g|png)$/i.test(key);

// encode từng segment (để giữ nguyên dấu '/')
function encodePathForUrl(key) {
  return key.split('/').map(encodeURIComponent).join('/');
}

// Tạo URL public (nếu bucket public) hoặc presigned (nếu private)
async function toUrl(key) {
  if (USE_PRESIGN) {
    const cmd = new HeadObjectCommand({ Bucket: BUCKET, Key: key });
    await s3.send(cmd); // xác thực tồn tại; nếu 404 sẽ throw
    const getCmd = new HeadObjectCommand({ Bucket: BUCKET, Key: key }); // trick: presign GET Object
    // dùng GET Object Command thực sự:
    const { GetObjectCommand } = await import('@aws-sdk/client-s3');
    const getObj = new GetObjectCommand({ Bucket: BUCKET, Key: key });
    return getSignedUrl(s3, getObj, { expiresIn: PRESIGN_TTL });
  } else {
    // URL kiểu "virtual-hosted–style"
    // Lưu ý: nếu bạn dùng CloudFront, thay domain này bằng domain CloudFront
    return `https://${BUCKET}.s3.${REGION}.amazonaws.com/${encodePathForUrl(key)}`;
  }
}

// Liệt kê TẤT CẢ object dưới ROOT (phân trang)
async function listAllKeys(prefix) {
  const keys = [];
  let token = undefined;
  do {
    const resp = await s3.send(new ListObjectsV2Command({
      Bucket: BUCKET,
      Prefix: prefix,
      ContinuationToken: token,
    }));
    for (const obj of resp.Contents || []) {
      keys.push(obj.Key);
    }
    token = resp.IsTruncated ? resp.NextContinuationToken : undefined;
  } while (token);
  return keys;
}

// Group theo “leaf” = thư mục chứa ảnh (directory của file)
// Ví dụ key: Keyframes_test/Keyframes_L01/keyframes/L01_V001/001.jpg
// -> leafPath: "Keyframes_L01/keyframes/L01_V001"
function extractLeafPath(key) {
  // bỏ ROOT ở đầu
  let rel = key.startsWith(ROOT) ? key.slice(ROOT.length) : key;
  const parts = rel.split('/').filter(Boolean);
  if (parts.length < 2) return null; // không đủ cấu trúc
  // remove file name
  parts.pop(); // bỏ "001.jpg"
  return parts.join('/');
}

// ========= MAIN =========
async function main() {
  if (!BUCKET) throw new Error('Missing AWS_BUCKET_NAME in env');
  const allKeys = await listAllKeys(ROOT);

  // Lọc ảnh
  const imageKeys = allKeys.filter(isImage);

  // Gom theo leaf
  const manifest = {};
  for (const key of imageKeys) {
    const leaf = extractLeafPath(key);
    if (!leaf) continue;
    if (!manifest[leaf]) manifest[leaf] = [];
    manifest[leaf].push(key);
  }

  // Sort ảnh trong từng leaf theo tên file (tăng dần)
  for (const leaf of Object.keys(manifest)) {
    manifest[leaf].sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
  }

  // Đổi từ key -> URL
  const out = {};
  for (const [leaf, keys] of Object.entries(manifest)) {
    const urls = [];
    for (const k of keys) {
      try {
        urls.push(await toUrl(k));
      } catch {
        // bỏ qua key không tồn tại/không truy cập được
      }
    }
    // Chỉ ghi leaf có ảnh hợp lệ
    if (urls.length) out[leaf] = urls;
  }

  await mkdir(path.dirname(OUT_FILE), { recursive: true });
  await writeFile(OUT_FILE, JSON.stringify(out, null, 2), 'utf8');
  console.log(`Wrote ${OUT_FILE} with ${Object.keys(out).length} leaves`);
}

main().catch((err) => {
  console.error('Failed to make manifest from S3:', err);
  process.exit(1);
});
