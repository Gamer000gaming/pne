# pne
A simple node-to-node, end-to-end encrypted message protocol meant to be a modern alternative to emails.

## Initial setup
- Clone this repo
- In the cloned repo, run `pip install -r requirements.txt`. You may need to use a python `venv`.

## How to run a node
- Configure port forwarding to your server for port 16361
- Run pne_server.py

## How to use the client
- Run pne_client.py

## Encryption
Every message is end-to-end encrypted. When you send a message, this happens:
* Each user generates a keypair locally. The server only stores the public key, never private keys.
* To send a message, the sender requests the recipient’s public key from the recipient’s server.
* The sender derives a shared secret using their private key and the recipient’s public key, then encrypts the message locally.
* The sender uploads the encrypted message and a hash of the plaintext to the recipient’s server.
* The server stores the encrypted message without being able to read it.
* When the recipient fetches messages, they decrypt locally and compute the plaintext hash.
* If the hash matches, the client confirms deletion and the server removes the message.

## Public test node
A public node is available for testing:
gamer000gaming.madhacker.biz (port 16361)
