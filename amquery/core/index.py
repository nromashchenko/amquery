"""
Main class of a metric index
"""

from amquery.core.biom import merge_biom_tables
from amquery.core.distance.factory import Factory as DistanceFactory
from amquery.core.preprocessing.factory import Factory as PreprocessorFactory
from amquery.core.sample import Sample
from amquery.core.storage.factory import Factory as StorageFactory
from amquery.core.refindex import ReferenceTree
from amquery.utils.benchmarking import measure_time
from amquery.utils.config import read_config, get_sample_dir
import scripts


class Index:
    def __init__(self, distance, preprocessor, storage, reference_tree):
        """
        :param distance: SampleDistance
        :param preprocessor: Preprocessor
        :param storage: MetricIndexStorage
        """
        self._distance = distance
        self._preprocessor = preprocessor
        self._storage = storage
        self._reference_tree = reference_tree

    def __len__(self):
        """
        :return: int 
        """
        return len(self._storage) if self._storage else 0

    @staticmethod
    def create(database_config):
        """
        :return: Index
        """
        distance = DistanceFactory.create(database_config)
        preprocessor = PreprocessorFactory.create(database_config)
        storage = StorageFactory.create(database_config)

        reference_tree = None
        #if 'rep_tree' in database_config:
        #    reference_tree = ReferenceTree.create(database_config)

        return Index(distance, preprocessor, storage, reference_tree)

    def save(self, database_config):
        database_name = database_config["name"]
        self.distance.save(database_name)
        self.storage.save(database_name)

    @staticmethod
    def _load(database_name):
        database_config = read_config()["databases"][database_name]
        distance = DistanceFactory.load(database_config)
        preprocessor = PreprocessorFactory.create(database_config)
        storage = StorageFactory.load(database_config)
        reference_tree = ReferenceTree.load(database_config)
        return distance, preprocessor, storage, reference_tree, database_config

    @staticmethod
    @measure_time(enabled=True)
    def load(database_name):
        distance, preprocessor, storage, reference_tree, database_config = Index._load(database_name)
        return Index(distance, preprocessor, storage, reference_tree), database_config

    def _reload(self):
        distance, preprocessor, storage, reference_tree, config = Index._load()
        self._distance = distance
        self._preprocessor = preprocessor
        self._storage = storage
        self._reference_tree = reference_tree

    @measure_time(enabled=True)
    def build(self, input_files, database_name):
        """
        :param input_files: Sequence[str]
        :return:
        """
        assert (len(input_files) == 1)
        input_file = input_files[0]

        sample_files = scripts.split_fasta(input_file, get_sample_dir(database_name))
        samples = [Sample(sample_file, database_name) for sample_file in sample_files]
        processed_samples = [self._preprocessor(sample) for sample in samples]
        self.distance.add_samples(processed_samples)
        self.storage.build(self.distance, processed_samples)

    def refine(self):
        raise NotImplementedError

    @measure_time(enabled=True)
    def add(self, input_files, database_config):
        """
        :param sample_files: Sequence[str]
        :param config: configparser.ConfigParser
        :return: None
        """
        #assert (len(input_files) == 1)
        #input_file = input_files[0]

        # update biom table if present
        #if database_config.has_option("distance", "biom_table"):
        #    master_table = database_config.get("distance", "biom_table")
        #    additional_table = database_config.get("additional", "biom_table")
        #    merge_biom_tables(master_table, additional_table)
        #    self._reload()

        database_name = database_config["name"]

        #samples = [Sample(sample_file) for sample_file in split_fasta(input_file, get_sample_dir())]
        samples = [Sample(sample_file, database_name) for sample_file in input_files]
        processed_samples = [self._preprocessor(sample) for sample in samples]

        self.distance.add_samples(processed_samples)
        self.storage.add_samples(processed_samples, self.distance)

    @measure_time(enabled=True)
    def search(self, sample_name, k, database_name):
        """
        :param sample_name: str 
        :param k: int
        :return: Tuple[Sequence[np.float], Sequence[np.str]]
        """

        if sample_name in self.distance.labels:
            processed_samples = [self.distance.sample_map[sample_name]]
        else:
            sample_files = scripts.split_fasta(sample_name, get_sample_dir(database_name))
            samples = [Sample(sample_file, database_name) for sample_file in sample_files]
            processed_samples = [self._preprocessor(sample) for sample in samples]

        return self.storage.find(self.distance, processed_samples[0], k)

    @property
    def distance(self):
        """
        :return: PairwiseDistance 
        """
        return self._distance

    @property
    def storage(self):
        """
        :return: Storage 
        """
        return self._storage

    @property
    def samples(self):
        """
        :return: Sequence[Sample]
        """
        return list(self.distance.sample_map.values())