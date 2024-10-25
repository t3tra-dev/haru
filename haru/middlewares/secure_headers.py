from haru.middleware import Middleware
from haru.request import Request
from haru.response import Response

from typing import Optional, Dict, List, Tuple, Union


class SecureHeadersOptions:
    content_security_policy: Optional[str] = "default-src 'self'"
    content_security_policy_report_only: Optional[str] = None
    x_content_type_options: Optional[str] = 'nosniff'
    x_frame_options: Optional[str] = 'SAMEORIGIN'
    strict_transport_security: Optional[str] = 'max-age=63072000; includeSubDomains; preload'
    referrer_policy: Optional[str] = 'no-referrer'
    x_permitted_cross_domain_policies: Optional[str] = 'none'
    x_xss_protection: Optional[str] = '0'
    cross_origin_opener_policy: Optional[str] = 'same-origin'
    cross_origin_embedder_policy: Optional[str] = 'require-corp'
    cross_origin_resource_policy: Optional[str] = 'same-origin'
    origin_agent_cluster: Optional[str] = '?1'
    remove_server_header: bool = True
    permissions_policy: Optional[Dict[str, Union[str, List[str]]]] = None


HEADERS_MAP: Dict[str, Tuple[str, str]] = {
    'content_security_policy': ('Content-Security-Policy', "default-src 'self'"),
    'x_content_type_options': ('X-Content-Type-Options', 'nosniff'),
    'x_frame_options': ('X-Frame-Options', 'SAMEORIGIN'),
    'strict_transport_security': ('Strict-Transport-Security', 'max-age=63072000; includeSubDomains; preload'),
    'referrer_policy': ('Referrer-Policy', 'no-referrer'),
    'x_permitted_cross_domain_policies': ('X-Permitted-Cross-Domain-Policies', 'none'),
    'x_xss_protection': ('X-XSS-Protection', '0'),
    'cross_origin_opener_policy': ('Cross-Origin-Opener-Policy', 'same-origin'),
    'cross_origin_embedder_policy': ('Cross-Origin-Embedder-Policy', 'require-corp'),
    'cross_origin_resource_policy': ('Cross-Origin-Resource-Policy', 'same-origin'),
    'origin_agent_cluster': ('Origin-Agent-Cluster', '?1'),
}


class SecureHeadersMiddleware(Middleware):
    """
    Middleware to automatically add security-related HTTP headers to responses.
    """

    def __init__(self, options: Optional[SecureHeadersOptions] = None):
        """
        Initialize the SecureHeadersMiddleware with optional configurations.

        :param options: Configuration options for the middleware.
        :type options: Optional[SecureHeadersOptions]
        """
        self.options = options or SecureHeadersOptions()

    async def before_response(self, request: Request, response: Response) -> None:
        """
        Modify the response before it's sent to the client by adding security headers.

        :param request: The incoming HTTP request.
        :type request: Request
        :param response: The HTTP response to be sent.
        :type response: Response
        """
        headers_to_set = self._get_headers_to_set()

        for header_name, header_value in headers_to_set.items():
            response.headers[header_name] = header_value

        if self.options.remove_server_header:
            response.headers.pop('Server', None)

    def _get_headers_to_set(self) -> Dict[str, str]:
        """
        Generate a dictionary of headers to set based on the provided options.

        :return: A dictionary where keys are header names and values are header values.
        :rtype: Dict[str, str]
        """
        headers = {}

        for option_name, (header_name, default_value) in HEADERS_MAP.items():
            option_value = getattr(self.options, option_name, None)
            if option_value is not None:
                if option_value is not False:
                    headers[header_name] = option_value
            else:
                headers[header_name] = default_value

        if self.options.content_security_policy_report_only:
            headers['Content-Security-Policy-Report-Only'] = self.options.content_security_policy_report_only

        if self.options.permissions_policy:
            permissions_policy_header = self._format_permissions_policy(self.options.permissions_policy)
            if permissions_policy_header:
                headers['Permissions-Policy'] = permissions_policy_header

        return headers

    def _format_permissions_policy(self, policy: Dict[str, Union[str, List[str]]]) -> str:
        """
        Format the Permissions-Policy header value.

        :param policy: A dictionary of permissions and their allowed origins.
        :type policy: Dict[str, Union[str, List[str]]]
        :return: The formatted Permissions-Policy header value.
        :rtype: str
        """
        directives = []
        for feature, value in policy.items():
            if isinstance(value, bool):
                directive_value = '*' if value else '()'
            elif isinstance(value, str):
                directive_value = value
            elif isinstance(value, list):
                directive_value = ' '.join(value)
            else:
                continue
            directives.append(f"{feature}={directive_value}")
        return ', '.join(directives)
