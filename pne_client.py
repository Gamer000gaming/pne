import requests, hashlib, base64
from nacl import public, signing, utils, secret

def generate_keys(address_password: str):
    seed = hashlib.sha256(address_password.encode()).digest()
    signing_key = signing.SigningKey(seed)
    verify_key = signing_key.verify_key
    return signing_key, verify_key

def ed25519_to_x25519(signing_key, verify_key):
    priv_x = signing_key.to_curve25519_private_key()
    pub_x = verify_key.to_curve25519_public_key()
    return priv_x, pub_x

def encrypt_message(shared_key: bytes, message: str):
    box = secret.SecretBox(shared_key)
    nonce = utils.random(secret.SecretBox.NONCE_SIZE)
    enc = box.encrypt(message.encode(), nonce)
    return base64.b64encode(enc).decode()

def decrypt_message(shared_key: bytes, ciphertext_b64: str):
    box = secret.SecretBox(shared_key)
    enc = base64.b64decode(ciphertext_b64)
    return box.decrypt(enc).decode()

def parse_address(addr: str):
    user, host_port = addr.split('@')
    if ':' in host_port:
        host, port = host_port.split(':')
    else:
        host, port = host_port, "16361"
    return user, host, int(port)

address = input("PNE address (user@host[:port]): ")
password = input("Password: ")

user, host, port = parse_address(address)
node_url = f"http://{host}:{port}"

signing_key, verify_key = generate_keys(f"{address}:{password}")
priv_x, pub_x = ed25519_to_x25519(signing_key, verify_key)

pub_b64 = base64.b64encode(pub_x.encode()).decode()
res = requests.post(f"{node_url}/register",
                    json={"username": user, "public_key": pub_b64})
print(res.text)

while True:
    cmd = input("PNE> ").strip()
    if cmd.startswith("send"):
        try:
            _, to_addr = cmd.split()
        except:
            print("Usage: send <user@host[:port]>")
            continue
        msg = input("Message: ")
        msg_hash = hashlib.sha256(msg.encode()).hexdigest()

        
        to_user, to_host, to_port = parse_address(to_addr)
        to_node_url = f"http://{to_host}:{to_port}"

        
        r = requests.get(f"{to_node_url}/pubkey/{to_user}")
        if r.status_code != 200:
            print(f"Recipient {to_addr} not found")
            continue
        recv_pub_x = public.PublicKey(base64.b64decode(r.text.encode()))

        
        box = public.Box(priv_x, recv_pub_x)
        shared_key = hashlib.sha256(box.shared_key()).digest()

        
        enc_msg = encrypt_message(shared_key, msg)

        
        data = {"to": to_addr, "from": address, "message": enc_msg, "hash": msg_hash}
        res = requests.post(f"{to_node_url}/receive", json=data)
        print(res.text)

    elif cmd.startswith("fetch"):
        r = requests.get(f"{node_url}/fetch/{user}")
        if r.status_code != 200:
            print("Error fetching messages")
            continue
        msgs = r.json()
        confirmed = []
        for m in msgs:
            from_addr = m['from']
            from_user, from_host, from_port = parse_address(from_addr)
            from_node_url = f"http://{from_host}:{from_port}"

            
            r_pub = requests.get(f"{from_node_url}/pubkey/{from_user}")
            if r_pub.status_code != 200:
                print(f"Cannot fetch sender public key for {from_addr}")
                continue
            sender_pub_x = public.PublicKey(base64.b64decode(r_pub.text.encode()))

            
            box = public.Box(priv_x, sender_pub_x)
            shared_key = hashlib.sha256(box.shared_key()).digest()

            
            try:
                plaintext = decrypt_message(shared_key, m['message'])
                print(f"From {from_addr}: {plaintext}")
                confirmed.append({"hash": m['hash']})
            except Exception:
                print(f"Failed to decrypt message from {from_addr} (message tampered?)")

        
        if confirmed:
            requests.post(f"{node_url}/confirm_fetch/{user}", json=confirmed)

    elif cmd in ["exit", "quit"]:
        break
    else:
        print("Commands: send <user@host[:port]>, fetch, exit")

