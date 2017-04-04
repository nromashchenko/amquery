from typing import Callable, List
import itertools

import numpy as np
import pandas as pd
import scipy.spatial.distance

from amquery.core.distance.metrics import distances
from amquery.core.sample_map import SampleMap
from amquery.core.sample import Sample
from amquery.utils.ui import progress_bar
from amquery.utils.config import Config
from amquery.utils.benchmarking import measure_time


class PwMatrix:

    def __init__(self,
                 config: Config,
                 sample_map: SampleMap,
                 dataframe: pd.DataFrame,
                 distance_func: Callable):

        self.config = config
        self.__sample_map = sample_map
        self.__dataframe = dataframe
        self.__distfunc = distance_func

    @staticmethod
    @measure_time(enabled=True)
    def create(config: Config, sample_map: SampleMap):
        distributions = [x.kmer_index(config) \
                         for x in sample_map.samples]
        pairs = list(itertools.combinations(distributions, 2))
        distance_func = distances[config.dist.func]
        result = np.fromiter(itertools.starmap(distance_func, pairs),
                             dtype=float)
        matrix = scipy.spatial.distance.squareform(result)
        dataframe = pd.DataFrame(matrix,
                                 index=sample_map.labels,
                                 columns=sample_map.labels)

        return PwMatrix(config, sample_map, dataframe,
                        distances[config.dist.func])

    @staticmethod
    def load(config: Config):
        sample_map = SampleMap.load(config)
        dataframe = pd.read_csv(config.pwmatrix_path,
                                sep='\t')
        dataframe['id'] = dataframe.keys()
        dataframe = dataframe.set_index('id')
        distance_func = distances[config.dist.func]
        pwmatrix = PwMatrix(config,
                            sample_map,
                            dataframe,
                            distance_func)
        return pwmatrix

    def save(self):
        self.__dataframe.to_csv(self.config.pwmatrix_path,
                                sep='\t',
                                na_rep="N/A",
                                index=False)
        self.__sample_map.save()

    def add_sample(self, sample: Sample) -> Sample:
        if sample.name not in self.labels:
            initvalues = [np.nan for x in range(len(self.__dataframe))]
            self.__dataframe[sample.name] = pd.Series(
                initvalues,
                index=self.dataframe.index)
            self.__dataframe.loc[sample.name] = initvalues + [np.nan]
            self.__sample_map[sample.name] = sample

    def __getitem__(self, pair):
        a, b = pair

        for x in [a, b]:
            if x.name not in self.labels:
                self.add_sample(x)

        if np.isnan(self.dataframe[a.name][b.name]):
            value = self.__distfunc(a.kmer_index(self.config),
                                    b.kmer_index(self.config))

            self.__dataframe[a.name][b.name] = value

        return self.dataframe[a.name][b.name]

    @property
    def sample_map(self) -> SampleMap:
        return self.__sample_map

    @property
    def labels(self) -> List[str]:
        return self.__dataframe.columns

    @property
    def dataframe(self) -> pd.DataFrame:
        return self.__dataframe

    @property
    def matrix(self) -> np.ndarray:
        return self.__dataframe.as_matrix()

    @property
    def hasvalue(self, a: str, b: str) -> bool:
        return a in self.labels and b in self.labels
