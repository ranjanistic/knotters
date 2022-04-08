from github import Github as GHub
from main.strings import DiscordChannel
from requests import delete as deleteRequest
from requests import get as getRequest
from requests import post as postRequest

from .env import (DISCORDBOTTOKEN, DISCORDSERVERID, GITHUBBOTTOKEN,
                  ISPRODUCTION, PUBNAME)
from .settings import (DISCORD_KNOTTERS_API_URL, DISCORD_KNOTTERS_HEADERS,
                       SENDER_API_HEADERS, SENDER_API_URL_SUBS)

try:
    if GITHUBBOTTOKEN:
        Github = GHub(GITHUBBOTTOKEN)
        GithubKnotters = Github.get_organization(PUBNAME)
    else:
        Github = None
        GithubKnotters = None
except Exception as e:
    # print(e)
    Github = None
    GithubKnotters = None


def GH_API(token: str = GITHUBBOTTOKEN) -> GHub:
    """Github API object for given access token

    Args:
        token (str, optional): Github access token. Defaults to main.env.GITHUBBOTTOKEN.

    Returns:
        GHub: The Github API object.
    """
    return GHub(token)


class DiscordServer():
    """Custom class to manage Discord Server methods and attributes
    """
    API_URL = DISCORD_KNOTTERS_API_URL

    CREATE_CHANNEL_URL = '/create-channel'

    @property
    def create_channel_url(self):
        return self.API_URL + self.CREATE_CHANNEL_URL

    def __init__(self, token, serverID) -> None:
        self.token = token
        self.serverID = serverID
        pass

    def createChannel(self, name: str, type: str = DiscordChannel.GUILD_TEXT, public: bool = False, category: str = None, message: str = "") -> str:
        """Create a discord channel

        Args:
            name (str): The name of the channel
            type (str, optional): The type of the channel. Defaults to main.strings.DiscordChannel.GUILD_TEXT.
            public (bool, optional): Whether the channel is public or not. Defaults to False.
            category (str, optional): The category of the channel. Defaults to None.
            message (str, optional): The message to send to the channel. Defaults to "".

        Returns:
            str or bool: The channel ID, or False if the channel could not be created.
        """
        try:
            resp = postRequest(
                self.create_channel_url,
                headers=DISCORD_KNOTTERS_HEADERS,
                json={
                    "channel_name": name,
                    "channel_type": type,
                    "public": public,
                    "channel_category": category,
                    "message": message
                }
            )
            if resp.status_code == 200:
                return resp.json()['channel_id']
            else:
                return False
        except Exception as e:
            return False


Discord = DiscordServer(token=DISCORDBOTTOKEN, serverID=DISCORDSERVERID)
"""DiscordServer object for the Discord server"""


class Sender():
    """To manage Sender.net marketing mail groups
    """
    def addUserToMailingServer(email: str, first_name: str, last_name: str) -> bool:
        """Adds a user (assuming to be new) to mailing server.
        By default, also adds the subscriber to the default group.

        Args:
            email (str): The email of the user.
            first_name (str): The first name of the user.
            last_name (str): The last name of the user.

        Returns:
            bool: True if the user was added to mailing server, False otherwise.
        """
        payload = {
            "email": email,
            "firstname": first_name,
            "lastname": last_name,
            "groups": ["dL8pBD"],
        }
        if not ISPRODUCTION:
            return True
        try:
            response = postRequest(
                SENDER_API_URL_SUBS, headers=SENDER_API_HEADERS, json=payload).json()
            return response['success']
        except:
            return False

    def getUserFromMailingServer(email: str, fullData: bool = False) -> dict:
        """
        Returns user data from mailing server.

        Args:
            email (str): The email of the user.
            fullData (bool, optional): Whether to return full data or or just id. Defaults to False.
        
        Returns:
            dict or str: The user data or id, or None if the user could not be found.
        """
        if not ISPRODUCTION:
            return True
        try:
            if not email:
                return None
            response = getRequest(
                f"{SENDER_API_URL_SUBS}/by_email/{email}", headers=SENDER_API_HEADERS).json()
            return response['data'] if fullData else response['data']['id']
        except:
            return None

    def removeUserFromMailingServer(email: str) -> bool:
        """Removes a user from mailing server.

        Args:
            email (str): The email of the user.

        Returns:
            bool: True if the user was removed from mailing server, False otherwise.
        """
        if not ISPRODUCTION:
            return True
        try:
            subscriber = Sender.getUserFromMailingServer(email, True)
            if not subscriber:
                return False

            payload = {
                "subscribers": [subscriber['id']]
            }
            response = deleteRequest(
                SENDER_API_URL_SUBS, headers=SENDER_API_HEADERS, json=payload).json()
            return response['success']
        except:
            return False

    def addUserToMailingGroup(email: str, groupID: str) -> bool:
        """Adds user to a mailing group (assuming the user to be an existing server subscriber).

        Args:
            email (str): The email of the user.
            groupID (str): The group ID.

        Returns:
            bool: True if the user was added to mailing group, False otherwise.
        """
        if not ISPRODUCTION:
            return True
        try:
            subID = Sender.getUserFromMailingServer(email)
            if not subID:
                return False
            payload = {
                "subscribers": [subID],
            }
            response = postRequest(
                f"{SENDER_API_URL_SUBS}/groups/{groupID}", headers=SENDER_API_HEADERS, json=payload).json()
            return response['success']
        except:
            return False

    def removeUserFromMailingGroup(groupID: str, email: str) -> bool:
        """Removes user from a mailing group.

        Args:
            groupID (str): The group ID.
            email (str): The email of the user.

        Returns:
            bool: True if the user was removed from mailing group, False otherwise.
        """
        if not ISPRODUCTION:
            return True
        try:
            subID = Sender.getUserFromMailingServer(email=email)
            if not subID:
                return False
            payload = {
                "subscribers": [subID]
            }
            response = deleteRequest(
                f"{SENDER_API_URL_SUBS}/groups/{groupID}", headers=SENDER_API_HEADERS, json=payload).json()
            return response['success']
        except:
            return None
