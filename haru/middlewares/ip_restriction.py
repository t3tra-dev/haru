"""
This module defines the `IPRestrictionMiddleware` class, which restricts access to resources
based on the client's IP address. The middleware allows or blocks requests from specified
IP addresses or networks (in CIDR notation), providing a way to control access to an application
based on the client's IP.

Usage example:

.. code-block:: python

    app.add_middleware(IPRestrictionMiddleware(allowed_ips=['192.168.1.0/24']))

Parameters:
    allowed_ips (List[str]): A list of IP addresses or CIDR networks that are allowed access.
    blocked_ips (List[str]): A list of IP addresses or CIDR networks that are explicitly blocked.
    default_action (str): The default action for IPs not in the `allowed_ips` or `blocked_ips` lists.
                          Can be 'allow' (default) or 'block'.

Note:
    If both `allowed_ips` and `blocked_ips` are specified, the `blocked_ips` list takes precedence.
"""

from typing import List
from ipaddress import ip_address, ip_network
from haru.middleware import Middleware
from haru.request import Request
from haru.exceptions import Forbidden

__all__ = ['IPRestrictionMiddleware']


class IPRestrictionMiddleware(Middleware):
    """
    IP Restriction Middleware

    This middleware restricts access to resources based on the client's IP address.
    It allows or blocks requests from specified IP addresses or networks.

    :param allowed_ips: A list of IP addresses or CIDR networks that are allowed access.
    :type allowed_ips: List[str]
    :param blocked_ips: A list of IP addresses or CIDR networks that are explicitly blocked.
    :type blocked_ips: List[str]
    :param default_action: The default action for IPs not in the `allowed_ips` or `blocked_ips` lists.
                           Can be 'allow' (default) or 'block'.
    :type default_action: str

    :raises Forbidden: If the client's IP address is blocked or not allowed.
    """

    def __init__(
        self,
        allowed_ips: List[str] = None,
        blocked_ips: List[str] = None,
        default_action: str = 'allow',
    ):
        """
        Initialize the `IPRestrictionMiddleware` with allowed and blocked IPs and a default action for unspecified IPs.

        :param allowed_ips: A list of IP addresses or CIDR networks that are allowed access.
        :type allowed_ips: List[str]
        :param blocked_ips: A list of IP addresses or CIDR networks that are explicitly blocked.
        :type blocked_ips: List[str]
        :param default_action: The default action for IPs not in the `allowed_ips` or `blocked_ips` lists. Defaults to 'allow'.
        :type default_action: str
        """
        super().__init__()
        self.allowed_ips = [ip_network(ip) for ip in (allowed_ips or [])]
        self.blocked_ips = [ip_network(ip) for ip in (blocked_ips or [])]
        self.default_action = default_action

    def before_request(self, request: Request) -> None:
        """
        Check the client's IP address and determine whether to allow or block the request.
        If the IP is in the blocked list, the request is denied. If the IP is in the allowed list, the request is accepted.
        If no IP lists are defined, the default action is taken.

        :param request: The current HTTP request object.
        :type request: Request

        :raises Forbidden: If the client's IP address is blocked or not allowed.
        """
        client_ip = ip_address(request.remote_addr)

        # Check if IP is in the blocked list
        for net in self.blocked_ips:
            if client_ip in net:
                raise Forbidden(description='Access denied.')

        # Check if IP is in the allowed list
        if self.allowed_ips:
            for net in self.allowed_ips:
                if client_ip in net:
                    return
            raise Forbidden(description='Access denied.')
        else:
            # Apply default action
            if self.default_action == 'block':
                raise Forbidden(description='Access denied.')
