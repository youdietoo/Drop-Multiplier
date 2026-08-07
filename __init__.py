import unrealsdk
from mods_base import SliderOption, build_mod, hook
from unrealsdk.unreal import UObject, WrappedStruct, BoundFunction
from collections import deque

from typing import Any

pending = deque()

@SliderOption(
    identifier="Drop Multiplier",
    value=1,
    min_value=1,
    max_value=100,
    description="Extra loot rolls.",
)
def multiplier_slider(_opt: SliderOption, _new_value: float) -> None:
    pass


@SliderOption(
    identifier="Async Drop Processing",
    value=3,
    min_value=1,
    max_value=5,
    description="How many enemy drops are processed per tick.",
)
def async_processing_slider(_opt: SliderOption, _new_value: float) -> None:
    pass


@hook("WillowGame.WillowPawn:DropLootOnDeath")
def drop_loot(obj: UObject, args: WrappedStruct, _ret: Any, _func: BoundFunction) -> None:

    for job in pending:
        if job[0] == obj:
            if job[4] <= 0:
                unrealsdk.logging.info(f"Removed drop queue: {obj}")
                pending.remove(job)
                return

            return

    pending.append([
        obj,
        args.Killer,
        args.DamageType,
        args.DamageTypeDefinition,
        int(multiplier_slider.value),
    ])

    unrealsdk.logging.info(f"Added drop queue: {obj}")


@hook("Engine.PlayerController:PlayerTick")
def player_tick(obj: UObject, args: WrappedStruct, _ret: Any, _func: BoundFunction) -> None:

    if not pending:
        return

    rolls_this_tick = int(async_processing_slider.value)

    for _ in range(rolls_this_tick):
        if not pending:
            break

        job = pending[0]

        job[0].DropLootOnDeath(
            job[1],
            job[2],
            job[3],
        )

        job[4] -= 1

        if job[4] <= 0:
            pending.popleft()
        else:
            pending.rotate(-1)

def clear_pending() -> None:
    pending.clear()


@hook("Engine.GameEngine:LoadMap")
def on_load_map(obj: UObject, args: WrappedStruct, _ret: Any, _func: BoundFunction) -> None:
    clear_pending()


@hook("Engine.GameEngine:Exit")
def on_exit(obj: UObject, args: WrappedStruct, _ret: Any, _func: BoundFunction) -> None:
    clear_pending()

def on_disable() -> None:
    pending.clear()


mod = build_mod(
    options=[
        multiplier_slider,
        async_processing_slider,
    ],
    on_disable=on_disable,
)