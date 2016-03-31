# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import datetime

import factory
import faker
from . import common
from hamsterlib.backends.sqlalchemy.objects import AlchemyCategory, AlchemyActivity, AlchemyFact


class AlchemyCategoryFactory(factory.alchemy.SQLAlchemyModelFactory):
    pk = factory.Sequence(lambda n: n)
    name = factory.Faker('word')

    class Meta:
        model = AlchemyCategory
        sqlalchemy_session = common.Session


class AlchemyActivityFactory(factory.alchemy.SQLAlchemyModelFactory):
    pk = factory.Sequence(lambda n: n)
    name = factory.Faker('sentence')
    category = factory.SubFactory(AlchemyCategoryFactory)
    deleted = False

    class Meta:
        model = AlchemyActivity
        sqlalchemy_session = common.Session


class AlchemyFactFactory(factory.alchemy.SQLAlchemyModelFactory):
    pk = factory.Sequence(lambda n: n)
    activity = factory.SubFactory(AlchemyActivityFactory)
    start = faker.Faker().date_time()
    end = start + datetime.timedelta(hours=3)
    description = factory.Faker('paragraph')

    class Meta:
        model = AlchemyFact
        sqlalchemy_session = common.Session
