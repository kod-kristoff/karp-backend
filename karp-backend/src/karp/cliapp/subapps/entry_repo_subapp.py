import json  # noqa: D100, I001

from tabulate import tabulate
import typer

from karp import lex
from karp.lex_core.value_objects import UniqueId  # noqa: F401
from karp.command_bus import CommandBus
from karp.lex_core.value_objects.unique_id import UniqueIdStr  # noqa: F401
from karp.lex.application.queries import ListEntryRepos
from karp.lex_core.commands import CreateEntryRepository
from karp.cliapp.typer_injector import inject_from_ctx


subapp = typer.Typer()


@subapp.command()
def create(infile: typer.FileBinaryRead, ctx: typer.Context):  # noqa: ANN201, D103
    try:
        data = json.load(infile)
    except Exception as err:  # noqa: BLE001
        typer.echo(f"Error reading file '{infile.name}': {str(err)}")
        raise typer.Exit(123) from err
    create_entry_repo = CreateEntryRepository.from_dict(
        data,
        user="local admin",
    )

    bus = inject_from_ctx(CommandBus, ctx)  # type: ignore [misc]

    bus.dispatch(create_entry_repo)

    print(
        f"Entry repository '{create_entry_repo.name}' with id '{create_entry_repo.id}' created."
    )


@subapp.command()
def list(ctx: typer.Context):  # noqa: ANN201, D103, A001
    query = inject_from_ctx(ListEntryRepos, ctx)  # type: ignore [misc]
    typer.echo(
        tabulate(
            [[entry_repo.name, entry_repo.entity_id] for entry_repo in query.query()],
            headers=["name", "id"],
        )
    )


@subapp.command()
def show(ctx: typer.Context, name: str):  # noqa: ANN201, D103
    repo = inject_from_ctx(lex.ReadOnlyEntryRepoRepository, ctx)  # type: ignore [misc]
    if entry_repo := repo.get_by_name(name):
        typer.echo(tabulate(((key, value) for key, value in entry_repo.dict().items())))
    else:
        typer.echo("No such entry-repo")
        raise typer.Exit(2)


def init_app(app: typer.Typer) -> None:  # noqa: D103
    app.add_typer(subapp, name="entry-repo")
