import unrealsdk
from collections import deque
from typing import Any
from mods_base import SliderOption, build_mod, hook
from unrealsdk.hooks import Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

pending = deque()

multiplier_slider = SliderOption(
    identifier="Drop Multiplier",
    value=1,
    min_value=1,
    max_value=100,
    step=1,
    is_integer=True,
    description="Extra loot rolls for player kills."
)


async_processing_slider = SliderOption(
    identifier="Async Drop Processing",
    value=3,
    min_value=1,
    max_value=5,
    step=1,
    is_integer=True,
    description="How many enemy drops are processed per tick."
)

@hook("WillowGame.WillowAIPawn:Died", Type.PRE)
def enemy_died(obj: UObject, args: WrappedStruct, _ret: Any, _func: BoundFunction) -> None:

    # lets not add the same pawn again while it's being processed
    for job in pending:
        if job[0] == obj:
            return

    killer = getattr(args, "Killer", None)

    if not killer:
        return

    multiplier = int(multiplier_slider.value)

    pending.append(
        [
            obj,
            killer,
            getattr(args, "DamageType", None),
            getattr(args, "DamageTypeDefinition", None),
            multiplier
        ]
    )


@hook("Engine.PlayerController:PlayerTick")
def player_tick(obj: UObject, args: WrappedStruct, _ret: Any, _func: BoundFunction) -> None:

    if not pending:
        return

    rolls_this_tick = int(async_processing_slider.value)

    for _ in range(rolls_this_tick):
        if not pending:
            break

        job = pending[0]

        pawn = job[0]
        killer = job[1]
        damage_type = job[2]
        damage_type_definition = job[3]

        try:
            pawn.DropLootOnDeath(
                killer,
                damage_type,
                damage_type_definition
            )

        except Exception as e:
            print(
                f"[DropMultiplier] DropLootOnDeath error: {e}"
            )

            pending.popleft()
            continue

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
    clear_pending()


mod = build_mod(
    options=[
        multiplier_slider,
        async_processing_slider
    ],
    on_disable=on_disable
)
