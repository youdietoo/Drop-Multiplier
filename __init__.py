import unrealsdk

from collections import deque
from typing import Any

from mods_base import SliderOption, build_mod, hook
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct


pending = deque()

multiplier_slider = SliderOption(
    identifier="Drop Multiplier",
    value=1,
    min_value=1,
    max_value=100,
    description="Extra loot rolls.",
)


async_processing_slider = SliderOption(
    identifier="Async Drop Processing",
    value=3,
    min_value=1,
    max_value=5,
    description="How many enemy drops are processed per tick.",
)



@hook("WillowGame.WillowPawn:DropLootOnDeath")
def add_or_remove_drop_job(obj: UObject, args: WrappedStruct, _ret: Any, _func: BoundFunction) -> None:
    for job in pending:
        if job[0] == obj:
            if job[4] <= 0:
                try:
                    pending.remove(job)
                except ValueError:
                    pass
                return

            return

    pending.append([obj, args.Killer, args.DamageType, args.DamageTypeDefinition, int(multiplier_slider.value)])


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
        
        try:
            pawn.DropLootOnDeath(
                job[1],
                job[2],
                job[3]
            )
        except Exception as e:
            print("DropLootOnDeath error:", repr(e))

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
    pending.clear()


mod = build_mod(
    options=[multiplier_slider, async_processing_slider],
    on_disable=on_disable
)
