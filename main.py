import random
import uuid
from datetime import datetime, timezone

from lorem import get_sentence, get_word
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session
from tqdm import tqdm

from models import Release, RemoteAccount, RemoteToken, Repository, User
from utils import random_chars, random_with_N_digits

engine = create_engine(
    "postgresql+psycopg2://paldemo:paldemo@127.0.0.1:5432/paldemo", echo=True
)
repos_per_user = 50
enabled_repos_per_user = 10
num_users = 500

with Session(engine) as session:
    session.execute(delete(RemoteToken))
    session.execute(delete(RemoteAccount))
    session.execute(delete(Release))
    session.execute(delete(Repository))
    session.execute(delete(User))

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

    for user_id in tqdm(user_ids, desc="user_repos"):
        all_repos = []
        remoteaccount_repos = {}
        for _ in range(repos_per_user):
            id = uuid.uuid4()
            github_id = random_with_N_digits(8)
            repo = Repository(
                id=id,
                github_id=github_id,
                name=f"{get_word()}/{get_word()}-{get_word()}-{random_chars(10)}",
                user_id=user_id,
                hook=random_with_N_digits(5),
            )
            all_repos.append(repo)

            remoteaccount_repos[github_id] = {
                "id": github_id,
                "full_name": repo.name,
                "description": get_sentence(),
                "default_branch": "main",
            }

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
