from __future__ import annotations

from dataclasses import dataclass

from .xml.serializable import Serializable, MappingGenerator, XmlElement
from .player import Player


@dataclass(frozen=True)
class SerializableTeam(Serializable):
    handicap: int
    is_invite: bool
    mmr: int
    players_count: int
    own_team: bool

    # Serialization
    @staticmethod
    def _generate_prefix(team_id: int) -> str:
        """
        Generate a prefix for the class.
        :param team_id: the id of the team
        :return: a MissionBagEntry prefix
        """
        return f"MissionBagTeam_{team_id}"

    @staticmethod
    def _data_mappings() -> MappingGenerator:
        """
        Yield each variable name and its corresponding attribute suffix.
        :return: a generator which yields the name, value
        """
        # Yield the values
        yield "handicap", "handicap"
        yield "is_invite", "isinvite"
        yield "mmr", "mmr"
        yield "players_count", "numplayers"
        yield "own_team", "ownteam"

    # noinspection PyMethodOverriding
    def serialize(self, root: XmlElement, *, team_id: int) -> None:  # type: ignore
        """
        Serialize a SerializableTeam instance.
        :param root: the root element to serialize into
        :param team_id: the id of the team
        """
        # Generate the prefix
        prefix: str = SerializableTeam._generate_prefix(team_id)

        # Serialize the data
        super().serialize(root, prefix)

    # noinspection PyMethodOverriding
    @classmethod
    def deserialize(cls, root: XmlElement, team_id: int) -> SerializableTeam:  # type: ignore
        """
        Deserialize a series of elements into a SerializableTeam instance.
        :param root: the root element to serialize into
        :param team_id: the id of the team
        :return: a serialized SerializableTeam instance
        """
        # Generate the prefix
        prefix: str = SerializableTeam._generate_prefix(team_id)

        # Deserialize the data
        return super(cls, cls).deserialize(root, prefix)


@dataclass(frozen=True)
class Team:
    handicap: int
    is_invite: bool
    mmr: int
    own_team: bool
    players: tuple[Player, ...]
