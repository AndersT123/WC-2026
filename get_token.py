"""Get the latest magic link token from the database."""
import asyncio
from sqlalchemy import select
from app.database import async_session_maker
from app.models.user import MagicLinkToken

async def main():
    async with async_session_maker() as db:
        result = await db.execute(
            select(MagicLinkToken)
            .order_by(MagicLinkToken.created_at.desc())
            .limit(1)
        )
        token_obj = result.scalar_one_or_none()

        if token_obj:
            print(f"Token: {token_obj.token}")
            print(f"Email: {token_obj.email}")
            print(f"Expires: {token_obj.expires_at}")
            print(f"Used: {token_obj.used_at}")
            return token_obj.token
        else:
            print("No tokens found")
            return None

if __name__ == "__main__":
    token = asyncio.run(main())
