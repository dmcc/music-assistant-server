"""
Remote Access Controller for Music Assistant.

This controller manages WebRTC-based remote access to Music Assistant instances.
It connects to a signaling server and handles incoming WebRTC connections,
bridging them to the local WebSocket API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from music_assistant_models.config_entries import ConfigEntry
from music_assistant_models.enums import ConfigEntryType, EventType

from music_assistant.controllers.remote_access.gateway import WebRTCGateway, generate_remote_id
from music_assistant.helpers.api import api_command
from music_assistant.models.core_controller import CoreController

if TYPE_CHECKING:
    from music_assistant_models.config_entries import ConfigValueType, CoreConfig
    from music_assistant_models.event import MassEvent

    from music_assistant import MusicAssistant
    from music_assistant.providers.hass import HomeAssistantProvider

# Signaling server URL
SIGNALING_SERVER_URL = "wss://signaling.music-assistant.io/ws"

# Config keys
CONF_REMOTE_ID = "remote_id"
CONF_ENABLED = "enable_remote_access"


class RemoteAccessController(CoreController):
    """Core Controller for WebRTC-based remote access."""

    domain: str = "remote_access"

    def __init__(self, mass: MusicAssistant) -> None:
        """Initialize the remote access controller.

        :param mass: MusicAssistant instance.
        """
        super().__init__(mass)
        self.manifest.name = "Remote Access"
        self.manifest.description = (
            "WebRTC-based remote access for connecting to Music Assistant "
            "from outside your local network (requires Home Assistant Cloud subscription)"
        )
        self.manifest.icon = "cloud-lock"
        self.gateway: WebRTCGateway | None = None
        self._remote_id: str | None = None
        self._setup_done = False

    async def get_config_entries(
        self,
        action: str | None = None,
        values: dict[str, ConfigValueType] | None = None,
    ) -> tuple[ConfigEntry, ...]:
        """Return all Config Entries for this core module (if any)."""
        entries = []
        has_ha_cloud = await self._check_ha_cloud_status()

        # Info alert about HA Cloud requirement
        entries.append(
            ConfigEntry(
                key="remote_access_info",
                type=ConfigEntryType.ALERT,
                label="Remote Access requires an active Home Assistant Cloud subscription.",
                required=False,
                hidden=has_ha_cloud,
            )
        )

        entries.append(
            ConfigEntry(
                key=CONF_ENABLED,
                type=ConfigEntryType.BOOLEAN,
                default_value=False,
                label="Enable Remote Access",
                description="Enable WebRTC-based (encrypted), secure remote access to your "
                "Music Assistant instance via https://app.music-assistant.io "
                "or supported mobile apps. ",
                hidden=not has_ha_cloud,
            )
        )
        entries.append(
            ConfigEntry(
                key="remote_access_id_label",
                type=ConfigEntryType.LABEL,
                label=f"Remote Access ID: {self._remote_id}",
                hidden=self._remote_id is None or not has_ha_cloud,
                depends_on=CONF_ENABLED,
            )
        )

        entries.append(
            ConfigEntry(
                key=CONF_REMOTE_ID,
                type=ConfigEntryType.STRING,
                label="Remote ID",
                description="Unique identifier for WebRTC remote access. "
                "Generated automatically and should not be changed.",
                required=False,
                hidden=True,
            )
        )

        return tuple(entries)

    async def setup(self, config: CoreConfig) -> None:
        """Async initialize of module."""
        self.config = config
        self.logger.debug("RemoteAccessController.setup() called")

        # Get or generate Remote ID
        remote_id_value = self.config.get_value(CONF_REMOTE_ID)
        if not remote_id_value:
            # Generate new Remote ID and save it
            remote_id_value = generate_remote_id()
            self._remote_id = remote_id_value
            # Save the Remote ID to config
            self.mass.config.set_raw_core_config_value(self.domain, CONF_REMOTE_ID, remote_id_value)
            self.mass.config.save(immediate=True)
            self.logger.debug("Generated new Remote ID: %s", remote_id_value)

        # Register API commands immediately
        self._register_api_commands()

        # Subscribe to provider updates to check for Home Assistant Cloud
        self.mass.subscribe(self._on_providers_updated, EventType.PROVIDERS_UPDATED)

        # Try initial setup (providers might already be loaded)
        await self._try_enable_remote_access()

    async def close(self) -> None:
        """Cleanup on exit."""
        if self.gateway:
            await self.gateway.stop()
            self.gateway = None
            self.logger.debug("WebRTC Remote Access stopped")

    def _on_remote_id_ready(self, remote_id: str) -> None:
        """Handle Remote ID registration with signaling server.

        :param remote_id: The registered Remote ID.
        """
        self.logger.debug("Remote ID registered with signaling server: %s", remote_id)
        self._remote_id = remote_id

    def _on_providers_updated(self, event: MassEvent) -> None:
        """Handle providers updated event.

        :param event: The providers updated event.
        """
        if self._setup_done:
            # Already set up, no need to check again
            return
        # Try to enable remote access when providers are updated
        self.mass.create_task(self._try_enable_remote_access())

    async def _try_enable_remote_access(self) -> None:
        """Try to enable remote access if Home Assistant Cloud is available."""
        if self._setup_done:
            # Already set up
            return

        # Check if remote access is enabled in config
        if not self.config.get_value(CONF_ENABLED, True):
            return

        # Check if Home Assistant Cloud is available and active
        cloud_status = await self._check_ha_cloud_status()
        if not cloud_status:
            self.logger.debug("Home Assistant Cloud not available")
            return

        # Mark as done to prevent multiple attempts
        self._setup_done = True
        self.logger.info("Home Assistant Cloud subscription detected, enabling remote access")

        # Determine local WebSocket URL from webserver config
        base_url = self.mass.webserver.base_url
        local_ws_url = base_url.replace("http", "ws")
        if not local_ws_url.endswith("/"):
            local_ws_url += "/"
        local_ws_url += "ws"

        # Get ICE servers from HA Cloud if available
        ice_servers = await self._get_ha_cloud_ice_servers()

        # Initialize and start the WebRTC gateway
        self.gateway = WebRTCGateway(
            signaling_url=SIGNALING_SERVER_URL,
            local_ws_url=local_ws_url,
            remote_id=self._remote_id,
            on_remote_id_ready=self._on_remote_id_ready,
            ice_servers=ice_servers,
        )

        await self.gateway.start()
        self.logger.info("WebRTC Remote Access enabled - Remote ID: %s", self._remote_id)

    async def _check_ha_cloud_status(self) -> bool:
        """Check if Home Assistant Cloud subscription is active.

        :return: True if HA Cloud is logged in and has active subscription.
        """
        # Find the Home Assistant provider
        ha_provider = cast("HomeAssistantProvider | None", self.mass.get_provider("hass"))
        if not ha_provider:
            self.logger.debug("Home Assistant provider not found or not available")
            return False

        try:
            # Access the hass client from the provider
            hass_client = ha_provider.hass
            if not hass_client or not hass_client.connected:
                self.logger.debug("Home Assistant client not connected")
                return False

            # Call cloud/status command to check subscription
            result = await hass_client.send_command("cloud/status")

            # Check for logged_in and active_subscription
            logged_in = result.get("logged_in", False)
            active_subscription = result.get("active_subscription", False)

            if logged_in and active_subscription:
                self.logger.debug("Home Assistant Cloud subscription is active")
                return True

            self.logger.debug(
                "Home Assistant Cloud not active (logged_in=%s, active_subscription=%s)",
                logged_in,
                active_subscription,
            )
            return False

        except Exception:
            self.logger.exception("Error checking Home Assistant Cloud status")
            return False

    async def _get_ha_cloud_ice_servers(self) -> list[dict[str, str]] | None:
        """Get ICE servers from Home Assistant Cloud.

        :return: List of ICE server configurations or None if unavailable.
        """
        # Find the Home Assistant provider
        ha_provider = cast("HomeAssistantProvider | None", self.mass.get_provider("hass"))
        if not ha_provider:
            return None

        try:
            # Access the hass client from the provider
            if not hasattr(ha_provider, "hass"):
                return None
            hass_client = ha_provider.hass
            if not hass_client or not hass_client.connected:
                return None

            # Try to get ICE servers from HA Cloud
            # This might be available via a cloud API endpoint
            # For now, return None and use default STUN servers
            # TODO: Research if HA Cloud exposes ICE/TURN server endpoints
            self.logger.debug(
                "Using default STUN servers (HA Cloud ICE servers not yet implemented)"
            )
            return None

        except Exception:
            self.logger.exception("Error getting Home Assistant Cloud ICE servers")
            return None

    @property
    def is_enabled(self) -> bool:
        """Return whether WebRTC remote access is enabled."""
        return self.gateway is not None and self.gateway.is_running

    @property
    def is_connected(self) -> bool:
        """Return whether the gateway is connected to the signaling server."""
        return self.gateway is not None and self.gateway.is_connected

    @property
    def remote_id(self) -> str | None:
        """Return the current Remote ID."""
        return self._remote_id

    def _register_api_commands(self) -> None:
        """Register API commands for remote access."""

        @api_command("remote_access/info")
        def get_remote_access_info() -> dict[str, str | bool]:
            """Get remote access information.

            Returns information about the remote access configuration including
            whether it's enabled, connected status, and the Remote ID for connecting.
            """
            return {
                "enabled": self.is_enabled,
                "connected": self.is_connected,
                "remote_id": self._remote_id or "",
                "signaling_url": SIGNALING_SERVER_URL,
            }
