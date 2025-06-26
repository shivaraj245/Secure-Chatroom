import rsa
import socket

class API:
    class Chat:
        def __init__(self, priv_key, pub_key) -> None:
            self.priv_key = priv_key
            self.pub_key = pub_key

        def send(self, msg: str):
            from network import s
            s.send(rsa.encrypt(msg.encode(), self.pub_key))

        def recv(self, buffer: int):
            from network import s
            msg = s.recv(buffer)
            return rsa.decrypt(msg, self.priv_key).decode()

    class Load_keys:
        def __init__(self, pub_key, priv_key) -> None:
            self.pub_key = pub_key
            self.priv_key = priv_key

        def private(self):
            return rsa.PrivateKey.load_pkcs1(self.priv_key)

        def public(self):
            return rsa.PublicKey.load_pkcs1(self.pub_key)

        def load_all(self):
            return rsa.PrivateKey.load_pkcs1(
                self.priv_key), rsa.PublicKey.load_pkcs1(self.pub_key)