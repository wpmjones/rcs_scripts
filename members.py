import asyncio
import asyncpg
import coc
from config import settings
from datetime import datetime

coc_client = coc.Client(settings['supercell']['apiKey'])


async def main():
    now = datetime.now()
    conn = await asyncpg.connect(user=settings['pg']['user'],
                                 password=settings['pg']['pass'],
                                 host="localhost",
                                 database=settings['pg']['db'])
    
    def get_player_info(tags):
        for tag in tags:
            player = await coc_client.get_player(tag)
            yield (tag, player.name, player.town_hall, player.trophies, player.attack_wins, player.defense_wins,
                player.builder_hall, player.versus_trophies, player.role, player._achievements['Gold Grab'].value,
                player._achievements['Elixir Escapade'].value, player._achievements['Heroic Heist'].value,
                player._achievements['Friend in Need'].value, player._achievements['Games Champion'].value,
                player.clan.tag[1:], now)

    clan_tags = await conn.fetch("SELECT clan_tag, clan_name FROM rcs_clans ORDER BY clan_name")
    for clan in clan_tags:
        clan = await coc_client.get_clan(f"#{clan['clan_tag']}")
        print(f"Working on {clan.name}")
        tag_list = [member.tag for member in clan.members]
        await conn.executemany("""INSERT INTO rcs_members(
            player_tag, player_name, th_level, trophies, attack_wins, defense_wins, bh_level, vs_trophies,
            clan_role, gold, elixir, dark_elixir, friend_need, clan_games, clan_tag, time_stamp)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)""",
            get_player_info(tag_list))
    await conn.close()
    print(f"Started at {now} and finished at {datetime.now()}")


asyncio.get_event_loop().run_until_complete(main())
