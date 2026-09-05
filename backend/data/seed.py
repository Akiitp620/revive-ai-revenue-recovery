import numpy as np
from faker import Faker

GLOBAL_SEED = 42

def set_seed(seed=GLOBAL_SEED):
    """Set the random seed for numpy, python random, and Faker for reproducibility."""
    import random
    random.seed(seed)
    np.random.seed(seed)
    Faker.seed(seed)

def get_faker():
    """Return a Faker instance initialized with the global seed."""
    fake = Faker()
    # Note: Faker.seed() sets it globally for faker, but to be safe:
    Faker.seed(GLOBAL_SEED)
    return fake
