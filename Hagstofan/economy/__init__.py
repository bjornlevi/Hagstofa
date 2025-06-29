# Hagstofan/economy/__init__.py
from Hagstofan.api_client import APIClient
from Hagstofan.economy.cpi import CPI

client = APIClient(base_url='https://px.hagstofa.is:443/pxis/api/v1')
cpi = CPI(client)

__all__ = ['cpi']