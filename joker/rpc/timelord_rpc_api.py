from typing import Any, Callable, Dict, List, Optional

from joker.timelord.timelord import Timelord
from joker.util.ws_message import WsRpcMessage, create_payload_dict


class TimelordRpcApi:
    def __init__(self, timelord: Timelord):
        self.service = timelord
        self.service_name = "joker_timelord"

    def get_routes(self) -> Dict[str, Callable]:
        return {}

    async def _state_changed(self, change: str, change_data: Optional[Dict[str, Any]] = None) -> List[WsRpcMessage]:
        payloads = []

        if change_data is None:
            change_data = {}

        if change in ("finished_pot", "new_compact_proof", "skipping_peak", "new_peak"):
            payloads.append(create_payload_dict(change, change_data, self.service_name, "metrics"))

        return payloads
