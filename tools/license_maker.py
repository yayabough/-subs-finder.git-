#!/usr/bin/env python3
import os, json, argparse, time, base64
from pathlib import Path
from secrets import token_hex

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import serialization, hashes
except Exception:
    print("Install dependency first: pip install cryptography")
    raise

PRODUCT_NAME = 'SubsFinder Pro (Offline)'
KEY_DIR = Path('keys')
PRIV_PATH = KEY_DIR / 'private_key.pem'
PUB_SPKI_B64_PATH = KEY_DIR / 'public_key_spki.b64'

def b64(x: bytes) -> str:
    return base64.b64encode(x).decode('ascii')

def ensure_keys():
    KEY_DIR.mkdir(exist_ok=True)
    if PRIV_PATH.exists() and PUB_SPKI_B64_PATH.exists():
        print("Keys already exist.\nPublic SPKI (paste into index.html):\n")
        print(PUB_SPKI_B64_PATH.read_text().strip())
        return
    print("Generating RSA keypair (2048-bit)…")
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    PRIV_PATH.write_bytes(pem)
    public_key = private_key.public_key()
    spki_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    PUB_SPKI_B64_PATH.write_text(b64(spki_der))
    print("Done. Public SPKI (paste into index.html PUBLIC_KEY_SPKI_B64):\n")
    print(b64(spki_der))

def make_license(name: str, email: str, plan: str, lifetime: bool = True) -> str:
    if not PRIV_PATH.exists():
        raise SystemExit("No private key. Run with --init first.")
    private_key = serialization.load_pem_private_key(PRIV_PATH.read_bytes(), password=None)
    payload = {
        "product": PRODUCT_NAME,
        "name": name,
        "email": email,
        "plan": plan,
        "lifetime": bool(lifetime),
        "issued_at": int(time.time()),
        "nonce": token_hex(8)
    }
    payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode('utf-8')
    signature = private_key.sign(
        payload_json,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=32),
        hashes.SHA256()
    )
    lic = f"{b64(payload_json)}.{b64(signature)}"
    outdir = Path('licenses'); outdir.mkdir(exist_ok=True)
    safe = email.replace('@', '_at_').replace(':', '_')
    (outdir / f"{int(time.time())}_{safe}.lic").write_text(lic)
    return lic

def main():
    ap = argparse.ArgumentParser(description="SubsFinder license tool")
    ap.add_argument('--init', action='store_true', help='generate keys and print public key SPKI base64')
    ap.add_argument('--make', action='store_true', help='make a license (requires --name and --email)')
    ap.add_argument('--name', type=str)
    ap.add_argument('--email', type=str)
    ap.add_argument('--plan', type=str, default='Pro')
    ap.add_argument('--lifetime', type=int, default=1)
    args = ap.parse_args()
    if args.init:
        ensure_keys(); return
    if args.make:
        if not args.name or not args.email:
            raise SystemExit('--make requires --name and --email')
        lic = make_license(args.name, args.email, args.plan, bool(args.lifetime))
        print("\nLICENSE STRING:\n")
        print(lic)
        return
    ap.print_help()

if __name__ == '__main__':
    main()
