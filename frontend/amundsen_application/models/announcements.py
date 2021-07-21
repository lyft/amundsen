# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from marshmallow import Schema, fields, post_dump
from marshmallow.exceptions import ValidationError

from typing import Dict, List, Any


class Post:
    def __init__(self, date: str, title: str, html_content: str) -> None:
        self.date = date
        self.html_content = html_content
        self.title = title


class PostSchema(Schema):
    date = fields.Str(required=True)
    title = fields.Str(required=True)
    html_content = fields.Str(required=True)


class Announcements:
    def __init__(self, posts: List = []) -> None:
        self.posts = posts


class AnnouncementsSchema(Schema):
    posts = fields.Nested(PostSchema, many=True)

    @post_dump
    def validate_data(self, data: Dict, **kwargs: Any) -> Dict:
        posts = data.get('posts', [])
        for post in posts:
            if post.get('date') is None:
                raise ValidationError('All posts must have a date')
            if post.get('title') is None:
                raise ValidationError('All posts must have a title')
        return data
