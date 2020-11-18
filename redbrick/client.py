"""RedBrick Client."""

from typing import Optional, Any


class RedBrickClient:
    """Interface to RedBrick platform."""

    class RedBrickClientPrivate:
        """A private singleton for redbrick."""

        def __init__(self, api_key: str, custom_url: Optional[str] = None) -> None:
            """Construct RedBrick client singleton."""
            self.api_key = api_key
            self.custom_url = custom_url

        def __str__(self) -> str:
            """Get string representation."""
            return repr(self) + "***" + self.api_key[-4:-1]

    instance: Optional[RedBrickClientPrivate] = None

    def __init__(
        self, api_key: Optional[str] = None, url: Optional[str] = None
    ) -> None:
        """Construct instance of RedBrickClient."""
        if not api_key:
            if not RedBrickClient.instance:
                raise Exception("Must specify api_key")
            return
        if not RedBrickClient.instance:
            RedBrickClient.instance = RedBrickClient.RedBrickClientPrivate(api_key, url)
        else:
            RedBrickClient.instance.api_key = api_key

    def __getattr__(self, name: str) -> Any:
        """Get specified attribute from object."""
        return getattr(self.instance, name)
