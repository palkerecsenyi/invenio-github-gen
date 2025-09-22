import random
import sys
import uuid
from datetime import datetime, timezone

from lorem import get_sentence, get_word
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from tqdm import tqdm

from models import RemoteAccount, Repository, User
from utils import random_chars, random_with_N_digits

engine = create_engine(
    "postgresql+psycopg2://paldemo:paldemo@127.0.0.1:5432/paldemo", echo=True
)
repos_per_user = 50
enabled_repos_per_user = 10
num_users = 5_000
delete_only = False

with Session(engine) as session:
    session.execute(text("TRUNCATE TABLE oauthclient_remotetoken CASCADE"))
    session.execute(text("TRUNCATE TABLE oauthclient_remoteaccount CASCADE"))
    session.execute(text("TRUNCATE TABLE github_releases CASCADE"))
    session.execute(text("TRUNCATE TABLE github_repositories CASCADE"))
    session.execute(text("TRUNCATE TABLE accounts_user CASCADE"))

    if delete_only:
        session.commit()
        sys.exit(0)

    user_ids = []
    for i in tqdm(range(num_users), desc="users"):
        username = random_chars(20)
        domain = random_chars(10)
        user = User(
            id=i,
            username=username,
            email=f"{username}@{domain}.com",
            domain=f"{domain}.com",
            password="",
            active=True,
            version_id=2,
            user_profile={"full_name": get_word(), "affiliations": get_word()},
            preferences={
                "locale": "en",
                "timezone": "Europe/Zurich",
                "visibility": "restricted",
                "email_visibility": "restricted",
            },
        )

        session.add(user)
        user_ids.append(i)

    next_github_id = 1
    for user_id in tqdm(user_ids, desc="user_repos"):
        all_repos = []
        remoteaccount_repos = {}
        for _ in range(repos_per_user):
            id = uuid.uuid4()
            repo = Repository(
                id=id,
                github_id=next_github_id,
                name=f"{get_word()}/{get_word()}-{get_word()}-{random_chars(10)}",
                user_id=user_id,
                hook=random_with_N_digits(6),
            )
            all_repos.append(repo)

            remoteaccount_repos[str(next_github_id)] = {
                "id": next_github_id,
                "full_name": repo.name,
                "description": get_sentence(),
                "default_branch": "main",
            }

            next_github_id += 1

        remote_account = RemoteAccount(
            user_id=user_id,
            client_id="gh_abcdefgh",
            extra_data=dict(
                repos=remoteaccount_repos,
                last_sync=datetime.now(tz=timezone.utc).isoformat(),
            ),
        )
        session.add(remote_account)

        for repo in random.choices(all_repos, k=enabled_repos_per_user):
            session.add(repo)

    session.commit()
