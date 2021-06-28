import aiohttp
import re

REGION_WHITELIST = ["nl", "de", "com"]


class ValueNotFound(Exception):
    """Exception raised when no value is found in http response"""

    def __init__(self, value, message="Value not found in http response"):
        self.value = value
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.value} -> {self.message}"


class AuthFailed(Exception):
    """Exception raised when authentication failed"""

    def __init__(self, value, message="Authentication failed"):
        self.value = value
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.value} -> {self.message}"


class MarleySpoon:
    def __init__(self, username: str, password: str, region: str = "nl"):
        self.region = region
        self.username = username
        self.password = password
        self.session = None
        self.cache = None

    @property
    def user_id(self) -> str:
        regex = r"gon\.current_user_id=(\d*?);"
        match_id = re.search(regex, self.cache)
        user_id = match_id.group(1) if match_id else None
        if not user_id:
            raise ValueNotFound("gon.current_user_id")
        return user_id

    @property
    def api_host(self) -> str:
        regex = r'gon\.api_host="(.*?)";'
        match_host = re.search(regex, self.cache)
        api_host = match_host.group(1).replace("\\", "") if match_host else None
        if not api_host:
            raise ValueNotFound("gon.api_host")
        return api_host

    @property
    def api_token(self) -> str:
        regex = r'gon\.api_token="(.*?)";'
        match_token = re.search(regex, self.cache)
        api_token = match_token.group(1) if match_token else None
        if not api_token:
            raise ValueNotFound("gon.api_token")
        return api_token

    async def get_csrf_token(self, uri):
        async with self.session.get(uri) as resp:
            self.cache = await resp.text()

        regex = r'<meta content="(.*?)" name="csrf-token" />'
        match_csrf_token = re.search(regex, self.cache)
        csrf_token = match_csrf_token.group(1) if match_csrf_token else None
        if not csrf_token:
            raise ValueNotFound("meta name='csrf-token'")
        return csrf_token

    async def login(self) -> str:
        uri = f"https://marleyspoon.{self.region}/login"
        token_value = await self.get_csrf_token(uri)
        post_data = {
            "authenticity_token": token_value,
            "spree_user[email]": self.username,
            "spree_user[password]": self.password,
            "spree_user[brand]": "ms",
        }
        async with self.session.post(uri, data=post_data) as resp:
            self.cache = await resp.text()

        regex = r'<div class="flash-message error">\n(.*)\n</div>'
        match_error = re.search(regex, self.cache)
        if match_error:
            raise AuthFailed(match_error.group(1).strip())
        return self.user_id, self.api_token, self.api_host

    @staticmethod
    async def orders(
        user_id: str,
        api_token: str,
        api_host: str = "https://api.marleyspoon.com",
        region: str = "nl",
    ) -> dict:
        uri = f"{api_host}/users/{user_id}/orders/current"
        params = {"brand": "ms", "country": region, "product_type": "web"}
        headers = {"Authorization": f"Bearer {api_token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(uri, params=params, headers=headers) as resp:
                result = await resp.json()
        return result

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_t, exc_v, exc_tb):
        await self.session.close()
