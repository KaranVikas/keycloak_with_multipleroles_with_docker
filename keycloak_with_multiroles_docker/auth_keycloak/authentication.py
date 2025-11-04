import logging
from django.conf import settings
from urllib.parse import splitvalue
from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework import exceptions
from django.contrib.auth import get_user_model
import jwt
from jwt import PyJWKClient

User = get_user_model()

logger = logging.getLogger(__name__)

class JWTAuthentication(BaseAuthentication):
  """
  DRF authentication class for JWT tokens
  - extract bearer token
  - validates sign with keycloak realm JWKS
  - enforces iss, aud, exp(with leeway)
  Returns (user ,token_payload) where user is a lightweight object
  """

  www_authenticate_realm = 'api'

  def authenticate(self, request):

    auth = get_authorization_header(request).split()

    if not auth or auth[0].lower() != b'bearer':
      return None

    if len(auth) == 1:
      raise exceptions.AuthenticationFailed('Invalid token header. No credentials provided.')
    elif len(auth) > 2:
      raise exceptions.AuthenticationFailed('Invalid token header. Token string should not contain spaces.')

    raw_token = auth[1].decode('utf-8')

    jwk_client = PyJWKClient(settings.KEYCLOAK_REALM_JWKS_URL)

    try:
      signing_key = jwk_client.get_signing_key_from_jwt(raw_token)
    except jwt.exceptions.InvalidTokenError as e:
      raise exceptions.AuthenticationFailed(f"Unable to obtain signing key: {e}")

    try:
      payload = jwt.decode(
        raw_token,
        signing_key.key,
        algorithms=['RS256'],
        audience=settings.KEYCLOAK_CLIENT_ID,
        issuer=settings.KEYCLOAK_REALM_URL,
        options={"verify_exp": True}
      )

    except jwt.ExpiredSignatureError as e:
      logger.error(f"❌ Token has expired: {e}")
      raise exceptions.AuthenticationFailed("Token has expired.")
    except jwt.InvalidIssuerError as e:
      logger.error(f"❌ Invalid token issuer: {e}")
      logger.error(f"Expected issuer: {settings.KEYCLOAK_ISSUER}")
      raise exceptions.AuthenticationFailed("Invalid token issuer.")
    except jwt.InvalidAudienceError as e:
      logger.error(f"❌ Invalid token audience: {e}")
      logger.error(f"Expected audience: {settings.KEYCLOAK_AUDIENCE}")
      raise exceptions.AuthenticationFailed("Invalid token audience.")
    except Exception as e:
      logger.error(f"❌ JWT decode failed with error: {e}")
      logger.error(f"Error type: {type(e)}")
      raise exceptions.AuthenticationFailed(f"Token validation error: {e}")


    keycloak_id = payload.get("sub")
    username = payload.get("username") or payload.get("email") or keycloak_id
    email = payload.get("email", "")
    name = payload.get("name", "")


    # Extract roles from keycloak token
    user_type = self.extract_user_type(payload)

    django_user = self.get_or_create_user(keycloak_id, username, email, name,user_type, payload)

    logger.info(f"✅ Authentication successful for user: {django_user.username} (ID: {django_user.id})")
    return (django_user, payload)

  def extract_user_type(self, payload: dict) -> str:
    """
      Extract user type from keycloak roles.
      Check both realm_access and resource_access roles.
      Maps: 'student' , 'parent' , 'admin' roles to user_type.
    """

    #   Check realm roles
    realm_roles = payload.get("realm_access", {}).get("roles", [])

    # Check client roles
    resource_access = payload.get('resource_access', {})
    client_roles = []
    for client, access in resource_access.items():
      client_roles.extend(access.get('roles', []))

    all_roles = realm_roles + client_roles

  #   Priority roles : admin > parent > student
    if 'admin' in all_roles:
      return 'admin'
    elif 'teacher' in all_roles or 'parent' in all_roles:
      return 'teacher'
    elif 'student' in all_roles:
      return 'student'

    #   Default to student if no recognised role
    logger.warning(f"No recognised role found in keycloak token. Defaulting to 'student' role.")
    return 'student'

  def get_or_create_user(self, keycloak_id:str, username:str, email:str, name:str,user_type:str,  payload:dict):
    """ Get or create Django user from keycloak user"""
    try:
#     try to find the user by keycloak ID first
      if keycloak_id:
        user = User.objects.get(keycloak_id=keycloak_id)
        logger.info(f"found existing user: {user.username}")

#         update user info if changed
        updated = False
        if user.email != email and email:
          user.email = email
          updated = True
        if user.name != name and name:
          user.name = name
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
        username = username,
        email = email,
        name = name,
        keycloak_id = keycloak_id,
        user_type = user_type,
        is_active = True
      )
      logger.info(f"Created new Django user: {user.username} from keycloak user")
      return user
    except Exception as e:
      logger.error(f"Failed to create user: {e}")

#     if username is already exists with different case or special characters.
      import uuid
      unique_username = f"{username}_{uuid.uuid4().hex[:8]}"
      user = User.objects.create(
        username = unique_username,
        email = email,
        name = name,
        keycloak_id = keycloak_id,
        user_type=user_type,
        is_active = True
      )
      logger.info(f"Created new Django user: {user.username} from keycloak user")
      return user

  def authenticate_header(self, request) -> str:
    return f'Bearer realm="{self.www_authenticate_realm}"'


#



