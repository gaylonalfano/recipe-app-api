# core/tests/test_commands.py
from unittest.mock import patch

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import TestCase


class CommandTests(TestCase):

    def test_wait_for_db_ready(self):
        """Test waiting for db when db is available"""
        with patch('django.db.utils.ConnectionHandler.__getitem__') as gi:
            gi.return_value = True
            # 'wait_for_db' is the name of management command we create
            call_command('wait_for_db')
            # Now command is called, we can do assertions of our test
            # Check that __getitem__ was called once
            self.assertEqual(gi.call_count, 1)

    # Read my notes!
    @patch('time.sleep', return_value=True)
    def test_wait_for_db(self, ts):
        """Test waiting for db"""
        with patch('django.db.utils.ConnectionHandler.__getitem__') as gi:
            # Add side_effect to mock __getitem__ failing 5 times then execute
            gi.side_effect = [OperationalError] * 5 + [True]
            # Call our command
            call_command('wait_for_db')
            # Assert the function was called six times
            self.assertEqual(gi.call_count, 6)
