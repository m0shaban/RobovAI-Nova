import sys
import os
import asyncio

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.core.database import db_client


async def main():
    try:
        res = await db_client.create_user('test@example.com', 'pass1234', 'Test User')
        print('create_user result:', res)
    except Exception as e:
        print('Exception:', type(e), e)


asyncio.run(main())
