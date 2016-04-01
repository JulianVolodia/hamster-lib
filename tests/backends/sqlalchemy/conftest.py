# -*- encoding: utf-8 -*-

from __future__ import unicode_literals
from builtins import str

import pytest

from sqlalchemy import orm, create_engine
import datetime
import fauxfactory

from pytest_factoryboy import register

from . import factories, common

from hamsterlib.backends.sqlalchemy import objects, database
from hamsterlib.backends.sqlalchemy.storage import SQLAlchemyStore

from hamsterlib import Category, Activity, Fact

register(factories.AlchemyCategoryFactory)
register(factories.AlchemyActivityFactory)
register(factories.AlchemyFactFactory)


@pytest.fixture
def alchemy_runner(request):
    engine = create_engine('sqlite:///:memory:')
    objects.metadata.bind = engine
    objects.metadata.create_all(engine)
    common.Session.configure(bind=engine)

    def fin():
        common.Session.remove()

    request.addfinalizer(fin)


# We are sometimes tempted not using hamsterObjects at all. but as our tests
# expect them as input we need them!


@pytest.fixture
def alchemy_store(request, alchemy_runner):
    store = SQLAlchemyStore('sqlite:///:memory:', common.Session)
    return store


@pytest.fixture(params=[True, False])
def existing_category_valid_parametrized(request, category_factory,
        name_string_valid_parametrized):
    """
    Provide a parametrized persisent category fixture.

    This fixuture will represent a wide array of potential name charsets as well
    as a ``category=None`` version.
    """

    if request.param:
        result = category_factory(name=name_string_valid_parametrized)
    else:
        result = None
    return result



@pytest.fixture
def existing_category_valid_without_none_parametrized(request, category_factory,
        name_string_valid_parametrized):
    """
    Provide a parametrized persisent category fixture.

    This fixuture will represent a wide array of potential name charsets as well
    but not ``category=None``.
    """
    return category_factory(name=name_string_valid_parametrized)


@pytest.fixture
def set_of_categories(alchemy_category_factory):
    """Provide a number of perstent facts at once."""
    return [alchemy_category_factory() for i in range(5)]


@pytest.fixture
def existing_activity_valid_parametrized(activity_factory,
        name_string_valid_parametrized, deleted_valid_parametrized):
    """
    Provide a parametrized persistent activity fixture.

    We make heavy usage of parametrized sub fixtures to generate a wide variation of
    possible persistent activities. Please refer to each used fixtures docstring
    for details on what is covered.
    """

    # [TODO]
    # Parametrize category. In particular cover cases where category=None

    return activity_factory(name=name_string_valid_parametrized,
        deleted=deleted_valid_parametrized)



@pytest.fixture
def alchemy_fact_valid_parametrized(alchemy_store, fact_factory,
        existing_activity_valid_parametrized, description_valid_parametrized,
        tag_list_valid_parametrized):
    fact = fact_factory(description=description_valid_parametrized,
        tags=tag_list_valid_parametrized)
    return fact



@pytest.fixture
def start_datetime():
    return datetime.datetime.now()


@pytest.fixture
def set_of_alchemy_facts(start_datetime, fact_factory):
    start = start_datetime
    result = []
    for i in range(5):
        end = start + datetime.timedelta(minutes=20)
        fact = fact_factory(start=start, end=end)
        result.append(fact)
        start = start + datetime.timedelta(days=1)
    return result

# as_hamster versions
# its not clear that they are needed anymore
@pytest.fixture
def alchemy_category_as_hamster(request, alchemy_category_factory):
    """Hamsterized version of a category."""
    category = alchemy_category_factory()
    return category.as_hamster()

@pytest.fixture
def alchemy_activity_as_hamster(request, alchemy_activity_factory):
    """Mocked hamsterized version of an activity."""
    activity = alchemy_activity_factory.build()
    activity.pk = None
    return activity


# Fallback hamster object fixtures. Unless we know how factories interact

@pytest.fixture(params=[fauxfactory.gen_string('utf8')])
def category(request):
    return Category(request.param, None)

@pytest.fixture(params=[fauxfactory.gen_string('utf8')])
def activity(request, category):
    return Activity(request.param, pk=None, category=category, deleted=False)

@pytest.fixture
def fact(request, activity, start_end_datetimes, description_valid_parametrized):
    start, end = start_end_datetimes
    return Fact(activity, start, end, pk=None, description=description_valid_parametrized)


