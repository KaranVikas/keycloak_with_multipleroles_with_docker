import logging

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from jwt import PyJWKClient
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header

User = get_user_model()

logger = logging.getLogger(__name__)


class JWTAuthentication(BaseAuthentication):
  """
  DRF authentication class for JWT tokens
  - extract bearer token
  - validates signature with keycloak realm JWKS
  - enforces iss, aud, exp (with leeway)
  Returns (user, token_payload) where user is a Django User object
  """

  www_authenticate_realm = 'api'

  def authenticate(self, request):
    """
    Authenticate the request and return a two-tuple of (user, token).
    """
    auth = get_authorization_header(request).split()

    if not auth or auth[0].lower() != b'bearer':
      return None

    if len(auth) == 1:
      raise exceptions.AuthenticationFailed('Invalid token header. No credentials provided.')
    elif len(auth) > 2:
      raise exceptions.AuthenticationFailed('Invalid token header. Token string should not contain spaces.')

    raw_token = auth[1].decode('utf-8')

    # Validate and decode token
    payload = self._validate_token(raw_token)
    logger.info("__________________________________")
    logger.info(f"Token payload: {payload}")

    # Extract user information from token
    keycloak_id = payload.get("sub")
    username = payload.get("preferred_username") or payload.get("username") or payload.get("email") or keycloak_id
    email = payload.get("email", "")
    first_name = payload.get("given_name", "")
    last_name = payload.get("family_name", "")
    name = payload.get("name", f"{first_name} {last_name}".strip())

    # Extract user_type from roles
    user_type = self._extract_user_type(payload)

    # Get or create Django user
    django_user = self._get_or_create_user(
      keycloak_id=keycloak_id,
      username=username,
      email=email,
      first_name=first_name,
      last_name=last_name,
      name=name,
      user_type=user_type,
      payload=payload
    )

    logger.info(
      f"✅ Authentication successful for user: {django_user.username} (ID: {django_user.id}, Type: {django_user.user_type})")
    return (django_user, payload)

  def _validate_token(self, raw_token: str) -> dict:
    """
    Validate JWT token with Keycloak JWKS and return decoded payload.
    """
    jwk_client = PyJWKClient(settings.KEYCLOAK_JWKS_URL)
    logger.info(f"JWK Client initialized with URL: {settings.KEYCLOAK_JWKS_URL}")
    logger.info("got jwk_client", jwk_client)
    try:
      unverified_header = jwt.get_unverified_header(raw_token)
      logger.info(f"Token header (kid): {unverified_header.get('kid')}")
      logger.info("__________________________________")
      logger.info("getting signing key from keycloak")
      signing_key = jwk_client.get_signing_key_from_jwt(raw_token)
      logger.info(f"✅ Got signing key from keycloak - Key type: {type(signing_key.key)}")
    except jwt.exceptions.InvalidTokenError as e:
      logger.error(f"❌ Unable to obtain signing key: {e}")
      raise exceptions.AuthenticationFailed(f"Unable to obtain signing key: {e}")

    try:
      payload = jwt.decode(
        raw_token,
        signing_key.key,
        algorithms=['RS256'],
        audience=settings.KEYCLOAK_CLIENT_ID,
        issuer=settings.KEYCLOAK_ISSUER,
        options={"verify_exp": True},
        leeway=settings.KEYCLOAK_LEEWAY
      )
      return payload

    except jwt.ExpiredSignatureError as e:
      logger.error(f"❌ Token has expired: {e}")
      raise exceptions.AuthenticationFailed("Token has expired.")
    except jwt.InvalidIssuerError as e:
      logger.error(f"❌ Invalid token issuer: {e}")
      logger.error(f"Expected issuer: {settings.KEYCLOAK_ISSUER}")
      raise exceptions.AuthenticationFailed("Invalid token issuer.")
    except jwt.InvalidAudienceError as e:
      logger.error(f"❌ Invalid token audience: {e}")
      logger.error(f"Expected audience: {settings.KEYCLOAK_CLIENT_ID}")
      raise exceptions.AuthenticationFailed("Invalid token audience.")
    except jwt.exceptions.InvalidTokenError as e:
      logger.error(f"❌ JWT decode failed: {e}")
      raise exceptions.AuthenticationFailed(f"Token validation error: {e}")

  def _extract_user_type(self, payload: dict) -> str:
    """
    Extract user type from keycloak roles.
    Checks both realm_access and resource_access roles.
    Maps: 'admin', 'teacher', 'parent', 'student' roles to user_type.
    Priority: admin > teacher > parent > student
    """
    # Check realm roles
    realm_roles = payload.get("realm_access", {}).get("roles", [])

    # Check client roles
    resource_access = payload.get('resource_access', {})
    client_roles = []
    for client, access in resource_access.items():
      client_roles.extend(access.get('roles', []))

    # Combine all roles
    all_roles = set(realm_roles + client_roles)

    logger.debug(f"User roles from token: {all_roles}")

    # Priority-based role mapping
    if 'admin' in all_roles:
      return 'admin'
    elif 'teacher' in all_roles:
      return 'teacher'
    elif 'parent' in all_roles:
      return 'parent'
    elif 'student' in all_roles:
      return 'student'

    # Default to student if no recognized role
    logger.warning(f"No recognized role found in keycloak token. Defaulting to 'student'. Roles: {all_roles}")
    return 'student'

  def _get_or_create_user(
    self,
    keycloak_id: str,
    username: str,
    email: str,
    first_name: str,
    last_name: str,
    name: str,
    user_type: str,
    payload: dict
  ) -> User:
    """
    Get or create Django user from Keycloak token data.
    Updates user information if it has changed.
    """
    # Try to find existing user by keycloak_id
    try:
      if keycloak_id:
        user = User.objects.get(keycloak_id=keycloak_id)
        logger.debug(f"Found existing user: {user.username}")

        # Update user info if changed
        updated = False
        fields_to_update = {
          'email': email,
          'first_name': first_name,
          'last_name': last_name,
          'name': name,
          'user_type': user_type,
        }

        for field, value in fields_to_update.items():
          if value and getattr(user, field) != value:
            setattr(user, field, value)
            updated = True

        if updated:
          user.save()
          logger.info(f"Updated user info for: {user.username}")

        return user

    except User.DoesNotExist:
      pass

    # Create new user
    try:
      user = User.objects.create(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        name=name,
        keycloak_id=keycloak_id,
        user_type=user_type,
        is_active=True
      )
      logger.info(f"✨ Created new Django user: {user.username} (type: {user_type}) from Keycloak")
      return user

    except Exception as e:
      logger.error(f"❌ Failed to create user with username '{username}': {e}")

      # If username already exists, create with unique username
      import uuid
      unique_username = f"{username}_{uuid.uuid4().hex[:8]}"
      user = User.objects.create(
        username=unique_username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        name=name,
        keycloak_id=keycloak_id,
        user_type=user_type,
        is_active=True
      )
      logger.info(f"✨ Created Django user with unique username: {user.username} (type: {user_type})")
      return user

  def authenticate_header(self, request) -> str:
    """
    Return a string to be used as the value of the `WWW-Authenticate`
    header in a `401 Unauthenticated` response.
    """
    return f'Bearer realm="{self.www_authenticate_realm}"'
