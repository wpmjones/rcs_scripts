import sys
import random
import praw
import coc
import re
import yaml
import logging
import asyncpg
import asyncio
import aiohttp
from datetime import datetime
from config import settings, color_pick

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S',
                    filename='rcslist.log',
                    filemode='w',
                    level=logging.INFO)
logging.info('Starting rcslist.py')

now = datetime.now()

coc_client = coc.login(settings['supercell']['user'],
                       settings['supercell']['pass'],
                       key_names="ubuntu")

subreddit = "redditclansystem"
wiki_page = "official_reddit_clan_system"
feeder_link = ("[See Below](https://www.reddit.com/r/RedditClanSystem/wiki/official_reddit_"
               "clan_system#wiki_4._official_feeder_clans)")
reddit = praw.Reddit(client_id=settings['redditSpeed']['client'],
                     client_secret=settings['redditSpeed']['secret'],
                     username=settings['redditSpeed']['username'],
                     password=settings['redditSpeed']['password'],
                     user_agent="ubuntu:con.mayodev.rcs_clan_updater:v0.9 (by /u/TubaKid44)")


with open("leaderalts.yaml") as f:
    leaders = yaml.load(f)


async def update_wiki_page(conn, subreddit, wiki_page):
    try:
        page = reddit.subreddit(subreddit).wiki[wiki_page]
        content = page.content_md
        clan_types = ["comp", "social", "gen", "warFarm"]

        # loop through clan types
        for clan_type in clan_types:
            page_content = ("Clan&nbsp;Name | Clan&nbsp;Tag | Lvl | Leader | Members | "
                            "War&nbsp;Frequency | Social&nbsp;Media | Notes | Feeder/Other\n"
                            "-|-|:-:|-|:-:|:-:|-|-|:-:")
            start_marker = f"[](#{clan_type}Start)"
            end_marker = f"[](#{clan_type}End)"
            sql = (f"SELECT clan_name, subreddit, clan_tag, clan_level, leader, leader_reddit, member_count, "
                   f"war_frequency, social_media, notes, feeder "
                   f"FROM rcs_clans WHERE classification='{clan_type}' "
                   f"ORDER BY member_count, clan_name")
            fetched = await conn.fetch(sql)
            for clan in fetched:
                # Set proper War Frequency text
                if str(clan['war_frequency']) == "moreThanOncePerWeek":
                    war_freq = "2+ / Week"
                elif str(clan['war_frequency']) == "always":
                    war_freq = "Always"
                elif str(clan['war_frequency']) == "oncePerWeek":
                    war_freq = "1 / Week"
                elif str(clan['war_frequency']) == "never":
                    war_freq = "Rarely"
                else:
                    war_freq = "Unknown"
                # Set proper Social Media
                if not clan['social_media']:
                    social_media = ""
                else:
                    social_media = clan['social_media']
                # Set proper Notes
                if not clan['notes']:
                    clan_notes = ""
                else:
                    clan_notes = clan['notes']
                # Set Feeder info
                if clan['feeder'] == "Y":
                    feeder = ""
                else:
                    feeder = feeder_link
                # set icon based on clan size
                clan_dot = "![](%%yellowdot%%) "
                if clan['member_count'] < 35:
                    clan_dot = "![](%%greendot%%) "
                if clan['member_count'] > 45:
                    clan_dot = "![](%%reddot%%) "
                page_content += (f"\n{clan_dot}[{clan['clan_name'].replace(' ','&nbsp;')}]"
                                 f"(https://link.clashofclans.com/?action=OpenClanProfile&tag="
                                 f"{str(clan['clan_tag'])}) | [#{clan['clan_tag']}]"
                                 f"(https://www.clashofstats.com/clans/{clan['clan_name'].replace(' ',  '-')}-"
                                 f"{clan['clan_tag']}/members) | {str(clan['clan_level'])} | [{clan['leader']}]"
                                 f"({clan['leader_reddit']}) | {str(clan['member_count'])}/50 | "
                                 f"{war_freq} | {social_media} | {clan_notes} | {feeder}")
            # Locate start and end markers
            start = content.index(start_marker)
            end = content.index(end_marker) + len(end_marker)
            content = content.replace(content[start:end], f"{start_marker}{page_content}{end_marker}")
            logging.info(f"finished with {clan_type}")
        # Process feeder clans
        page_content = ("Home&nbsp;Clan | Clan&nbsp;Name | Clan&nbsp;Tag | Lvl | Type | Members | Contact | Notes\n"
                        "-|-|-|:-:|-|:-:|-|-")
        start_marker = "[](#feederStart)"
        end_marker = "[](#feederEnd)"
        sql = (f"SELECT a.feeder, a.clan_name, a.clan_tag, a.clan_level, a.social_media, a.member_count, "
               f"b.leader, b.leader_reddit, a.notes "
               f"FROM rcs_clans a, rcs_clans b "
               f"WHERE a.classification = 'feeder' AND a.feeder = b.clan_name "
               f"ORDER BY a.feeder")
        fetched = await conn.fetch(sql)
        for clan in fetched:
            contact = f"[{clan['leader']}]({clan['leader_reddit']})"
            if not clan['notes']:
                clan_notes = ""
            else:
                clan_notes = clan['notes']
            page_content += (f"\n{clan['feeder'].replace(' ', '&nbsp;')} | "
                             f"{clan['clan_name'].replace(' ', '&nbsp;')} | "
                             f"[#{clan['clan_tag']}](https://www.clashofstats.com/clans/"
                             f"{clan['clan_tag']}/members) | {str(clan['clan_level'])} | "
                             f"{clan['social_media']} | {str(clan['member_count'])}/50 | "
                             f"{contact} | {clan_notes}")
        start = content.index(start_marker)
        end = content.index(end_marker) + len(end_marker)
        content = content.replace(content[start:end], f"{start_marker}{page_content}{end_marker}")
        logging.info("finished with feeders")
    except Exception as inst:
        logging.warning(f"Compilation of content for {wiki_page} FAILED")
        logging.warning(type(inst))
        logging.warning(inst.args)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logging.error(f"Line Num: {exc_tb.tb_lineno}")
    try:
        page.edit(content, reason="Updating Clan Tracking Wikipage (ubuntu)")
        logging.info(f"{wiki_page} updated successfully")
    except Exception as inst:
        logging.warning(f"Wiki page update for {wiki_page} FAILED")
        logging.warning(type(inst))
        logging.warning(inst.args)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logging.error(f"Line Num: {exc_tb.tb_lineno}")


async def update_records(conn, subreddit, wiki_page):
    try:
        page = reddit.subreddit(subreddit).wiki[wiki_page]
        content = page.content_md
        page_content = ("| Clan&nbsp;Name | Wins | Losses | Ties | Total Wars\n"
                        ":--|:--|:-:|:-:|:-:|:-:")
        start_marker = "[](#recordStart)"
        end_marker = "[](#recordEnd)"
        sql = (f"SELECT clan_name, clan_tag, war_wins, war_losses, war_ties "
               f"FROM rcs_clans "
               f"ORDER BY war_wins DESC")
        fetched = await conn.fetch(sql)
        i = 1
        for clan in fetched:
            total_wars = clan['war_wins'] + clan['war_losses'] + clan['war_ties']
            page_content += (f"\n{str(i)}. | [{clan['clan_name'].replace(' ', '&nbsp;')}]"
                             f"(https://link.clashofclans.com/?action=OpenClanProfile&tag="
                             f"{clan['clan_tag']}) | {str(clan['war_wins'])} | {str(clan['war_losses'])} | "
                             f"{clan['war_ties']} | {str(total_wars)}")
            i += 1
        start = content.index(start_marker)
        end = content.index(end_marker) + len(end_marker)
        content = content.replace(content[start:end], f"{start_marker}{page_content}{end_marker}")
        logging.info(f"Page content compiles for {wiki_page}")
    except Exception as inst:
        logging.warning(f"Compilation of content for {wiki_page} FAILED")
        logging.warning(type(inst))
        logging.warning(inst.args)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logging.error(f"Line Num: {exc_tb.tb_lineno}")
    try:
        page.edit(content, reason="Updating Clan Records (ubuntu)")
        logging.info(f"{wiki_page} updated successfully")
    except Exception as inst:
        logging.warning('General Update Wiki Page Error')
        logging.warning(type(inst))
        logging.warning(inst.args)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logging.error(f"Line Num: {exc_tb.tb_lineno}")


def leader(clan, player):
    # print(f"Checking leader for {clan}. API shows {player}.")
    return player in leaders[clan] if clan in leaders else False


async def update_database(conn):
    try:
        session = aiohttp.ClientSession()
        sql = "SELECT clan_name, clan_tag, leader, clan_level, classification, war_wins FROM rcs_clans"
        fetched = await conn.fetch(sql)
        leader_data = ""
        for clan in fetched:
            clan_data = await coc_client.get_clan(f"#{clan['clan_tag']}")

            # clan_description = re.sub(r"[^a-zA-Z\s\d]+", "", clan_data.description)
            clan_description = clan_data.description.replace("'", "''")
            for member in clan_data.members:
                if member.role == "leader":
                    clan_leader = member.name
            if clan['clan_level'] != clan_data.level:
                payload = {
                    "avatar_url": clan_data.badge.url,
                    "content": (f"Please help us in congratulating {clan_data.name} "
                                f"on reaching level {str(clan_data.level)}!")
                }
                async with session.post(settings['rcsHooks']['botDev'], data=payload) as response:
                    logging.info(await response.text())
            if clan_data.war_win_streak > 5 and 8 < now.hour < 12:
                payload = {
                    "content": (f"Big congratulations to {clan_data.name} on their "
                                f"war win streak of {str(clan_data.war_win_streak)}.")
                }
                async with session.post(settings['rcsHooks']['botDev'], data=payload) as response:
                    logging.info(await response.text())
            if clan['war_wins'] != clan_data.war_wins and clan_data.war_wins % 50 == 0:
                prefix = random.choice(["Holy smokes, that is a lot of wins!",
                                        "Check this out!",
                                        "Milestone!",
                                        "And the wins keep coming!"])
                suffix = random.choice(["You are awesome!",
                                        "Keep up the great work!",
                                        "Go win a few more!"])
                payload = {
                    "avatar_url": clan_data.badge.url,
                    "content": f"{prefix} {clan_data.name} just hit **{str(clan_data.war_wins)}** wins! {suffix}"
                }
                async with session.post(settings['rcsHooks']['botDev'], data=payload) as response:
                    logging.info(await response.text())
            if not leader(clan_data.name, clan_leader) and clan['classification'] != "feeder" and clan['leader'] != clan_leader:
                if not (clan['clan_tag'] == "9GQVL988" and clan_leader[:5] == "Shock"):
                    print(f"Leader change for {clan_data.name} - {clan_leader}")
                    leader_data += f"{clan['clan_name']}: Leader changed from {clan['leader']} to {clan_leader}\n"
            sql = (f"UPDATE rcs_clans "
                   f"SET clan_level = {clan_data.level}, "
                   f"member_count = {clan_data.member_count}, "
                   f"war_frequency = '{clan_data.war_frequency}', "
                   f"clan_type = '{clan_data.type}', "
                   f"description = '{clan_description}', "
                   f"location = '{clan_data.location}', "
                   f"war_wins = {clan_data.war_wins}, ")
            if clan_data.public_war_log:
                war_log = 1
                sql += (f"war_ties = {clan_data.war_ties}, "
                        f"war_losses = {clan_data.war_losses}, ")
            else:
                war_log = 0
            sql += (f"win_streak = {clan_data.war_win_streak}, "
                    f"war_log_public = {war_log}, "
                    f"badge_url = '{clan_data.badge.url}', "
                    f"points = {clan_data.points}, "
                    f"vs_points = {clan_data.versus_points}, "
                    f"required_trophies = {clan_data.required_trophies} "
                    f"WHERE clan_tag = '{clan_data.tag[1:]}'")
            await conn.execute(sql)
            if leader_data != "" and 8 < now.hour < 12:
                payload = {
                    "embeds": [{
                        "color": color_pick(181, 0, 0),
                        "footer": {
                            "text": "Leader change detected",
                            "icon_url": (f"https://api-assets.clashofclans.com/badges/200/h8Hj8FDhK"
                                         f"2b1PdkwF7fEbTGY5UkT_lntLEOXbiLTujQ.png")
                        },
                        "fields": [
                            {"name": "Leader Changes", "value": leader_data},
                            {"name": "Disclaimer", "value": ("These changes may or may not be permanent. "
                                                             "Please investigate as appropriate.")}
                        ]
                    }]
                }
                async with session.post(settings['rcsHooks']['botDev'], data=payload) as response:
                    logging.info(await response.text())
        logging.info("Database update complete.")
    except Exception as inst:
        logging.error(f"Error updating Database")
        logging.error('Failed to update datebase')
        logging.error(type(inst))
        logging.error(inst.args)
        logging.error(inst)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logging.error(f"Line Num: {exc_tb.tb_lineno}")
    finally:
        await session.close()


async def clean_database(conn):
    try:
        sql = "SELECT clan_tag FROM rcs_clans"
        fetched = await conn.fetch(sql)
        for clan in fetched:
            if "#" in clan['clan_tag']:
                fixed_tag = clan['clan_tag'].replace("#", "")
                sql = f"UPDATE rcs_clans SET clan_tag = '{fixed_tag}' WHERE clan_tag = '{clan['clan_tag']}'"
                await conn.execute(sql)
        logging.info("Database cleaned")
    except Exception as inst:
        logging.error(f"Error cleaning database")
        logging.error(type(inst))
        logging.error(inst.args)
        logging.error(inst)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logging.error(f"Line Num: {exc_tb.tb_lineno}")


async def main():
    conn = await asyncpg.connect(host=settings['pg']['host'],
                             port=settings['pg']['port'],
                             user=settings['pg']['user'],
                             password=settings['pg']['pass'],
                             database=settings['pg']['db'])
    await clean_database(conn)
    await update_database(conn)
    await update_wiki_page(conn, subreddit, wiki_page)
    await update_records(conn, subreddit, "clan_records")
    await conn.close()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
    coc_client.close()
