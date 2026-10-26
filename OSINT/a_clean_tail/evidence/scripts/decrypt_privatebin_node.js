const fs = require('fs');
const { webcrypto } = require('crypto');
const subtle = webcrypto.subtle;

const ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
function b58decode(s){
  let n = 0n;
  for (const c of s) n = n * 58n + BigInt(ALPHABET.indexOf(c));
  let hex = n.toString(16);
  if (hex.length % 2) hex = '0' + hex;
  let bytes = Buffer.from(hex, 'hex');
  // leading zeros
  let z = 0; for (const c of s){ if (c === ALPHABET[0]) z++; else break; }
  bytes = Buffer.concat([Buffer.alloc(z), bytes]);
  return new Uint8Array(bytes);
}
function b64d(s){ return new Uint8Array(Buffer.from(s, 'base64')); }

function strToU8(str){ return Uint8Array.from(Buffer.from(str, 'latin1')); }

(async () => {
  const pb = JSON.parse(fs.readFileSync('/tmp/opencode/paste.json','utf8'));
  const adata = pb.adata;
  const spec = adata[0].slice();
  const iv = b64d(spec[0]);
  const salt = b64d(spec[1]);
  const iters = spec[2], keysize = spec[3], tagLength = spec[4], comp = spec[7];
  const ct = b64d(pb.ct);
  const aadString = JSON.stringify(adata);
  console.log('AAD:', aadString);

  const frag = "8DPEkPZMJFcPWGWXGLbF4Nd3afesNEWs9agcT4VSsoA9";
  let key = b58decode(frag);
  // padStart(32,'\u0000') on string => left pad bytes
  if (key.length < 32) {
    const p = new Uint8Array(32); p.set(key, 32-key.length); key = p;
  }
  console.log('key len', key.length, Buffer.from(key).toString('hex'));

  const imported = await subtle.importKey('raw', key, {name:'PBKDF2'}, false, ['deriveKey']);
  const dk = await subtle.deriveKey(
    { name:'PBKDF2', salt, iterations: iters, hash:{name:'SHA-256'} },
    imported,
    { name:'AES-GCM', length: keysize },
    false, ['decrypt']
  );
  try {
    const pt = await subtle.decrypt({name:'AES-GCM', iv, additionalData: strToU8(aadString), tagLength}, dk, ct);
    let out = Buffer.from(pt);
    if (comp === 'zlib') out = require('zlib').inflateSync(out);
    console.log('=== PLAINTEXT ===');
    console.log(out.toString('utf8'));
  } catch(e) { console.error('ERR', e); }
})();
