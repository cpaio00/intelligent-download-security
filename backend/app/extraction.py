"""Reference feature extraction (thrember) in a separate, time- and memory-limited worker process.

A parse that hangs or exhausts memory kills only the worker; the pool is then rebuilt. Files are passed as bytes
and never written to disk or executed."""
import multiprocessing as mp
import sys

import numpy as np

_FE = None


def _init(memory_mb: int):
    global _FE
    if memory_mb and sys.platform.startswith("linux"):
        import resource
        lim = memory_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (lim, lim))
    import warnings
    warnings.filterwarnings("ignore")
    from thrember.features import PEFeatureExtractor
    _FE = PEFeatureExtractor()


def _extract(data: bytes):
    v = _FE.feature_vector(data)
    return np.asarray(v, dtype=np.float32)


class ExtractionError(Exception):
    def __init__(self, kind: str):
        super().__init__(kind)
        self.kind = kind          # "timeout" | "failed"


class Extractor:
    def __init__(self, timeout_s: float, memory_mb: int):
        self.timeout_s, self.memory_mb = timeout_s, memory_mb
        self._ctx = mp.get_context("spawn")
        self._pool = self._new_pool()

    def _new_pool(self):
        return self._ctx.Pool(1, initializer=_init, initargs=(self.memory_mb,), maxtasksperchild=200)

    def extract(self, data: bytes) -> np.ndarray:
        job = self._pool.apply_async(_extract, (data,))
        try:
            return job.get(timeout=self.timeout_s)
        except mp.TimeoutError:
            self._restart()
            raise ExtractionError("timeout")
        except Exception:
            raise ExtractionError("failed")

    def _restart(self):
        self._pool.terminate(); self._pool.join(); self._pool = self._new_pool()

    def close(self):
        self._pool.terminate(); self._pool.join()
