import sys
import time
import json
import os.path
import logging
from zlib import crc32
from datetime import datetime

from colorama import Fore, Style

from src.hunt.utilities.hunt import find_hunt_attributes_path, format_mmr
from src.hunt.utilities.file_watcher import FileWatchdog
from src.hunt.attributes_parser import ElementTree, Team, Player, parse_teams
from src.hunt.constants import USER_PROFILE_ID, RESOURCES_PATH

TEAM_HASHES: list[int] = []


def main():
    # Setup logging
    logging.basicConfig(format="[%(asctime)s, %(levelname)s] %(message)s",
                        datefmt="%H:%M", level=logging.DEBUG, stream=sys.stdout)

    # Locate the attributes file
    attributes_path: str = find_hunt_attributes_path()
    assert os.path.exists(attributes_path), "Attributes file does not exist."

    # Set up a file watcher to listen for changes on the attributes file
    file_watchdog: FileWatchdog = FileWatchdog(file_path=attributes_path, callback=attributes_file_modified)
    file_watchdog.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Stop the file watcher if a keyboard interrupt is received
        file_watchdog.stop()
    file_watchdog.join()

    # Signal to the user that we're shutting down
    logging.info("Shutting down.")


def attributes_file_modified(file_path: str):
    try:
        # Attempt to parse the attributes file;
        #  when the file is being written to by the game
        #  it usually has a step where it contains garbage
        #  data (empty?), which will throw an exception.
        parsed_attributes: ElementTree = ElementTree.parse(source=file_path)
    except ElementTree.ParseError as exception:
        # Skip the update
        logging.debug(f"Failed to parse the attributes file: {exception=}")
        return

    # Parse the teams from the attributes file
    try:
        teams: tuple[Team] = parse_teams(root=parsed_attributes.getroot())
    except (AttributeError, AssertionError) as exception:
        logging.debug(f"Failed to parse the attributes file: {exception=}")
        return

    # Check if the teams are empty
    if not teams:
        logging.warning("Parsed 0 teams from the attributes file.")
        return

    # Prevent printing the same data multiple times and save them to a file
    team_hash: int = hash(teams)
    if team_hash in TEAM_HASHES:
        return
    TEAM_HASHES.append(team_hash)

    # Save the data to disk
    if save_teams_to_file(teams=teams):
        logging.debug("Team data already saved to disk.")
        return  # If the file already exists, skip logging

    # Print useful data from the match
    log_player_data(teams=teams)


def save_teams_to_file(teams: tuple[Team]) -> bool:
    """
    Saves the parsed teams to a json file.
    :param teams: a tuple of parsed teams
    :return: True if the file hash already exists, otherwise False
    """
    now: datetime = datetime.now()
    teams_json: str = json.dumps(teams, indent=2, default=vars)

    # Generate the file path
    teams_hash: int = crc32(teams_json.encode())
    generated_file_path: str = os.path.join(RESOURCES_PATH,
                                            f"{now.year}-{now.month:02d}-{now.day:02d}",
                                            f"{now.hour:02d}-{now.minute:02d}-{teams_hash:08x}.json")

    # Create the directories
    directory_path: str = os.path.dirname(generated_file_path)
    os.makedirs(name=directory_path, exist_ok=True)

    # Check if the file already exists
    for file_name in os.listdir(directory_path):
        if f"{teams_hash:08x}" in file_name:
            return True  # This file already exists

    # Save the file
    with open(generated_file_path, mode="w") as file:
        file.write(teams_json)

    return False  # This file doesn't exist yet


def log_player_data(teams: tuple[Team]):
    """
    Logs the user's MMR, the players they were killed by,
      and the players they killed.
    :param teams: a tuple of parsed teams
    """
    players: tuple[Player] = tuple(player for team in teams for player in team.players)
    players_killed: tuple[Player] = tuple(filter(lambda player: player.killed_by_me, players))
    players_killed_me: tuple[Player] = tuple(filter(lambda player: player.killed_me, players))
    user: Player | None = next(filter(lambda player: player.profile_id == USER_PROFILE_ID, players), None)

    if user:
        logging.info(f"User MMR: {format_mmr(user.mmr)}")
    else:
        logging.warning("Failed to locate the user by their profile id.")
    player: Player
    for player in players_killed_me:
        logging.info(f"  Killed by {Fore.RED}{player.name}{Style.RESET_ALL} ({format_mmr(player.mmr)})")
    for player in players_killed:
        logging.info(f"  Killed {Fore.GREEN}{player.name}{Style.RESET_ALL} ({format_mmr(player.mmr)})")


if __name__ == "__main__":
    main()
