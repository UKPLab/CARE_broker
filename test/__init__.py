import random
import string


def get_random_string(length):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
