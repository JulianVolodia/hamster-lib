# -*- encoding: utf-8 -*-

from __future__ import unicode_literals
from future.utils import python_2_unicode_compatible
from builtins import str

import pytest
import logging

from hamsterlib.storage import BaseStore


@python_2_unicode_compatible
class TestControler:
    @pytest.mark.parametrize('storetype', ['sqlalchemy'])
    def test_get_store_valid(self, controler, storetype):
        """Make sure  we recieve a valid ``store`` instance."""
        # [TODO]
        # Once we got backend registration up and running this should be
        # improved to check actual store type for that backend.
        controler.config['store'] = storetype
        assert isinstance(controler._get_store(), BaseStore)

    def test_get_store_invalid(self, controler):
        """Make sure we get an exception if store retrieval fails."""
        controler.config['store'] = None
        with pytest.raises(KeyError):
            controler._get_store()

    def test_get_logger(self, controler):
        """Make sure we recieve a logger that maches our expectations."""
        logger = controler._get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'hamsterlib.lib'
        # [FIXME]
        # assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.NullHandler)

    @pytest.mark.xfail
    def test_parse_raw_fact_with_persistent_activity(self, controler,
            raw_fact_with_persistent_activity):
        raw_fact, expectation = raw_fact_with_persistent_activity
        fact = controler.parse_raw_fact(raw_fact)
        assert fact.start == expectation['start']
        assert fact.end == expectation['end']
        assert fact.activity.name == expectation['activity']
        if fact.activity.category:
            assert fact.activity.category._name == expectation['category']
        else:
            assert expectation['category'] is None
        assert fact.description == expectation['description']
