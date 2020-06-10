"""RedBrick Client."""

from typing import Optional, Any


class RedBrickClient:
    """Interface to RedBrick platform."""

    class __RedBrickClient:
        """A private singleton for redbrick."""

        def __init__(self, api_key: str) -> None:
            """Construct RedBrick client singleton."""
            self.api_key = api_key

        def __str__(self) -> str:
            """Get string representation."""
            return repr(self) + "***" + self.api_key[-4:-1]

    instance: Optional[__RedBrickClient] = None

    def __init__(self, api_key: Optional[str] = None,) -> None:
        """Construct instance of RedBrickClient."""
        if not api_key:
            if not RedBrickClient.instance:
                raise Exception("Must specify api_key and org_id")
            return
        if not RedBrickClient.instance:
            RedBrickClient.instance = RedBrickClient.__RedBrickClient(api_key)
        else:
            RedBrickClient.instance.api_key = api_key

    def __getattr__(self, name: str) -> Any:
        """Get specified attribute from object."""
        return getattr(self.instance, name)
