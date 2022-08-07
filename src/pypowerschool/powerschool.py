#
# powerschool.py
#
# Copyright (c) 2022 Doug Penny
# Licensed under MIT
#
# See LICENSE.md for license information
#
# SPDX-License-Identifier: MIT
#

import base64
import datetime
import json
import sys
from typing import Dict, List, Union
from urllib.parse import urljoin

import httpx

from pypowerschool.endpoints import CoreResourcesMixin


class Client(CoreResourcesMixin):
    """
    The Client object handles GET and POST requests to a PowerSchool server.

    A data access plugin must be installed and enabled on the PowerShoool
    server to access data via the API. For more information about creating
    a data access PowerSchool plugin, please refer to the PowerSchool
    developer documentation.
    https://support.powerschool.com/developer/

    Requests are made asynchronously when possible. There are a few situations,
    like requesting mulitple pages of data, that synchronous calls are
    required.

    Public Methods:
        fetch_item(
            self, resource_endpoint: str, expansions: str = None,
            extensions: str = None, query: str = None) -> Dict
        fetch_items(
            self, resource_endpoint: str, expansions: str = None,
            extensions: str = None, query: str = None) -> List
        fetch_metadata(self) -> Dict
        post_data(self, endpoint: str, post_data: Dict) -> Union[None, int]
        powerquery(self, powerquery_endpoint: str, params: Dict = None) -> List
        resource_count(self, resource_url: str, params: str = None) -> int
    """

    def __new__(cls, *args):
        """
        Construct a new, singleton instance of the Client class.
        """
        if not hasattr(cls, 'instance'):
            cls.instance = super(Client, cls).__new__(cls)
        return cls.instance

    def __init__(self, url: str, client_id: str, client_secret: str) -> None:
        """
        Initializes a new Client object.

        The client ID and client secret can be found under
        Data Provider Configuration after installing a basic data access
        PowerSchool plugin.

        Args:
            base_url:
                Base URL of the PowerSchool server
            client_id:
                Client ID for accessing the PowerSchool server
            client_secret:
                Client secret for accessing the PowerSchool server
        """
        self.base_url = url
        self.client_id = client_id.encode("UTF-8")
        self.client_secret = client_secret.encode("UTF-8")
        try:
            self.headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": self._access_token(),
            }
        except httpx.RequestError as e:
            sys.stderr.write(f"An error occured making the request: {e}\n")
        except httpx.HTTPStatusError as e:
            sys.stderr.write(f"Error response {e.response.status_code}\n")
            sys.stderr.write(f"A connection error occured: {e}\n")
        except Exception as e:
            sys.stderr.write(f"An unknown error occured: {e}\n")

    def _access_token(self) -> str:
        """
        Fetches a valid access token.

        Retrieves a valid access token whic is used in all future requests.

        Returns:
            A string to be used as the value of the HTTP Authorization header.
        """
        if hasattr(self, "access_token_response"):
            if self.access_token_response["expiration_datetime"] > datetime.datetime.now():
                return f"Bearer {self.access_token_response['access_token']}"
        token_url = self.base_url + "/oauth/access_token"
        credentials = base64.b64encode(self.client_id + b":" + self.client_secret)
        auth_string = f"Basic {str(credentials, encoding='utf8')}"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "Authorization": auth_string,
        }
        data = "grant_type=client_credentials"
        r = httpx.post(token_url, data=data, headers=headers)
        response = r.json()
        auth_error = response.get('error')
        if auth_error:
            sys.stderr.write(f"A connection error occured: {auth_error}\n")
        response["expiration_datetime"] = datetime.datetime.now() + datetime.timedelta(
            seconds=int(response["expires_in"])
        )
        self.access_token_response = response
        return "Bearer " + response["access_token"]

    def _access_token_expired(self) -> bool:
        """
        Checkes access token expiration.

        Checkes to see if an access token exists and, if so, if it has expired.

        Returns:
            True if the token has expired or does not exist or
            False if the token exists and is valid.
        """
        if hasattr(self, "access_token_response"):
            if self.access_token_response["expiration_datetime"] > datetime.datetime.now():
                return False
            else:
                return True
        else:
            return True

    async def fetch_item(
            self, resource_endpoint: str, expansions: str = None, extensions: str = None,
            query: str = None) -> Dict:
        """
        Fetches a single record from PowerSchool.

        Args:
            resource_endpoint (str):
                Endpoint URL for the requested resource
            expansions (str, optional):
                Comma-delimited list of elements to expand
            extensions (str, optional):
                Comma-delimited list of extensions (1:1) to query
            query (str, optional):
                Criteria for selecting a subset of records

        Returns:
            A dictionary representing the record retrieved.
        """
        endpoint_url = urljoin(self.base_url, resource_endpoint)
        params = {}
        if expansions:
            params['expansions'] = expansions
        if extensions:
            params['extensions'] = extensions
        if query:
            params['q'] = query
        if self._access_token_expired():
            self.headers["Authorization"] = self._access_token()
        async with httpx.AsyncClient() as async_client:
            return await async_client.get(endpoint_url, headers=self.headers, params=params)

    async def fetch_items(
            self, resource_endpoint: str, expansions: str = None, extensions: str = None,
            query: str = None) -> List:
        """
        Fetches a collection of records from PowerSchool.

        Retrieves a collection of records from the PowerSchool server.
        PowerSchool pages data, so we have to incrementally build up the
        list of items in the collection.

        Args:
            resource_endpoint (str):
                Endpoint URL for the requested resource
            expansions (str, optional):
                Comma-delimited list of elements to expand
            extensions (str, optional):
                Comma-delimited list of extensions (1:1) to query
            query (str, optional):
                Criteria for selecting a subset of records

        Returns:
            A list of dictionaries representing the collection retrieved.
        """
        resource_name = resource_endpoint[resource_endpoint.rfind('/') + 1:]
        key_1 = resource_name + 's'
        key_2 = resource_name
        endpoint_url = urljoin(self.base_url, resource_endpoint)
        params = {}
        if expansions:
            params['expansions'] = expansions
        if extensions:
            params['extensions'] = extensions
        if query:
            params['q'] = query
        resource_count = self.resource_count(endpoint_url, params)
        data = []
        page_number = 1
        with httpx.Client() as client:
            while len(data) < resource_count:
                params['page'] = str(page_number)
                try:
                    requested_resource_response = client.get(
                        endpoint_url, headers=self.headers, params=params)
                    requested_resources = requested_resource_response.json()[
                        key_1][key_2]
                    if isinstance(requested_resources, list):
                        data.extend(requested_resources)
                    else:
                        resource_dict = [requested_resources]
                        data.extend(resource_dict)
                except Exception as e:
                    sys.stderr.write(f"An error occured retrieving items: {e}\n")
                    return []
                page_number += 1
        return data

    def fetch_metadata(self) -> Dict:
        """
        Fetches PowerSchool server metadata.

        Returns:
            A dictionary of server metadata.
        """
        metadata_endpoint = urljoin(self.base_url, "ws/v1/metadata")
        metadata_response = httpx.get(metadata_endpoint, headers=self.headers)
        return metadata_response.json()["metadata"]

    async def post_data(self, endpoint: str, post_data: Dict) -> Union[None, int]:
        """
        Creates a new entry for the given endpoint.

        Args:
            endpoint (str):
                Endpoint URL for the new entry
            post_data (dict):
                Dictionay of values used for creating the new entry

        Returns:
            If creation is successful, the ID of the new entry,
            otherwise, None.
        """
        if self._access_token_expired():
            self.headers["Authorization"] = self._access_token()
        post_url = urljoin(self.base_url, endpoint)
        data = json.dumps(post_data)
        try:
            async with httpx.AsyncClient() as async_client:
                response = await async_client.post(post_url, data=data, headers=self.headers)
            response = response.json()
            if response['insert_count'] == 1 and response['result'][0]['status'] == 'SUCCESS':
                return response['result'][0]['success_message']['id']
            else:
                return None
        except Exception as e:
            sys.stderr.write(f"An error occured attempting to post data: {e}\n")
            return None

    def powerquery(self, powerquery_endpoint: str, args: Dict = None) -> List:
        """
        Invokes a PowerQuery.

        A PowerQuery is a data source that can be accessed via the API.
        A typical PowerQuery declares a set of arguments, a set of
        columns, and a select statement. A PowerQuery may be pre-defined
        by PowerSchool or it may be defined by a third-party and installed
        in PowerSchool via the Plugin Package. Once the plugin is installed
        and enabled, the third-party PowerQuery becomes accessible as another
        resource in PowerSchool.

        Args:
            powerquery_endpoint (str):
                Endpoint URL for the PowerQuery resource
            args (Dict, optional):
                Dictionary of arguments to pass to the PowerQuery

        Returns:
            A list of dictionaries representing the collection retrieved.
        """
        if self._access_token_expired():
            self.headers["Authorization"] = self._access_token()
        powerquery_url = urljoin(self.base_url, powerquery_endpoint)
        body = json.dumps(args) if args else '{}'
        data = []
        params = {'page': 1}
        with httpx.Client() as client:
            count_response = client.post(powerquery_url + '/count', data=body,
                                         headers=self.headers)
            items_count = count_response.json().get('count', 0)
            while len(data) < items_count:
                try:
                    response = client.post(powerquery_url, data=body, headers=self.headers,
                                           params=params)
                    data.extend(response.json()['record'])
                except KeyError:
                    if response.json().get('message') == 'Validation Failed':
                        sys.stderr.write(
                            f"{response.json().get('message')}\n{response.json().get('errors')}\n"
                        )
                    else:
                        sys.stderr.write(f"An error occured: {response.json().get('message')}\n")
                    return []
                except Exception as generic_error:
                    sys.stderr.write(f"An error occured executing a PowerQuery: {generic_error}\n")
                    return []
                params['page'] = params['page'] + 1
        return data

    def resource_count(self, resource_url: str, params: str = None) -> int:
        """
        Retrieves the number of resources available.

        Args:
            endpoint (str):
                Endpoint URL for the requested resource
            params (dict, optional):
                Dictionay of parameters to include with the request. These may
                included expansions, extensions, and/or queries.

        Returns:
            Integer value equal to the numebr of resources available.
        """
        resource_count_url = f"{resource_url}/count"
        if self._access_token_expired():
            self.headers["Authorization"] = self._access_token()
        try:
            with httpx.Client() as client:
                data = client.get(resource_count_url, headers=self.headers, params=params)
            return data.json()["resource"]["count"]
        except Exception as e:
            sys.stderr.write(f"An error occured retrieving a resource count: {e}\n")
            return 0
