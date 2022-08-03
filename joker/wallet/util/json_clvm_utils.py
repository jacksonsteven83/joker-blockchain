from typing import Any

from joker.types.blockchain_format.program import Program


def json_to_jokerlisp(json_data: Any) -> Any:
    list_for_jokerlisp = []
    if isinstance(json_data, list):
        for value in json_data:
            list_for_jokerlisp.append(json_to_jokerlisp(value))
    else:
        if isinstance(json_data, dict):
            for key, value in json_data:
                list_for_jokerlisp.append((key, json_to_jokerlisp(value)))
        else:
            list_for_jokerlisp = json_data
    return Program.to(list_for_jokerlisp)
