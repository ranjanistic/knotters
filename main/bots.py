import requests
from github import Github as GHub
from .env import GITHUBBOTTOKEN, PUBNAME, ISPRODUCTION
from .settings import SENDER_API_URL_SUBS, SENDER_API_HEADERS

if ISPRODUCTION:
    Github = GHub(GITHUBBOTTOKEN)
    GithubKnotters = Github.get_organization(PUBNAME)
else:
    Github = None
    GithubKnotters = None

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
        if not ISPRODUCTION: return True
        try:
            response = requests.request(
                'POST', SENDER_API_URL_SUBS, headers=SENDER_API_HEADERS, json=payload).json()
            return response['success']
        except:
            return False

    def getUserFromMailingServer(email: str, fullData: bool = False) -> dict:
        """
        Returns user data from mailing server.

        :fullData: If True, returns only the id of user from mailing server. Default: False
        """
        if not ISPRODUCTION: return True
        try:
            if not email:
                return None
            response = requests.request(
                'GET', f"{SENDER_API_URL_SUBS}/by_email/{email}", headers=SENDER_API_HEADERS).json()
            return response['data'] if fullData else response['data']['id']
        except:
            return None


    def removeUserFromMailingServer(email: str) -> bool:
        """
        Removes user from mailing server.
        """
        if not ISPRODUCTION: return True
        try:
            subscriber = Sender.getUserFromMailingServer(email, True)
            if not subscriber:
                return False

            payload = {
                "subscribers": [subscriber['id']]
            }
            response = requests.request(
                'DELETE', SENDER_API_URL_SUBS, headers=SENDER_API_HEADERS, json=payload).json()
            return response['success']
        except:
            return None


    def addUserToMailingGroup(email: str, groupID: str) -> bool:
        """
        Adds user to a mailing group (assuming the user to be an existing server subscriber).
        """
        if not ISPRODUCTION: return True
        try:
            subID = Sender.getUserFromMailingServer(email)
            if not subID:
                return False
            payload = {
                "subscribers": [subID],
            }
            response = requests.request(
                'POST', f"{SENDER_API_URL_SUBS}/groups/{groupID}", headers=SENDER_API_HEADERS, json=payload).json()

            return response['success']
        except:
            return None


    def removeUserFromMailingGroup(groupID: str, email: str) -> bool:
        """
        Removes user from a mailing group.
        """
        if not ISPRODUCTION: return True
        try:
            subID = Sender.getUserFromMailingServer(email=email)
            if not subID:
                return False
            payload = {
                "subscribers": [subID]
            }
            response = requests.request(
                'DELETE', f"{SENDER_API_URL_SUBS}/groups/{groupID}", headers=SENDER_API_HEADERS, json=payload).json()
            return response['success']
        except:
            return None
