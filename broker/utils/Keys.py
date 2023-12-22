from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


def read_private(path="private.pem"):
    """
    Read private key from file
    :param path: path to file
    :return: private key
    """
    with open(path, "r") as src:
        return RSA.importKey(src.read())


def write_pub(key, path="public_key.txt"):
    """
    Write a key to the path
    :param key: key
    :param path: path to save the key as txt file
    :return:
    """
    with open(path, 'w') as out:
        out.write(key.exportKey().decode('utf-8'))


def verify(message, sig, key):
    """
    verify signature from message with public key
    :param message: message to verify
    :param sig: signature to verify
    :param key: public key
    :return:
    """
    hash = SHA256.new(message.encode('utf-8'))
    pubkey = RSA.importKey(bytes.fromhex(key))
    verifier = PKCS1_v1_5.new(pubkey)
    return verifier.verify(hash, bytes.fromhex(sig))


class Keys:
    """
    Key calculations
    Framework URL https://www.pycryptodome.org/
    @author: Dennis Zyska
    """

    def __init__(self, private_key_path=None):
        if private_key_path is None:
            # Generate new key
            self.private_key = RSA.generate(2048)
        else:
            self.private_key = read_private(private_key_path)
        self.public_key = self.private_key.publickey()

    def sign(self, message):
        """
        Generate signature from message with private key
        :param message: message to sign
        :return: signature
        """
        digest = SHA256.new()
        digest.update(message.encode('utf-8'))
        signer = PKCS1_v1_5.new(self.private_key)
        sig = signer.sign(digest)
        return sig.hex()

    def get_public(self):
        """
        Return public key
        :return:
        """
        return self.public_key.exportKey("DER").hex()
