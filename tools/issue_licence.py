# tools/issue_license.py
import time, uuid, argparse, json
from jose import jwt

def issue(private_key_pem, customer_id, plan, duration_days, product_id="myapp", features=None, hw=None):
    now = int(time.time())
    payload = {
        "sub": customer_id,
        "lic": str(uuid.uuid4()),
        "pid": product_id,
        "ver": ">=1.0.0,<2.0.0",
        "iat": now,
        "exp": now + duration_days*24*3600,
        "plan": plan,
        "feats": features or {},
        "hw": hw,  # optional machine binding
        "nonce": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, private_key_pem, algorithm="RS256")
    return token

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--private-key-file", required=True)
    ap.add_argument("--customer-id", required=True)
    ap.add_argument("--plan", choices=["weekly","monthly","quarterly","yearly"], required=True)
    ap.add_argument("--duration-days", type=int)  # override explicit
    ap.add_argument("--hw")  # optional hardware fingerprint
    ap.add_argument("--out", required=True)  # output license file path
    args = ap.parse_args()

    with open(args.private_key_file, "r", encoding="utf-8") as f:
        priv = f.read()

    plan_days = {
        "weekly": 7,
        "monthly": 30,
        "quarterly": 90,
        "yearly": 365,
    }
    days = args.duration_days or plan_days[args.plan]
    token = issue(priv, args.customer_id, args.plan, days, hw=args.hw)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(token)
    print(f"Issued license: {args.out}")