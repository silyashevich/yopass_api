"""
yopass_api :: store secret, get link and fetch secret in Yopass
"""
import json
import re
import warnings
from random import SystemRandom
from string import ascii_letters, digits
from urllib.parse import urljoin

import pgpy
import requests
from cryptography.utils import CryptographyDeprecationWarning


class Yopass:
    """Base class used by bound module functions."""

    def __init__(self, api: str, timeout=None):
        """Initialize an instance.

        Args:
            api (str): Yopass URL
            timeout: optional, see https://requests.readthedocs.io/en/latest/user/advanced/#timeouts
        """
        warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
        self.api = api
        self.timeout = timeout

    @property
    def api(self):
        """Сontains Yopass URL

        Returns:
            str: Yopass URL
        """
        return self._api

    @api.setter
    def api(self, value):
        regex = re.compile(
            r"^https?://"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            r"(?::\d+)?"
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        if not regex.search(value):
            raise ValueError("Invalid value: URL expected")
        self._api = value

    @property
    def timeout(self):
        """Сontains requests timeout

        Returns:
            timeout, see https://requests.readthedocs.io/en/latest/user/advanced/#timeouts
        """
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        if not value or isinstance(
            value,
            (
                int,
                float,
                tuple,
            ),
        ):
            self._timeout = value
        else:
            raise ValueError("Invalid value: int/float/tuple expected")

    def generate_passphrase(self, length: int) -> str:
        """Simple password string generation (ASCII letters and digits)

        Args:
            length (int):

        Returns:
            str: password string
        """
        return "".join(
            SystemRandom().choice(ascii_letters + digits) for _ in range(length)
        )

    def secret_url(self, secret_id: str, password: str) -> str:
        """Generate URL from secret_id and password

        Args:
            secret_id (str): secret identifier
            password (str): secret password

        Returns:
            str: URL
        """
        return (
            urljoin(self._api, f"/#/s/{secret_id}/{password}")
            if secret_id != ""
            else ""
        )

    def store(self, message: str, password: str, expiration: str, one_time=True) -> str:
        """Store secret in Yopass

        Args:
            message (str): secret
            password (str): password
            expiration (str): "1h" or "1d"  or "1w"
            one_time (bool, optional): one/multiple time link generate. Defaults to True.

        Returns:
            str: secret identifier
        """
        expiry_dict = {"1h": 3600, "1d": 86400, "1w": 604800}
        if expiration not in expiry_dict:
            return ""
        cipher = pgpy.constants.SymmetricKeyAlgorithm.AES256
        secret = pgpy.PGPMessage.new(message=message).encrypt(
            passphrase=password, cipher=cipher
        )
        payload = json.dumps(
            obj={
                "message": str(secret),
                "expiration": expiry_dict[expiration],
                "one_time": one_time,
            }
        )
        headers = {
            "Content-type": "application/json",
        }
        try:
            response = requests.post(
                urljoin(self._api, "/secret"),
                data=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json().get("message", "")
        except requests.exceptions.RequestException as _:
            return ""

    def fetch(self, secret_id: str, password: str) -> str:
        """Fetch secret from Yopass

        Args:
            secret_id (str): secret identifier
            password (str): password

        Returns:
            str: secret
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        try:
            response = requests.get(
                urljoin(self._api, f"/secret/{secret_id}"),
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as _:
            return ""
        try:
            secret = pgpy.PGPMessage.from_blob(
                response.json().get("message", "")
            ).decrypt(passphrase=password)
            return secret.message
        except pgpy.errors.PGPDecryptionError as _:
            return ""
