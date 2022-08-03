import asyncio
import logging
from typing import Tuple

import aiohttp
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization

from joker.protocols.shared_protocol import protocol_version
from joker.server.outbound_message import NodeType
from joker.server.server import JokerServer, ssl_context_for_client
from joker.server.ws_connection import WSJokerConnection
from joker.ssl.create_ssl import generate_ca_signed_cert
from joker.types.blockchain_format.sized_bytes import bytes32
from joker.types.peer_info import PeerInfo
from joker.util.ints import uint16
from tests.time_out_assert import time_out_assert

log = logging.getLogger(__name__)


async def disconnect_all(server: JokerServer) -> None:
    cons = list(server.all_connections.values())[:]
    for con in cons:
        await con.close()


async def disconnect_all_and_reconnect(server: JokerServer, reconnect_to: JokerServer, self_hostname: str) -> bool:
    await disconnect_all(server)
    return await server.start_client(PeerInfo(self_hostname, uint16(reconnect_to._port)), None)


async def add_dummy_connection(
    server: JokerServer, self_hostname: str, dummy_port: int, type: NodeType = NodeType.FULL_NODE
) -> Tuple[asyncio.Queue, bytes32]:
    timeout = aiohttp.ClientTimeout(total=10)
    session = aiohttp.ClientSession(timeout=timeout)
    incoming_queue: asyncio.Queue = asyncio.Queue()
    dummy_crt_path = server._private_key_path.parent / "dummy.crt"
    dummy_key_path = server._private_key_path.parent / "dummy.key"
    generate_ca_signed_cert(
        server.joker_ca_crt_path.read_bytes(), server.joker_ca_key_path.read_bytes(), dummy_crt_path, dummy_key_path
    )
    ssl_context = ssl_context_for_client(
        server.joker_ca_crt_path, server.joker_ca_key_path, dummy_crt_path, dummy_key_path
    )
    pem_cert = x509.load_pem_x509_certificate(dummy_crt_path.read_bytes(), default_backend())
    der_cert = x509.load_der_x509_certificate(pem_cert.public_bytes(serialization.Encoding.DER), default_backend())
    peer_id = bytes32(der_cert.fingerprint(hashes.SHA256()))
    url = f"wss://{self_hostname}:{server._port}/ws"
    ws = await session.ws_connect(url, autoclose=True, autoping=True, ssl=ssl_context)
    wsc = WSJokerConnection(
        type,
        ws,
        server._port,
        log,
        True,
        False,
        self_hostname,
        incoming_queue,
        lambda x, y: x,
        peer_id,
        100,
        30,
    )
    await wsc.perform_handshake(server._network_id, protocol_version, dummy_port, NodeType.FULL_NODE)
    return incoming_queue, peer_id


async def connect_and_get_peer(server_1: JokerServer, server_2: JokerServer, self_hostname: str) -> WSJokerConnection:
    """
    Connect server_2 to server_1, and get return the connection in server_1.
    """
    await server_2.start_client(PeerInfo(self_hostname, uint16(server_1._port)))

    async def connected():
        for node_id_c, _ in server_1.all_connections.items():
            if node_id_c == server_2.node_id:
                return True
        return False

    await time_out_assert(10, connected, True)
    for node_id, wsc in server_1.all_connections.items():
        if node_id == server_2.node_id:
            return wsc
    assert False
