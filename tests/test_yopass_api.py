import os
import sys
import unittest
import uuid

sys.path.insert(0, os.path.abspath(".."))

import yopass_api.yopass_api as yopass_api

API_URL = "https://api.yopass.se"


class YopassApiTestCase(unittest.TestCase):
    def setUp(self):
        self.yopass = yopass_api.Yopass(api=API_URL)

    def test_01_api(self):
        self.assertEqual(self.yopass.api, API_URL)
        with self.assertRaises(ValueError):
            self.yopass.api = "1234"

    def test_02_timeout(self):
        self.assertEqual(self.yopass.timeout, None)
        self.assertRaises(ValueError, exec, "self.yopass.timeout = 'zzz'", locals())
        with self.assertRaises(ValueError):
            self.yopass.api = "3"
        self.assertEqual(self.yopass.timeout, None)
        self.yopass.timeout = (3.0, 3.0)
        self.assertEqual(self.yopass.timeout, (3.0, 3.0))
        self.yopass.timeout = 3.0
        self.assertEqual(self.yopass.timeout, 3.0)
        self.yopass.timeout = 3
        self.assertEqual(self.yopass.timeout, 3)

    def test_03_generate_passphrase(self):
        self.assertEqual(isinstance(self.yopass.generate_passphrase(0), (str,)), True)
        self.assertEqual(isinstance(self.yopass.generate_passphrase(10), (str,)), True)

    def test_04_secret_url(self):
        self.assertEqual(self.yopass.secret_url("1", "2"), f"{API_URL}/#/s/1/2")
        self.assertEqual(self.yopass.secret_url("1", ""), f"{API_URL}/#/s/1/")
        self.assertEqual(self.yopass.secret_url("", "2"), "")

    def test_05_store(self):
        # normal store
        result = self.yopass.store(
            message="message",
            password="password",
            expiration="1h",
            one_time=False,
        )
        self.assertEqual(isinstance(uuid.UUID(result), uuid.UUID), True)
        # wrong expiration
        result = self.yopass.store(
            message="message",
            password="password",
            expiration="21h",
            one_time=False,
        )
        self.assertEqual(result, "")
        # wrong URL
        self.yopass.api = "https://google.com"
        result = self.yopass.store(
            message="message",
            password="password",
            expiration="1h",
            one_time=False,
        )
        self.assertEqual(result, "")
        self.yopass.api = API_URL

    def test_06_fetch(self):
        # all ok
        result = self.yopass.store(
            message="message",
            password="password",
            expiration="1h",
            one_time=False,
        )
        self.assertEqual(
            self.yopass.fetch(secret_id=result, password="password"), "message"
        )
        # wrong password
        result = self.yopass.store(
            message="message",
            password="password",
            expiration="1h",
            one_time=False,
        )
        self.assertEqual(
            self.yopass.fetch(secret_id=result, password="wrong_password"), ""
        )
        # wrong secret_id
        result = self.yopass.store(
            message="message",
            password="password",
            expiration="1h",
            one_time=False,
        )
        self.assertEqual(self.yopass.fetch(secret_id=1111, password="password"), "")
