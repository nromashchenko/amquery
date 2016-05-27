import abc
import operator as op
import random
from typing import Sequence, Callable, Union

import numpy as np


class BaseIndividual(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __eq__(self, other):
        """
        :type other: Individual
        :rtype: bool
        """
        pass

    @abc.abstractmethod
    def __ne__(self, other):
        """
        :type other: Individual
        :rtype: bool
        """
        pass

    @abc.abstractproperty
    def engine(self):
        pass

    @abc.abstractproperty
    def chromosome(self):
        pass

    @abc.abstractproperty
    def mutation_rate(self) -> float:
        pass

    @abc.abstractmethod
    def replicate(self) -> Sequence:
        pass

    @abc.abstractmethod
    def mate(self, other):
        """
        :return: the result of mating with other Individual object
        of the same type
        """
        pass


class Individual(BaseIndividual):
    """
    :type _l: int
    :type _engine: Sequence[Callable]
    :type _mutation_rate: float
    :type _chromosome: tuple
    """

    def __init__(self, mutation_rate, engine, l, starting_chr=None):
        # TODO add docs about starting_chromosome
        """
        :type mutation_rate: float
        :param mutation_rate: the binomial mutation success rate for each gene
        :type engine: Union[Sequence[Callable[Optional]], Callable[Optional]]
        :param engine: an engine is used to mutate individual's features.
                       It can be:
                       - A single callable object that takes one argument
                         (current value of a feature) and returns an new value.
                         It must handle `None` inputs if `starting_chromosome`
                         is `None`
                       - A sequence of such callable object, one per each
                         feature
                       Note: when `starting_chr` is `None` the first time
                       `engine` is used its callables get `None` as input,
                       which means they should return some starting value; this
                       detail may not be important for your implementation, (e.g.
                       if you don't have any special rules for starting values
                       and mutated values), but make sure the your callables
                       handle `None` inputs if you don't `starting_chr`
        :type l: Optional[int]
        :param l: the number of features, defaults to `None`. Can't be == 0.
                  - If `l` is set to `None`, it's true value is inferred from
                    `len(engine)`, hence a `ValueError` will be raised if
                    `engine` is not a sequence;
                  - If `l` is not `None` and `engine` is a sequence such that
                    `len(engines) != l`, a `ValueError` will be raised.
        :type starting_chr: Sequence
        :param starting_chr:
        """
        if l and isinstance(engine, Sequence) and len(engine) != l:
            raise ValueError("len(engine) != l, while l is not None")
        elif l is None and not isinstance(engine, Sequence):
            raise ValueError("`l` is not specified, while `engine` is not a "
                             "sequence, hence `l` cannot be be inferred")
        if not isinstance(mutation_rate, float):
            raise ValueError("Mutation rate must be a float")

        self._engine = (engine if isinstance(engine, Sequence) else
                        [engine] * l)
        self._l = l if l else len(engine)
        self._mutation_rate = mutation_rate

        if starting_chr and self._l != len(starting_chr):
            raise ValueError(
                "`starting_chr`'s length doesn't match the number "
                "of features specified by `l` (or inferred from "
                "`len(engine)`)")
        # chromosome is a sequence of genes (features)
        self._chromosome = (tuple(starting_chr) if starting_chr else
                            tuple(gen(None) for gen in self._engine))

    def __eq__(self, other):
        """
        :type other: BaseIndividual
        """
        return self.chromosome == other.chromosome

    def __ne__(self, other):
        """
        :type other: BaseIndividual
        """
        return not self == other

    @property
    def engine(self):
        """
        :rtype: Sequence[Callable]
        """
        return self._engine

    @property
    def chromosome(self):
        """
        :rtype: tuple[Any]
        """
        return self._chromosome

    @property
    def mutation_rate(self):
        """
        :rtype: float
        """
        return self._mutation_rate

    @staticmethod
    def _mutate(mutation_rate, chromosome, engine):
        """
        :type mutation_rate: float
        :param mutation_rate: the probability of mutation per gene
        :type chromosome: Sequence
        :param chromosome: a sequence of genes (features)
        :rtype: list[Any]
        :return: a mutated chromosome
        """
        mutation_mask = np.random.binomial(1, mutation_rate, len(chromosome))
        return [gen(val) if mutate else val for (val, mutate, gen) in
                list(zip(chromosome, mutation_mask, engine))]

    @staticmethod
    def _crossover(chr1, chr2):
        """
        :type chr1: Sequence
        :type chr2: Sequence
        :rtype: list
        """
        if len(chr1) != len(chr2):
            raise ValueError("Incompatible species can't mate")
        choice_mask = np.random.binomial(1, 0.5, len(chr1))
        return [a if ch else b for (a, b, ch) in zip(choice_mask, chr1, chr2)]

    def replicate(self):
        return self._mutate(self.mutation_rate, self.chromosome, self.engine)

    def mate(self, other):
        """
        :type other: BaseIndividual
        """
        offspring_chr = self._crossover(self.replicate(),
                                        other.replicate())

        return type(self)(mutation_rate=self._mutation_rate,
                          engine=self._engine, l=self._l,
                          starting_chr=offspring_chr)


class Population(object):
    """
    :type _evaluated_ancestors: list[(Any, BaseIndividual)]
    :type _legends: list[(Any, BaseIndividual)]
    :type _fitness_func: (BaseIndividual) -> Any
    """
    modes = ("maximize", "minimize")

    def __init__(self, ancestors, size, fitness_function, mode="maximize",
                 n_legends=10):
        """
        :type ancestors: Sequence[BaseIndividual]
        :param ancestors: a bunch of individuals to begin with
        :type size: int
        :param size: population size
        :type fitness_function: (BaseIndividual) -> Any
        :param fitness_function: a callable that requires one argument - an
                                 instance of Individual - and returns an
                                 instance of a class that supports comparison
                                 operators, i.e. can be used to evaluate and
                                 compare fitness of different Individuals.
        :type n_legends: int
        :param n_legends: the number of the best individuals to remember
        :return:
        """
        if mode not in Population.modes:
            raise ValueError('`mode` must be `"maximize"` or `"minimize"`')

        if not isinstance(size, int) or size <= 0:
            raise ValueError("`size` must be a positive integer")

        if not isinstance(ancestors, Sequence) or not ancestors:
            raise ValueError("`ancestors` must be a nonempty sequence")

        if len(ancestors) < size:
            raise ValueError("At least `size` ancestors are required to start a"
                             "population")

        if not all(isinstance(indiv, BaseIndividual) for indiv in ancestors):
            raise ValueError("`ancestors` can only contain instances of"
                             "`Individual`")
        if not isinstance(n_legends, int) or n_legends <= 0:
            raise ValueError("`n_legends` must be a positive integer")

        self._maximize = mode == "maximize"
        self._ancestors = list(ancestors)
        self._size = size
        self._n_legends = n_legends
        self._legends = []

        try:
            if fitness_function(ancestors[0]) is None:
                raise ValueError(
                    "`fitness_function` mustn't return `NoneType` "
                    "values")
        except (TypeError, AttributeError):
            raise ValueError("Your `fitness_function` doesn't suit your"
                             "Idividuals")
        self._fitness_func = fitness_function
        # TODO get rid of the `evaluated_ancestors` attribute
        self._evaluated_ancestors = list(zip(map(self._fitness_func, ancestors),
                                         ancestors))

    @property
    def legends(self):
        """
        :rtype: list[(Any, BaseIndividual)]
        """
        return self._legends

    def _repopulate(self, evaluated_ancestors):
        """
        Mate ancestors to restore population size
        :type evaluated_ancestors: list[(Any, BaseIndividual)]
        :rtype: list[(Any, BaseIndividual)]
        """
        # generate all possible pairs of individuals and mate enough random
        # pairs to reach the desired population size
        individuals = [indiv for fitness, indiv in evaluated_ancestors]
        n_pairs = self._size - len(evaluated_ancestors)
        mating_pairs = random_pairs(individuals, n_pairs)
        evaluated_offsprings = map(self._mate_and_evaluate, mating_pairs)
        # evaluate offsprings and merge the result with `evaluated_ancestors`
        return op.iadd(list(evaluated_offsprings), evaluated_ancestors)

    def _mate_and_evaluate(self, mating_pair):
        indiv1, indiv2 = mating_pair
        offspring = indiv1.mate(indiv2)
        return self._fitness_func(offspring), offspring

    def _select(self, evaluated_population, n_fittest, n_random_unfit):
        """
        :type evaluated_population: list[(Any, BaseIndividual)]
        :param evaluated_population:
        :type n_fittest: int
        :param n_fittest:
        :type n_random_unfit: int
        :param n_random_unfit:
        :rtype: list[Any, BaseIndividual)]
        """
        # pick the most fittest and random lesser fit individuals
        ranked_pop = sorted(evaluated_population, reverse=self._maximize,
                            key=lambda x: x[0])
        fittest_survivors = ranked_pop[:n_fittest]
        random_unfit_survivors = random.sample(ranked_pop[n_fittest:],
                                               n_random_unfit)
        return fittest_survivors + random_unfit_survivors

    @staticmethod
    def _filter_duplicates_by_id(objects):
        """
        Filter duplicated references from a sequence. Utilises object ids.
        :type objects: Sequence[Any]
        :rtype: list[Any]
        """
        return {id(obj): obj for obj in objects}.values()

    def _update_legends(self, contenders):
        """
        :type contenders: list[(Any, BaseIndividual)]
        :rtype: None
        """
        # merge `contenders` with `self._legends`, sort again and strip to
        # `self._n_legends`
        # note: since `contenders` can contain some evaluated individuals from
        #       `legends` (if they managed to survive through the generations)
        #       we need to remove obvious duplicates by checking object ids
        self._legends = sorted(
            self._filter_duplicates_by_id(contenders + self._legends),
            key=lambda x: x[0], reverse=self._maximize)[:self._n_legends]

    def _run_generation(self, evaluated_ancestors, n_fittest, n_unfit):
        """
        Repopulate the population, apply selection, update the list of legends
        and return the survivors
        :type evaluated_ancestors: list[(Any, Individual)]
        :param n_fittest:
        :param n_unfit:
        :rtype: list[(Any, Individual)]
        """
        # repopulate, apply selection and update the hall of fame (legends)
        population = self._repopulate(evaluated_ancestors)
        selected_individuals = self._select(population, n_fittest, n_unfit)
        # note: since the list returned by `self._select` starts with the
        # fittest individuals we can pick contenders for the hall of fame
        # by slicing the first `self._n_legends` of `selected_individuals`
        self._update_legends(selected_individuals[:self._n_legends])
        return selected_individuals

    def evolve(self, n_gen, n_fittest, n_random_unfit):
        """
        :type n_gen: int
        :param n_gen: the number of generations
        :type n_fittest: int
        :param n_fittest: the number of the most fittest individuals to pick
                          for the next generation
        :type n_random_unfit: int
        :param n_random_unfit: the number of lesser fit individuals to pick at
                               random
        """
        if n_fittest < 0 or not isinstance(n_fittest, int):
            raise ValueError("`n_fittest` must be a nonzero integer")

        if n_random_unfit < 0 or not isinstance(n_random_unfit, int):
            raise ValueError("`n_unfit` must be a nonzero integer")

        if n_fittest + n_random_unfit > self._size:
            raise ValueError("Population size is too small to fit "
                             "`n_fittest` + `n_unfit`")
        current_generation = self._evaluated_ancestors

        for _ in range(n_gen):
            current_generation = self._run_generation(
                current_generation, n_fittest, n_random_unfit)
            yield self._legends


def random_pairs(sequence: Sequence, n: int):
    pairs = set()
    indices = list(range(len(sequence)))
    while len(pairs) != n:
        i, j = tuple(random.sample(indices, 2))
        if (i, j) in pairs or (j, i) in pairs:
            continue
        pairs.add((i, j))
    yield from ((sequence[i], sequence[j]) for i, j in pairs)


if __name__ == "__main__":
    raise RuntimeError