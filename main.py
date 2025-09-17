from lorem import word
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Repository
from utils import random_with_N_digits

engine = create_engine("postgres://cds-rdm:cds-rdm@127.0.0.1:5432/cds-rdm", echo=True)

with Session(engine) as session:
    for _ in range(1000):
        repo = Repository(
            github_id=str(random_with_N_digits(8)), name="-".join(word(count=3))
        )
