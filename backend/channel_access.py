"""Per-user channel access control.

A user may be restricted to a set of channel groups (tags). A user with **no** groups
assigned is unrestricted and sees every channel (backwards compatible); admins are always
unrestricted. Restriction is enforced at every point that serves a per-user channel list
(M3U / XC / HDHomeRun / XMLTV) and when authorising a live stream.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.models import Channel, Session, User
from backend.users import user_has_admin_role
from backend.utils import clean_text

logger = logging.getLogger("tic.channel_access")


async def allowed_channel_tag_names_for_username(username: str | None) -> set[str] | None:
    """Channel group (tag) names a user may see, or ``None`` when unrestricted.

    ``None`` means "see all channels" and is returned for: an empty/unknown username
    (e.g. the internal TVHeadend stream user), admins, and any user with no groups
    assigned. Otherwise a concrete set of allowed tag names is returned.
    """
    name = clean_text(username)
    if not name:
        return None
    async with Session() as session:
        result = await session.execute(
            select(User)
            .where(User.username == name)
            .options(selectinload(User.roles), selectinload(User.allowed_channel_tags))
        )
        user = result.scalars().first()
    if user is None or user_has_admin_role(user):
        return None
    tag_names = {tag.name for tag in (user.allowed_channel_tags or []) if tag.name}
    return tag_names or None


def channel_allowed(channel: dict, allowed_tag_names: set[str] | None) -> bool:
    """Whether a channel dict (as produced by read_config_all_channels) is visible."""
    if allowed_tag_names is None:
        return True
    return bool(set(channel.get("tags") or []) & allowed_tag_names)


def filter_channels_for_access(channels, allowed_tag_names: set[str] | None) -> list:
    """Return only the channels visible under the given allowed tag set."""
    if allowed_tag_names is None:
        return list(channels)
    return [channel for channel in channels if channel_allowed(channel, allowed_tag_names)]


async def channel_id_allowed_for_username(channel_id, username: str | None) -> bool:
    """Whether a user may stream a specific channel (used to authorise stream requests)."""
    allowed_tag_names = await allowed_channel_tag_names_for_username(username)
    if allowed_tag_names is None:
        return True
    try:
        channel_id_int = int(channel_id)
    except (TypeError, ValueError):
        return False
    async with Session() as session:
        result = await session.execute(
            select(Channel).where(Channel.id == channel_id_int).options(selectinload(Channel.tags))
        )
        channel = result.scalars().first()
    if channel is None:
        return False
    channel_tag_names = {tag.name for tag in (channel.tags or []) if tag.name}
    return bool(channel_tag_names & allowed_tag_names)
