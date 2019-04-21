import asyncio
import asyncpg
import coc
from config import settings
from datetime import datetime

coc_client = coc.Client(settings['supercell']['user'], settings['supercell']['pass'])
now = datetime.now()


async def main():
    conn = await asyncpg.connect(user=settings['pg']['user'],
                                 password=settings['pg']['pass'],
                                 host="localhost",
                                 database=settings['pg']['db'])
    clan_tags = await conn.fetch("SELECT clan_tag, clan_name FROM rcs_clans ORDER BY clan_name")
    # TODO temp fix for http keys issue
    await asyncio.sleep(2)
    for clan in clan_tags:
        clan = await coc_client.get_clan(f"#{clan['clan_tag']}")
        print(f"Working on {clan.name}")
        tag_list = [m.tag for m in clan.members]
        for tag in tag_list:
            player = await coc_client.get_player(tag)
            await conn.execute("""INSERT INTO rcs_members(
                player_tag, player_name, th_level, trophies, attack_wins, defense_wins, bh_level, vs_trophies,
                clan_role, gold, elixir, dark_elixir, friend_need, clan_games, clan_tag, time_stamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)""",
                player.tag, player.name, player.town_hall, player.trophies, player.attack_wins, player.defense_wins,
                player.builder_hall, player.versus_trophies, player.role, player.achievements_dict['Gold Grab'].value,
                player.achievements_dict['Elixir Escapade'].value, player.achievements_dict['Heroic Heist'].value,
                player.achievements_dict['Friend in Need'].value, player.achievements_dict['Games Champion'].value,
                player.clan.tag[1:], now)
        await conn.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
print(f"Started at {now} and finished at {datetime.now()}")
loop.close()
