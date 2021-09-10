"""All constants for Music Assistant."""

__version__ = "0.2.12"
REQUIRED_PYTHON_VER = "3.8"

# configuration keys/attributes
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_ENABLED = "enabled"
CONF_HOSTNAME = "hostname"
CONF_PORT = "port"
CONF_TOKEN = "token"
CONF_URL = "url"
CONF_NAME = "name"
CONF_CROSSFADE_DURATION = "crossfade_duration"
CONF_GROUP_DELAY = "group_delay"
CONF_VOLUME_CONTROL = "volume_control"
CONF_POWER_CONTROL = "power_control"
CONF_MAX_SAMPLE_RATE = "max_sample_rate"
CONF_VOLUME_NORMALISATION = "volume_normalisation"
CONF_TARGET_VOLUME = "target_volume"
CONF_SSL_CERTIFICATE = "ssl_certificate"
CONF_SSL_KEY = "ssl_key"
CONF_EXTERNAL_URL = "external_url"


# configuration base keys/attributes
CONF_KEY_BASE = "base"
CONF_KEY_PLAYER_SETTINGS = "player_settings"
CONF_KEY_MUSIC_PROVIDERS = "music_providers"
CONF_KEY_PLAYER_PROVIDERS = "player_providers"
CONF_KEY_METADATA_PROVIDERS = "metadata_providers"
CONF_KEY_PLUGINS = "plugins"
CONF_KEY_SECURITY = "security"
CONF_KEY_SECURITY_LOGIN = "login"
CONF_KEY_SECURITY_APP_TOKENS = "app_tokens"
CONF_KEY_BASE_INFO = "info"

# events
EVENT_PLAYER_ADDED = "player added"
EVENT_PLAYER_REMOVED = "player removed"
EVENT_PLAYER_CHANGED = "player changed"
EVENT_STREAM_STARTED = "streaming started"
EVENT_STREAM_ENDED = "streaming ended"
EVENT_CONFIG_CHANGED = "config changed"
EVENT_MUSIC_SYNC_STATUS = "music sync status"
EVENT_QUEUE_UPDATED = "queue updated"
EVENT_QUEUE_ITEMS_UPDATED = "queue items updated"
EVENT_SHUTDOWN = "application shutdown"
EVENT_PROVIDER_REGISTERED = "provider registered"
EVENT_PROVIDER_UNREGISTERED = "provider unregistered"
EVENT_ARTIST_ADDED = "artist added"
EVENT_ALBUM_ADDED = "album added"
EVENT_TRACK_ADDED = "track added"
EVENT_PLAYLIST_ADDED = "playlist added"
EVENT_RADIO_ADDED = "radio added"
EVENT_TASK_UPDATED = "task updated"

# player attributes
ATTR_PLAYER_ID = "player_id"
ATTR_PROVIDER_ID = "provider_id"
ATTR_NAME = "name"
ATTR_POWERED = "powered"
ATTR_ELAPSED_TIME = "elapsed_time"
ATTR_STATE = "state"
ATTR_AVAILABLE = "available"
ATTR_CURRENT_URI = "current_uri"
ATTR_VOLUME_LEVEL = "volume_level"
ATTR_MUTED = "muted"
ATTR_IS_GROUP_PLAYER = "is_group_player"
ATTR_GROUP_CHILDS = "group_childs"
ATTR_DEVICE_INFO = "device_info"
ATTR_SHOULD_POLL = "should_poll"
ATTR_FEATURES = "features"
ATTR_CONFIG_ENTRIES = "config_entries"
ATTR_UPDATED_AT = "updated_at"
ATTR_ACTIVE_QUEUE = "active_queue"
ATTR_GROUP_PARENTS = "group_parents"
