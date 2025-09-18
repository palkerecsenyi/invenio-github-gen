import random
import string
from random import randint


def random_with_N_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10**n) - 1
    return randint(range_start, range_end)


def random_chars(n):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(n))
