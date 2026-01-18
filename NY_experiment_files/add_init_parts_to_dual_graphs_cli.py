import click
from add_init_parts_to_dual_graphs import add_init_parts

@click.command()
@click.option(
    "--block-type",
    prompt="Which dual graph to add init parts to",
    help="",
    type=click.Choice(["blockgroups", "vtds", "tracts"]),
)

def main(
    block_type
):
    add_init_parts(block_type)

if __name__ == "__main__":
    main()