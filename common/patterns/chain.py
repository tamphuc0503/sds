from __future__ import annotations
from abc import ABC, abstractmethod
import logging
import re

from common.utils.id import correlation_id
from common.utils.string import split_and_strip


class PipelineError(Exception):
    class Codes:
        LANGUAGES_NOT_FOUND = "language_not_found"
        LANGUAGES_TOO_MANY = "too_many_langues"

    def __init__(self, code: Codes, message):
        super().__init__(message)
        self.code = code


class PipelineReq:
    """A single of builder pattern"""

    def __init__(self, pdf_path) -> None:
        super().__init__()
        self.pdf_path = pdf_path
        self.correlation_id = correlation_id()
        self.data_chain = dict()

    def set_chain_data(self, pipeline, data):
        self.data_chain[pipeline] = data

    def get_data_pipeline(self, pipeline):
        """Get data model from a pipeline in chain.

        Args:
            pipeline (Classname): the class of a pipeline.

        Returns:
            _type_: _description_
        """
        return self.data_chain[pipeline.__name__]

    def set_pdf_doc(self, doc, paragraphs):
        self.doc = doc
        self.paragraphs = paragraphs


class Pipeline(ABC):
    PLUS = "+"
    """Using Chain of Responsibility pattern to work with pipeline.
    The output of pipeline is input of 1 pipeline
    """

    def __init__(self) -> None:
        self.prev_pipeline: Pipeline = None
        self.next_pipeline: Pipeline = None
        self.logger = logging.getLogger(type(self).__name__)
        self.logger.setLevel(logging.DEBUG)
        self.correlation_id = "N/A"
        super().__init__()

    @abstractmethod
    def _run(self, request: PipelineReq):
        # include __future__ for bypass reportUndefinedVariables issue in `next`
        pass

    def set_next(self, next_pipeline: Pipeline) -> Pipeline:
        if next_pipeline is None:
            raise TypeError("Pipeline must not None")

        self.next_pipeline = next_pipeline
        self.next_pipeline.prev_pipeline = self
        self.next_pipeline.set_correlation_id(self.correlation_id)
        return next_pipeline

    def chain(self, request: PipelineReq):
        self.set_correlation_id(request.correlation_id)
        res = self._run(request)
        request.set_chain_data(type(self).__name__, res)

        if self.next_pipeline:
            self.next_pipeline.set_correlation_id(request.correlation_id)
            return self.next_pipeline.chain(request=request)
        # should we wrap into a new dictionary?
        return request.data_chain

    def set_correlation_id(self, correlation_id):
        self.correlation_id = correlation_id

    def log_info(self, msg):
        self.logger.info(f"{self.correlation_id} - {self.__str__()}: {msg}")

    def __str__(self):
        return type(self).__name__


class RegexPipeline(Pipeline):
    def __init__(self, pattern) -> None:
        super().__init__()
        self.regex = re.compile(pattern)
        self.bucket = list()

    def extract_codes(self, line, bucket):
        matches = self.regex.findall(line)
        for m in matches:
            # this mean the line will contains + and have many match.
            if Pipeline.PLUS in m:
                m = str.join(Pipeline.PLUS, split_and_strip(m, Pipeline.PLUS))
            bucket.append(m.strip())
        return matches


class Chain:
    class NoopPipeline(Pipeline):
        pass

    def __init__(self, pipelines: list[Pipeline]) -> None:
        self.pipelines = pipelines

    def run(self, request: PipelineReq):
        pipeline = self._prepare_pipelines(self.pipelines)
        return pipeline.chain(request=request)

    def _prepare_pipelines(self, pipelines: list[Pipeline]):
        if len(self.pipelines) < 1:
            return

        current_pipeline = pipelines[0]
        for i in range(1, len(self.pipelines)):
            current_pipeline = current_pipeline.set_next(self.pipelines[i])

        return pipelines[0]
