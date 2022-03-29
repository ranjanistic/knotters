
from requests import post as postRequest, delete as deleteRequest, get as getRequest
from github import Github as GHub
from .env import GITHUBBOTTOKEN, PUBNAME, ISPRODUCTION, DISCORDBOTTOKEN, DISCORDSERVERID
from .settings import SENDER_API_URL_SUBS, SENDER_API_HEADERS, DISCORD_KNOTTERS_API_URL, DISCORD_KNOTTERS_HEADERS

try:
    if GITHUBBOTTOKEN:
        Github = GHub(GITHUBBOTTOKEN)
        GithubKnotters = Github.get_organization(PUBNAME)
    else:
        Github = None
        GithubKnotters = None
except Exception as e:
    print(e)
    Github = None
    GithubKnotters = None


def GH_API(token=GITHUBBOTTOKEN):
    return GHub(token)


class DiscordServer():
    def __init__(self, token, serverID) -> None:
        self.token = token
        self.serverID = serverID
        self.API_URL = DISCORD_KNOTTERS_API_URL
        pass

    def createChannel(self, name, type='GUILD_TEXT', public=False, category=None, message=""):
        resp = postRequest(
            self.API_URL + '/create-channel',
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


Discord = DiscordServer(token=DISCORDBOTTOKEN, serverID=DISCORDSERVERID)


class Sender():
    def addUserToMailingServer(email: str, first_name: str, last_name: str) -> bool:
        """
        Adds a user (assuming to be new) to mailing server.
        By default, also adds the subscriber to the default group.
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

        :fullData: If True, returns only the id of user from mailing server. Default: False
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
        """
        Removes user from mailing server.
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
            return None

    def addUserToMailingGroup(email: str, groupID: str) -> bool:
        """
        Adds user to a mailing group (assuming the user to be an existing server subscriber).
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
            return None

    def removeUserFromMailingGroup(groupID: str, email: str) -> bool:
        """
        Removes user from a mailing group.
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
