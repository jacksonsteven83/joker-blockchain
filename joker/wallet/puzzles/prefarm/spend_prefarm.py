import asyncio

from blspy import G2Element
from clvm_tools import binutils

from joker.consensus.block_rewards import calculate_base_farmer_reward, calculate_pool_reward, \
    calculate_base_community_reward
from joker.rpc.full_node_rpc_client import FullNodeRpcClient
from joker.types.blockchain_format.program import Program
from joker.types.coin_spend import CoinSpend
from joker.types.condition_opcodes import ConditionOpcode
from joker.types.spend_bundle import SpendBundle
from joker.util.bech32m import decode_puzzle_hash
from joker.util.condition_tools import parse_sexp_to_conditions
from joker.util.config import load_config
from joker.util.default_root import DEFAULT_ROOT_PATH
from joker.util.ints import uint32, uint16


def print_conditions(spend_bundle: SpendBundle):
    print("\nConditions:")
    for coin_spend in spend_bundle.coin_spends:
        result = Program.from_bytes(bytes(coin_spend.puzzle_reveal)).run(Program.from_bytes(bytes(coin_spend.solution)))
        error, result_human = parse_sexp_to_conditions(result)
        assert error is None
        assert result_human is not None
        for cvp in result_human:
            print(f"{ConditionOpcode(cvp.opcode).name}: {[var.hex() for var in cvp.vars]}")
    print("")


async def main() -> None:
    rpc_port: uint16 = uint16(18555)
    self_hostname = "localhost"
    path = DEFAULT_ROOT_PATH
    config = load_config(path, "config.yaml")
    client = await FullNodeRpcClient.create(self_hostname, rpc_port, path, config)
    try:
        community_prefarm = (await client.get_block_record_by_height(1)).reward_claims_incorporated[2]
        farmer_prefarm = (await client.get_block_record_by_height(1)).reward_claims_incorporated[1]
        pool_prefarm = (await client.get_block_record_by_height(1)).reward_claims_incorporated[0]

        pool_amounts = int(calculate_pool_reward(uint32(0)) / 2)
        farmer_amounts = int(calculate_base_farmer_reward(uint32(0)) / 2)
        community_amounts = int(calculate_base_community_reward(uint32(0)) / 2)
        print(farmer_prefarm.amount, farmer_amounts)
        assert farmer_amounts == farmer_prefarm.amount // 2
        assert pool_amounts == pool_prefarm.amount // 2
        assert community_amounts == community_prefarm.amount // 2
        address1 = "xjk1rdatypul5c642jkeh4yp933zu3hw8vv8tfup8ta6zfampnyhjnusxdgns6"  # Key 1
        address2 = "xjk1duvy5ur5eyj7lp5geetfg84cj2d7xgpxt7pya3lr2y6ke3696w9qvda66e"  # Key 2
        address3 = "xjk1duvy5ur5eyj7lp5geetfg84cj2d7xgpxt7pya3lr2y6ke3696w9qvda66e"  # Key 3

        ph1 = decode_puzzle_hash(address1)
        ph2 = decode_puzzle_hash(address2)
        ph3 = decode_puzzle_hash(address3)

        p_community_2 = Program.to(
            binutils.assemble(f"(q . ((51 0x{ph1.hex()} {community_amounts}) (51 0x{ph2.hex()} {community_amounts})))")
        )
        p_farmer_2 = Program.to(
            binutils.assemble(f"(q . ((51 0x{ph1.hex()} {farmer_amounts}) (51 0x{ph2.hex()} {farmer_amounts})))")
        )
        p_pool_2 = Program.to(
            binutils.assemble(f"(q . ((51 0x{ph1.hex()} {pool_amounts}) (51 0x{ph2.hex()} {pool_amounts})))")
        )

        p_solution = Program.to(binutils.assemble("()"))

        sb_farmer = SpendBundle([CoinSpend(farmer_prefarm, p_farmer_2, p_solution)], G2Element())
        sb_pool = SpendBundle([CoinSpend(pool_prefarm, p_pool_2, p_solution)], G2Element())
        sb_community = SpendBundle([CoinSpend(community_prefarm, p_community_2, p_solution)], G2Element())

        print("\n\n\nConditions")
        print_conditions(sb_pool)
        print("\n\n\n")
        print("Farmer to spend")
        print(sb_pool)
        print(sb_farmer)
        print(sb_community)
        print("\n\n\n")
        res = await client.push_tx(sb_farmer)
        # res = await client.push_tx(sb_pool)

        print(res)
        up = await client.get_coin_records_by_puzzle_hash(farmer_prefarm.puzzle_hash, True)
        uf = await client.get_coin_records_by_puzzle_hash(pool_prefarm.puzzle_hash, True)
        uc = await client.get_coin_records_by_puzzle_hash(community_prefarm.puzzle_hash, True)
        print(up)
        print(uf)
        print(uc)
    finally:
        client.close()


asyncio.run(main())
