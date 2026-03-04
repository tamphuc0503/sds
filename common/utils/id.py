import random
import string
from uuid import uuid4


def random_id(length: int):
    # choose from all lowercase letter
    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str


def correlation_id():
    return f"{uuid4()}-{random_id(4)}"
