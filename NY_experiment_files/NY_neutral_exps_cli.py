import click
from NY_neutral_exps import NY_neutral_exp

@click.command()
@click.option(
    "--block-type",
    prompt="Block type (blockgroups, vtds, or tracts)",
    help="",
    type=click.Choice(["blockgroups", "vtds", "tracts"]),
)
@click.option(
    "--init-part",
    prompt="Number for initial partition (1–5)",
    help="",
    type=int
)
@click.option(
    "--random-seed",
    prompt="Random seed",
    help="Integer to set random seed",
    type=int
)
@click.option(
    "--total-steps",
    prompt="Step count (must be divisible by 20)",
    help="Number of districting plans per building block graph",
    type=int
)

def main(
    block_type, init_part, random_seed, total_steps
):
    NY_neutral_exp(block_type, init_part, random_seed, total_steps)


if __name__ == "__main__":
    main()