# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from random import randint
from datetime import datetime, timedelta

from amundsen_application.models.announcements import Announcements, Post
from amundsen_application.base.base_announcement_client import BaseAnnouncementClient

try:
    from sqlalchemy import Column, Integer, String, DateTime, create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
except ModuleNotFoundError:
    pass

Base = declarative_base()


class DBAnnouncement(Base):  # type: ignore
    __tablename__ = 'announcements'

    id = Column(Integer, primary_key=True)

    date = Column(DateTime)
    title = Column(String)
    content = Column(String)


class SQLAlchemyAnnouncementClient(BaseAnnouncementClient):
    def __init__(self) -> None:
        self._setup_mysql()

    def _setup_mysql(self) -> None:
        self.engine = create_engine('sqlite:////tmp/amundsen.db', echo=True)

        session = sessionmaker(bind=self.engine)()

        # add dummy announcements to preview
        if not self.engine.dialect.has_table(self.engine, DBAnnouncement.__tablename__):
            Base.metadata.create_all(self.engine)

            announcements = []

            dummy_announcement = """
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec at dapibus lorem.
            Orci varius natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus.
            Suspendisse est lectus, bibendum vitae vestibulum vitae, commodo eu tortor.
            Sed rhoncus augue eget turpis interdum, eu aliquam lectus ornare. Aenean tempus in mauris vitae viverra.
            """

            for i in range(randint(5, 9)):
                announcement = DBAnnouncement(id=i + 1,
                                              date=datetime.now() + timedelta(days=i + 1),
                                              title=f'Test announcement title {i + 1}',
                                              content=dummy_announcement)

                announcements.append(announcement)

            session.add_all(announcements)
            session.commit()

    def get_posts(self) -> Announcements:
        """
        Returns an instance of amundsen_application.models.announcements.Announcements, which should match
        amundsen_application.models.announcements.AnnouncementsSchema
        """
        session = sessionmaker(bind=self.engine)()

        posts = []

        for row in session.query(DBAnnouncement).order_by(DBAnnouncement.date.desc()):
            post = Post(title=row.title,
                        date=row.date.strftime('%b %d %Y %H:%M:%S'),
                        html_content=row.content)
            posts.append(post)

        return Announcements(posts)
