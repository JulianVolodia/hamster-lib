# -*- encoding: utf-8 -*-

from __future__ import unicode_literals
from future.utils import python_2_unicode_compatible
from builtins import str

import hamsterlib
from hamsterlib import objects
import datetime
import hamsterlib.helpers as helpers
# from future.utils import raise_from


"""
Module containing base classes intended to be inherited from when implementing storage backends.

Note:
    This is propably going to be replaced by a ``ABC``-bases solution.
"""


@python_2_unicode_compatible
class BaseStore(object):
    """A controlers Store provides unified interfaces to interact with our stored enteties."""

    def __init__(self, path):
        self.path = path
        self.categories = BaseCategoryManager(self)
        self.activities = BaseActivityManager(self)
        self.facts = BaseFactManager(self)

    def cleanup(self):
        """
        Any backend specific teardown code that needs to be executed before
        we shut down gracefully.
        """
        raise NotImplementedError


@python_2_unicode_compatible
class BaseManager(object):
    """Base class for all object managers."""

    def __init__(self, store):
        self.store = store


@python_2_unicode_compatible
class BaseCategoryManager(BaseManager):
    """Base class defining the minimal API for a CategoryManager implementation."""

    def save(self, category):
        """
        Save a Category to our selected backend.
        Internal code decides wether we need to add or update.

        Args:
            category (hamsterlib.Category): Category instance to be saved.

        Returns:
            hamsterlib.Category: Saved Category

        Raises:
            TypeError: If the ``category`` parameter is not a valid ``Category`` instance.
        """

        # We split this into two seperate steps to make validation easier to
        # extend. And yes I know we are supposed to duck-type, but I always feel
        # more comftable validating untrusted input this way.
        if not isinstance(category, objects.Category):
            raise TypeError(_("You need to pass a hamster category"))

        # We don't check for just ``category.pk`` becauses we don't want to make
        # assumptions about the PK beeing an int.
        if category.pk or category.pk == 0:
            result = self._update(category)
        else:
            result = self._add(category)
        return result

    def get_or_create(self, category):
        """
        Check if we already got a category with that name, if not create one.

        This is a convinience method as it seems sensible to rather implement
        this once in our controler than having every client implementation
        deal with it anew.

        It is worth noting that the lookup completely ignores any PK contained in the
        passed category. This makes this suitable to just create the desired Category
        and pass it along. One way or the other one will end up with a persistend
        db-backed version.

        Args:
            category (hamsterlib.Category or None): The categories.

        Returns:
            hamsterlib.Category: The retrieved or created category. Either way,
                the returned Category will contain all data from the backend, including
                its primary key.
        """

        if category:
            try:
                category = self.get_by_name(category)
            except KeyError:
                category = objects.Category(category)
                category = self._add(category)
        else:
            category = None
        return category

    def _add(self, category):
        """
        Add a ``Category`` to our backend.

        Args:
            category (hamsterlib.Category): ``Category`` to be added.

        Returns:
            hamsterlib.Category: Newly created ``Category`` instance.

        Raises:
            ValueError: When the category name was alreadyy present! It is supposed to be
            unique.

        Note:
            * Legacy version stored the proper name as well as a ``lower(name)`` version
            in a dedicated field named ``search_name``.
        """
        raise NotImplementedError

    def _update(self, category):
        """
        Update a ``Categories`` values in our backend.

        Args:
            category (hamsterlib.Category): Category to be updated.

        Returns:
            hamsterlib.Category: The updated Category.

        Raises:
            KeyError: If the ``Category`` can not be found by the backend.
            ValueError: If the ``Category().name`` is already beeing used by
                another ``Category`` instance.
        """
        raise NotImplementedError

    def remove(self, category):
        """
        Remove a category.

        Any ``Activity`` referencing the passed category will be set to
        ``Activity().category=None``.

        Args:
            category (hamsterlib.Category): Category to be updated.

        Returns:
            None: If everything went ok.

        Raises:
            KeyError: If the ``Category`` can not be found by the backend.
        """
        raise NotImplementedError

    def get(self, pk):
        """
        Get an ``Category`` by its primary key.

        Args:
            pk (int): Primary key of the ``Category`` to be fetched.

        Returns:
            hamsterlib.Category: ``Category`` with given primary key.

        Raises:
            KeyError: If no ``Category`` with this primary key can be found by the backend.
        """

        raise NotImplementedError

    def get_by_name(self, name):
        """
        Look up a category by its name.

        Args:
            name (str): Name of the ``Category`` to we want to fetch.

        Returns:
            hamsterlib.Category: ``Category`` with given name.

        Raises:
            KeyError: If no ``Category`` with this name was found by the backend.
        """
        raise NotImplementedError

    def get_all(self):
        """
        Return a list of all categories.

        Returns:
            list: List of ``Categories``, ordered by ``lower(name).
        """
        raise NotImplementedError


@python_2_unicode_compatible
class BaseActivityManager(BaseManager):
    """Base class defining the minimal API for a ActivityManager implementation."""
    def save(self, activity):
        """
        Save a ``Activity`` to the backend.

        This public method decides if it calles either ``_add`` or ``_update``.

        Args:
            activity (hamsterlib.Activity): ``Activity`` to be saved.

        Returns:
            hamsterlib.Activity: The saved ``Activity``.

        Raises:
            ValueError: If the category/activity.name combination was alreadyy present!
        """

        if activity.pk or activity.pk == 0:
            # [FIXME]
            # It appears that[activity.name + activity.category] is supposed to
            # be unique (see ``storage.db __change_category()``).
            # That means that if we update the category of an activity we need
            # to ensure that particular combination does not exist already.
            # We still need to contemplate if this is to be handled on the
            # controler or storage-backend level.
            result = self._update(activity)
        else:
            result = self._add(activity)
        return result

    def get_or_create(self, activity):
        """
        Convinience method to either get an activity matching the specs or create a new one.

        Args:
            name (str): Activity name
            category (hamsterlib.Category): The activities category
            deleted (bool): If the to be created category is marked as deleted.

        Returns:
            hamsterlib.Activity: The retrieved or created activity
        """
        try:
            activity = self.get_by_composite(activity.name, activity.category)
        except KeyError:
            activity = self.save(hamsterlib.Activity(activity.name, category=activity.category,
                deleted=activity.deleted))
        return activity

    def _add(self, activity, temporary=False):
        """
        Add a new ``Activity`` instance to the databasse.

        Args:
            activity (hamsterlib.Activity): The ``Activity`` to be added.
            temporary (bool, optional): If ``True``, the fact will be created with
                ``Fact.deleted = True``. Defaults to ``False``.

        Returns:
            hamsterlib.Activity: The newly created ``Activity``.

        Note:
            According to ``storage.db.Storage.__add_activity``: when adding a new activity
            with a new category, this category does not get created but instead this
            activity.category=None. This makes sense as categories passed are just ids, we
            however can pass full category objects. At the same time, this aproach allows
            to add arbitrary category.id as activity.category without checking their existence.
            this may lead to db anomalies.
        """
        raise NotImplementedError

    def _update(self, activity):
        """
        Update values for a given activity.

        Which activity to refer to is determined by the passed PK new values
        are taken from passed activity as well.

        Note:
            Seems to modify ``index``.
        """

        raise NotImplementedError

    def remove(self, activity):
        """
        Remove an ``Activity`` from the database.import

        If the activity to be removed is associated with any ``Fact``-instances,
        we set ``activity.deleted=True`` instead of deleting it properly.
        If it is not, we delete it from the backend.

        Args:
            activity (hamsterlib.Activity): The activity to be removed.

        Returns:
            bool: True

        Raises:
            KeyError: If the given ``Activity`` can not be found in the database.
        """
        raise NotImplementedError

    def get(self, pk):
        """
        Return an activity based on its primary key.

        Args:
            pk (int): Primary key of the activity

        Returns:
            hamsterlib.Activity: Activity matchin primary key.

        Raises:
            KeyError: If the primary key can not be found in the database.
        """
        raise NotImplementedError

    def get_by_composite(self, name, category):
        """
        Lookup for a supposedly unique ``Activityname`` / ``Category`` pair.

        This method utilizes that to return the corresponding entry or None.

        Args:
            name (str): Name of the ``Activities`` in question.
            category (hamsterlib.Category): ``Category`` of the activities.

        Returns:
            hamsterlib.Activity: The correspondig activity

        Raises:
            KeyError: If the composite key can not be found.
        """

        raise NotImplementedError

    def get_all(self, category=None, search_term=''):
        """
        Return all activities.

        Args:
            category (hamsterlib.Category, optional): Category to filter by. Defaults to ``None``.
                If ``None``, return all activities without a category.
            search_term (str): (Sub-)String that needs to be present in the ``Article.name`` in
                order to be considered for the resulti``Article.name`` in
                    order to be considered for the resulting list.

        Returns:
            list: List of activities
        """
        raise NotImplementedError


@python_2_unicode_compatible
class BaseFactManager(BaseManager):
    """Base class defining the minimal API for a FactManager implementation."""
    def save(self, fact):
        """
        Save a Fact to our selected backend.

        Args:
            fact (hamsterlib.Fact): Fact to be saved. Needs to be complete otherwise this will
            fail.

        Returns:
            hamsterlib.Fact: Saved Fact.
        """

        if fact.pk or fact.pk == 0:
            result = self._update(fact)
        else:
            result = self._add(fact)
        return result

    def get(self, pk):
        """
        Return a Fact by its primary key.

        Args:
            pk (int): Primary key of the ``Fact to be retrieved``.

        Returns:
            hamsterlib.Fact: The ``Fact`` corresponding to the primary key.

        Raises:
            KeyError: If primary key not found in the backend.
        """
        raise NotImplementedError

    def get_all(self, start=None, end=None, filter_term=''):
        """
        Return a list of ``Facts`` matching given criterias.

        Args:
            start_date (datetime.datetime, optional): Consider only Facts starting at or after
                this date. Alternativly you can also pass a ``datetime.datetime`` object
                in which case its own time will be considered instead of the default ``day_start``
                or a ``datetime.time`` which will be considered as today.
                Defaults to ``None``.
            end_date (datetime.datetime, optional): Consider only Facts ending before or at
                this date. Alternativly you can also pass a ``datetime.datetime`` object
                in which case its own time will be considered instead of the default ``day_start``
                or a ``datetime.time`` which will be considered as today.
                Defaults to ``None``.
            filter_term (str, optional): Only consider ``Facts`` with this string as part of their
                associated ``Activity.name``.

        Returns:
            list: List of ``Facts`` matching given specifications.

        Raises:
            TypeError: If ``start`` or ``end`` are not ``datetime.date``, ``datetime.time`` or
                ``datetime.datetime`` objects.
            ValueError: If ``end`` is before ``start``.

        Note:
            This public function only provides some sanity checks and normalization. The actual
            backend query is handled by ``_get_all``.
        """

        if start is not None:
            if isinstance(start, datetime.datetime):
                # isinstance(datetime.datetime, datetime.date) returns True,
                # which is why we need to catch this case first.
                pass
            elif isinstance(start, datetime.date):
                start = datetime.datetime.combine(start, self.store.config['day_start'])
            elif isinstance(start, datetime.time):
                start = datetime.datetime.combine(datetime.date.today(), start)
            else:
                raise TypeError(_(
                    "You need to pass either a datetime.date, datetime.time or datetime.datetime"
                    " object."))

        if end is not None:
            if isinstance(end, datetime.datetime):
                # isinstance(datetime.datetime, datetime.date) returns True,
                # which is why we need to except this case first.
                pass
            elif isinstance(end, datetime.date):
                end = helpers.end_day_to_datetime(end, self.store.config)
            elif isinstance(end, datetime.time):
                end = datetime.datetime.combine(datetime.date.today(), end)
            else:
                raise TypeError(_(
                    "You need to pass either a datetime.date, datetime.time or datetime.datetime"
                    " object."))

        if start and end and (end <= start):
            raise ValueError(_("End value can not be earlier than start!"))

        return self._get_all(start, end, filter_term)

    def get_today(self):
        """
        Return all facts for today, while respecting ``day_start``.

        Returns:
            list: List of ``Fact`` instances.
        """
        today = datetime.date.today()
        return self.get_all(
            datetime.datetime.combine(today, self.store.config['day_start']),
            helpers.end_day_to_datetime(today, self.store.config)
        )

    def _get_all(self, start=None, end=None, search_terms=''):
        """
        Return a list of ``Facts`` matching given criterias.

        Args:
            start_date (datetime.datetime, optional): Consider only Facts starting at or after
                this date. Defaults to ``None``.
            end_date (datetime.datetime): Consider only Facts ending before or at
                this date. Defaults to ``None``.
            filter_term (str, optional): Only consider ``Facts`` with this string as part of their
                associated ``Activity.name``.

        Returns:
            list: List of ``Facts`` matching given specifications.

        Note:
            In contrast to the public ``get_all``, this method actually handles the backend query.
        """
        raise NotImplementedError

    def _add(self, fact):
        """
        Add a new ``Fact`` to the backend.

        Args:
            fact (hamsterlib.Fact): Fact to be added.

        Returns:
            hamsterlib.Fact: Added ``Fact``.

        Returns:
            hamsterlib.Fact: Added ``Fact``.
        """
        raise NotImplementedError

    def _update(self, fact):
        raise NotImplementedError

    def remove(self, fact):
        """
        Remove a given ``Fact`` from the backend.

        Args:
            fact (hamsterlib.Fact): ``Fact`` instance to be removed.

        Returns:
            None: If everything worked as intended.

        Raises:
            KeyError: If the ``Fact`` specified could not be found in the backend.
        """
        raise NotImplementedError
