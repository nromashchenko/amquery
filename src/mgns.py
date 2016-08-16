#!/usr/bin/env python3

import click
import os
from bunch import Bunch
from typing import List

import distance as mdist
import lib.prebuild as pre
import lib.iof as iof
from lib.config import Config
from lib.metrics import distances
from lib.dist import SampleMap
from lib.pwcomp import PwMatrix
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
@click.option('--kmer_size', '-k', type=int, help='K-mer size',
              default=50, required=True)
@click.option('--distance', '-d', type=click.Choice(distances.keys()),
              default='jsd', help='A distance metric')
@pass_config
def init(config: Config, name: str, kmer_size: int, distance: str):
    index_path = os.path.join(config.workon, name)
    iof.make_sure_exists(index_path)
    config.current_index = name

    config.dist = Bunch()
    config.dist.func = distance
    config.dist.kmer_size = kmer_size

    config.built = "false"
    config.save()


@cli.command()
@click.argument('input_files', type=click.Path(exists=True), nargs=-1,
                required=True)
@pass_config
def add(config: Config, input_files: List[str]):
    _index_check(config)

    if not hasattr(config, "index"):
        config.index = Bunch()
        config.index.sample_map_file = "sample_map.p"
        config.save()

    mdist.add(config, input_files)


@cli.command()
@click.option('--coord_system_size', '-k', type=int, help='Coord system size',
              required=True)
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
def build(config: Config, coord_system_size: int, generations: int,
          mutation_rate: float, population_size: int,
          select_rate: float, random_select_rate: float,
          legend_size: int, idle_threshold: int):

    config.genetic = Bunch()
    config.genetic.coord_system_size = coord_system_size
    config.genetic.generations = generations
    config.genetic.mutation_rate = mutation_rate
    config.genetic.population_size = population_size
    config.genetic.select_rate = select_rate
    config.genetic.random_select_rate = random_select_rate
    config.genetic.legend_size = legend_size
    config.genetic.idle_threshold = idle_threshold
    config.save()

    index = Index.build(config)
    config.built = "true"


@cli.command()
@pass_config
def append(config: Config, input_files: List[str]):
    _index_check(config)
    _build_check(config)
    mdist.append(config, input_files)


@cli.command()
@click.argument('input_dirs', type=click.Path(exists=True), nargs=-1,
                required=True)
@click.option('--single-file', '-f', is_flag=True,
              help='A single file containing reads for all samples')
@click.option('--max-samples', '-n', type=int,
              help='Max count of samples to analyze')
@click.option('--min', type=int, default=109,
              help='Minimum read length')
@click.option('--cut', type=int, default=208)
@click.option('--threshold', type=int, default=5000,
              help='Required read count per sample')
@pass_config
def filter(config, input_dirs, single_file, max_samples,
           min, cut, threshold):
    if config.temp.force:
        iof.clear_dir(config.workon)

    filtered_dirs = pre.filter_reads(config, input_dirs,
                                     min, None, cut, threshold)

    if max_samples:
        if single_file:
            raise NotImplementedError(
                "--single-file is not implemented yet")
        else:
            pre.rarefy(config, filtered_dirs, max_samples)


@cli.command()
@click.argument('name', type=str, required=True)
@pass_config
def use(config: Config, name: str):
    index_path = os.path.join(config.workon, name)
    if not iof.exists(index_path):
        print('No such index:', name)

    config.current_index = name
    config.save()



if __name__ == "__main__":
    pass
