#!/usr/bin/env python3

import click
import os
from bunch import Bunch
from typing import List

import lib.iof as iof
from lib.config import Config
from lib.metrics import distances
from lib.index import Index
from tools import format_check as fc


pass_config = click.make_pass_decorator(Config, ensure=True)


def _index_check(config: Config):
    if "current_index" not in config:
        raise ValueError("There is no index created. Run 'mgns init' \
                         or 'mgns use' first")


def _build_check(config: Config):
    if not config.built:
        raise ValueError("First you have to build the index. Run \
                         'mgns build'")


@click.group()
@click.option('--workon', default='./.mgns/')
@click.option('--force', '-f', is_flag=True,
              help='Force overwrite output directory')
@click.option('--quiet', '-q', is_flag=True, help='Be quiet')
@click.option('--njobs', '-n', type=int, default=1,
              help='Number of jobs to start in parallel')
@pass_config
def cli(config: Config, workon: str, force: bool,
        quiet: bool, njobs: int):
    config.load(workon)
    config.temp.force = force
    config.temp.quiet = quiet
    config.temp.njobs = njobs


@cli.command()
@click.argument('name', type=str, required=True)
@pass_config
def init(config: Config, name: str):
    index_path = os.path.join(config.workon, name)
    iof.make_sure_exists(index_path)
    config.current_index = name

    config.built = "false"
    config.save()


@cli.command()
@click.argument('input_files', type=click.Path(exists=True), nargs=-1,
                required=True)
@click.option('--kmer_size', '-k', type=int, help='K-mer size',
              default=50)
@click.option('--distance', '-d', type=click.Choice(distances.keys()),
              default='jsd', help='A distance metric')
@click.option('--coord_system_size', '-c', type=int,
              help='Coordinate system size', required=True)
@click.option('--generations', '-n', type=int, help='Number of generations',
              default=1000)
@click.option('--mutation_rate', '-m', type=float, help='Mutation rate',
              default=0.1)
@click.option('--population_size', '-p', type=int, help='Population size',
              default=100)
@click.option('--select_rate', '-s', type=float,
              help='Fraction of best individuals to select on each generation',
              default=0.25)
@click.option('--random_select_rate', '-r', type=float,
              help='Fraction of random individuals to select \
              on each generation', default=0.1)
@click.option('--legend_size', '-l', type=int,
              help='Count of best individuals to keep tracking', default=15)
@click.option('--idle_threshold', '-i', type=int,
              help='Number of iterations to \
              continue the evolution at local minimum', default=5)
@pass_config
def build(config: Config, kmer_size: int, distance: str,
          input_files: List[str], coord_system_size: int,
          generations: int, mutation_rate: float, population_size: int,
          select_rate: float, random_select_rate: float,
          legend_size: int, idle_threshold: int):

    _index_check(config)

    config.dist = Bunch()
    config.dist.func = distance
    config.dist.kmer_size = kmer_size

    config.genetic = Bunch()
    config.genetic.coord_system_size = coord_system_size
    config.genetic.generations = generations
    config.genetic.mutation_rate = mutation_rate
    config.genetic.population_size = population_size
    config.genetic.select_rate = select_rate
    config.genetic.random_select_rate = random_select_rate
    config.genetic.legend_size = legend_size
    config.genetic.idle_threshold = idle_threshold

    config.jellyfish = Bunch()
    config.jellyfish.tables_count = 10
    config.jellyfish.hash_size = "100M"

    input_files = fc.format_check(input_files)
    index = Index.build(config, input_files)
    index.save()

    config.built = "true"
    config.save()


@cli.command()
@click.option('--kmer_size', '-k', type=int, help='K-mer size',
              default=50)
@click.option('--distance', '-d', type=click.Choice(distances.keys()),
              default='jsd', help='A distance metric')
@click.option('--coord_system_size', '-c', type=int,
              help='Coordinate system size', required=True)
@click.option('--generations', '-n', type=int, help='Number of generations',
              default=1000)
@click.option('--mutation_rate', '-m', type=float, help='Mutation rate',
              default=0.1)
@click.option('--population_size', '-p', type=int, help='Population size',
              default=100)
@click.option('--select_rate', '-s', type=float,
              help='Fraction of best individuals to select on each generation',
              default=0.25)
@click.option('--random_select_rate', '-r', type=float,
              help='Fraction of random individuals to select \
              on each generation', default=0.1)
@click.option('--legend_size', '-l', type=int,
              help='Count of best individuals to keep tracking', default=15)
@click.option('--idle_threshold', '-i', type=int,
              help='Number of iterations to \
              continue the evolution at local minimum', default=5)
@pass_config
def refine(config: Config, kmer_size: int, distance: str,
           coord_system_size: int, generations: int,
           mutation_rate: float, population_size: int,
           select_rate: float, random_select_rate: float,
           legend_size: int, idle_threshold: int):

    _index_check(config)

    config.dist = Bunch()
    config.dist.func = distance
    config.dist.kmer_size = kmer_size

    config.genetic = Bunch()
    config.genetic.coord_system_size = coord_system_size
    config.genetic.generations = generations
    config.genetic.mutation_rate = mutation_rate
    config.genetic.population_size = population_size
    config.genetic.select_rate = select_rate
    config.genetic.random_select_rate = random_select_rate
    config.genetic.legend_size = legend_size
    config.genetic.idle_threshold = idle_threshold

    config.jellyfish = Bunch()
    config.jellyfish.tables_count = 10
    config.jellyfish.hash_size = "100M"

    index = Index.load(config)
    index.refine()
    index.save()

    config.built = "true"
    config.save()


@cli.command()
@click.argument('input_files', type=click.Path(exists=True), nargs=-1,
                required=True)
@pass_config
def add(config: Config, input_files: List[str]):
    _index_check(config)

    index = Index.load(config)
    index.add(input_files)
    index.save()


@cli.command()
@click.argument('name', type=str, required=True)
@pass_config
def use(config: Config, name: str):
    index_path = os.path.join(config.workon, name)
    if not iof.exists(index_path):
        print('No such index:', name)

    config.current_index = name
    config.save()


@cli.command()
@pass_config
def stats(config: Config):
    _index_check(config)

    index = Index.load(config)
    indexed = len(index.sample_map)
    coord_system_size = len(index.coord_system.keys())

    print("Current index:", config.current_index)
    print("Indexed:", indexed, "samples")
    print("Coordinate system size:", coord_system_size)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True),
                required=True)
@click.option('-k', type=int, required=True,
              help='Count of nearest neighbors')
@pass_config
def find(config: Config, input_file: str, k: int):
    _index_check(config)
    _build_check(config)

    index = Index.load(config)
    _, points = index.find(input_file, k)
    print(k, "nearest neighbors:",
          ', '.join(sample.name for sample in points))
