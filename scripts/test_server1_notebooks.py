#!/usr/bin/env python3
"""Execute Cookbook notebook queries against an explicit disposable native server.

Notebook cells and queries are executed unchanged. Network assets resolve to
tracked repository fixtures, package-install commands are disabled, and only
embedding providers are replaced with deterministic vectors. This checks query
compatibility and cleanup, not the semantic quality of a model's rankings.
"""
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from io import BytesIO
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from threading import Lock
from types import ModuleType, SimpleNamespace
import urllib.parse
import urllib.request
import uuid

SOURCE = Path(__file__).resolve().parents[1]
NOTEBOOKS = [
    "QuickStart", "Indexing", "Loading_CSVParsers", "Loading_DataModels",
    "Loading_QueryGenerator", "Entities", "Images", "Blobs", "Connections",
    "Operations", "Regions", "Videos", "ClipsFrames", "Embeddings",
    "VectorSearch", "AudioVectorSearch", "BulkEmbeddings", "HybridSearch",
    "ImageVectorSearch", "TextSearch", "PDF", "VideoVectorSearch", "SPARQL",
]


class FixtureSentenceTransformer:
    def __init__(self, model_name, **kwargs):
        self.dimensions = 512 if "clip" in model_name.lower() else 384

    def get_sentence_embedding_dimension(self):
        return self.dimensions

    def encode(self, values, normalize_embeddings=False, **kwargs):
        import numpy as np
        from PIL import Image

        single = isinstance(values, (str, Image.Image))
        vectors = []
        for value in [values] if single else list(values):
            payload = value.tobytes() if isinstance(value, Image.Image) else str(value).encode()
            seed = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
            vector = np.random.default_rng(seed).normal(size=self.dimensions).astype(np.float32)
            if normalize_embeddings:
                vector /= np.linalg.norm(vector)
            vectors.append(vector)
        result = np.stack(vectors)
        return result[0] if single else result


class NotebookRunner:
    def __init__(self, source, logs, pdf_text_fixture=None):
        self.source = source
        self.logs = logs
        self.pdf_text_fixture = pdf_text_fixture
        self.current = "fixture setup"
        self.queries = 0
        self.failures = []
        self.lock = Lock()

    def fixture_path(self, url):
        text = url.full_url if hasattr(url, "full_url") else str(url)
        parsed = urllib.parse.urlparse(text)
        prefix = "/aperture-data/Cookbook/"
        if parsed.netloc != "raw.githubusercontent.com" or not parsed.path.startswith(prefix):
            raise RuntimeError("Offline notebook check refused network request: " + text)
        relative = parsed.path[len(prefix):]
        relative = relative[len(
            "refs/heads/main/"):] if relative.startswith("refs/heads/main/") else relative.split("/", 1)[1]
        path = (self.source / urllib.parse.unquote(relative).replace(" ", "_")).resolve()
        if not path.is_relative_to(self.source.resolve()) or not path.is_file():
            raise RuntimeError("Missing tracked notebook fixture: " + relative)
        return path

    def urlopen(self, url, *args, **kwargs):
        response = BytesIO(self.fixture_path(url).read_bytes())
        response.headers = {}
        return response

    def request(self, session, method, url, **kwargs):
        import requests
        if method.upper() != "GET":
            raise RuntimeError("Unexpected offline network method: " + method)
        response = requests.Response()
        response.status_code = 200
        response.url = str(url)
        response._content = self.fixture_path(url).read_bytes()
        return response

    @contextmanager
    def offline_providers(self):
        import IPython.display
        import requests
        from aperturedb import CommonLibrary
        from aperturedb.Connector import Connector

        provider = ModuleType("sentence_transformers")
        provider.SentenceTransformer = FixtureSentenceTransformer
        originals = (urllib.request.urlopen, requests.sessions.Session.request,
                     IPython.display.display, Connector.query, CommonLibrary._get_colab_secret)
        modules = {name: sys.modules.get(name) for name in ("sentence_transformers", "pypdf")}
        sys.modules["sentence_transformers"] = provider
        if self.pdf_text_fixture is not None:
            pdf_text = self.pdf_text_fixture.read_text()
            pdf = ModuleType("pypdf")

            class FixturePdfReader:
                def __init__(self, filename):
                    if not Path(filename).read_bytes().startswith(b"%PDF-"):
                        raise ValueError("Expected the tracked PDF fixture")
                    self.pages = [SimpleNamespace(extract_text=lambda value=part: value)
                                  for part in pdf_text.split("\f") if part.strip()]

            pdf.PdfReader = FixturePdfReader
            sys.modules["pypdf"] = pdf

        def checked_query(client, *args, **kwargs):
            try:
                response, blobs = originals[3](client, *args, **kwargs)
                if not isinstance(response, list) or any(
                        next(iter(command.values())).get("status") not in (0, 2)
                        for command in response):
                    raise RuntimeError(f"{self.current}: native command failed: {response}")
            except Exception as error:
                with self.lock:
                    self.failures.append((self.current, str(error)))
                raise
            with self.lock:
                self.queries += 1
            return response, blobs

        urllib.request.urlopen = self.urlopen
        requests.sessions.Session.request = lambda session, method, url, **kwargs: self.request(
            session, method, url, **kwargs)
        IPython.display.display = lambda *args, **kwargs: None
        CommonLibrary._get_colab_secret = lambda name: None
        Connector.query = checked_query
        try:
            yield
        finally:
            (urllib.request.urlopen, requests.sessions.Session.request,
             IPython.display.display, Connector.query, CommonLibrary._get_colab_secret) = originals
            for name, module in modules.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module

    @contextmanager
    def sparql_fixture(self):
        import numpy as np
        from aperturedb.CommonLibrary import create_connector
        from aperturedb.Utils import Utils

        client = create_connector()
        utils = Utils(client)
        run_id = "sparql-notebook-" + uuid.uuid4().hex
        scope = ["$documentation_run", "==", run_id]
        definitions = utils.get_indexes(target="descriptor", class_name="ViT-B/16", property_key="_blob")
        created = not definitions
        try:
            if created:
                assert utils.create_vector_index("ViT-B/16", 512, ["L2", "CS"], {"flat": {}})
            elif definitions[0]["params"]["dimensions"] != 512:
                raise ValueError("The SPARQL fixture requires a 512-dimensional ViT-B/16 class")
            properties = {"documentation_run": run_id}
            client.query([
                {"AddImage": {"class": "Images", "_ref": 1, "properties": {
                    **properties, "caption": "chicken with butter", "dish_name": "Butter chicken"}}},
                {"AddEntity": {"class": "Ingredient", "_ref": 2,
                               "properties": {**properties, "name": "chicken"}}},
                {"AddEntity": {"class": "Ingredient", "_ref": 3,
                               "properties": {**properties, "name": "butter"}}},
                {"AddConnection": {"class": "HasIngredient", "src": 1, "dst": 2}},
                {"AddConnection": {"class": "HasIngredient", "src": 1, "dst": 3}},
                {"AddDescriptor": {"class": "ViT-B/16", "properties": properties,
                                   "connect": {"ref": 1, "class": "has_embedding"}}},
            ], [(self.source / "images/004_Large.jpeg").read_bytes(),
                np.random.default_rng(0).random(512).astype(np.float32).tobytes()])
            yield
        finally:
            client.query([
                {"DeleteDescriptor": {"with_class": "ViT-B/16", "constraints": scope}},
                {"DeleteImage": {"with_class": "Images", "constraints": scope}},
                {"DeleteEntity": {"with_class": "Ingredient", "constraints": scope}},
            ])
            if created:
                assert utils.remove_descriptorset("ViT-B/16")
            utils.client.close()
            client.close()

    def run_notebook(self, name):
        from IPython.core.interactiveshell import InteractiveShell

        notebook = next((self.source / "notebooks").rglob(name + ".ipynb"))
        before = self.queries
        failure_before = len(self.failures)
        with tempfile.TemporaryDirectory(prefix="cookbook-v1-" + name + "-") as temporary:
            work = Path(temporary)
            shutil.copytree(self.source / "notebooks/simple/data", work / "data")
            (work / "images").symlink_to(self.source / "images", target_is_directory=True)
            previous = Path.cwd()
            shell = InteractiveShell(user_ns={})
            shell.system = lambda *args, **kwargs: None
            shell.run_line_magic = lambda *args, **kwargs: None
            shell.user_ns["get_ipython"] = lambda: shell
            try:
                os.chdir(work)
                with (self.logs / (name + ".log")).open("w") as log:
                    for index, cell in enumerate(json.loads(notebook.read_text())["cells"]):
                        if cell["cell_type"] != "code":
                            continue
                        self.current = name + ":cell" + str(index)
                        print(self.current, file=log, flush=True)
                        with redirect_stdout(log), redirect_stderr(log):
                            result = shell.run_cell("".join(cell["source"]), store_history=False)
                        error = result.error_before_exec or result.error_in_exec
                        if error:
                            raise RuntimeError(
                                f"{self.current}: {error}; see {self.logs / (name + '.log')}") from error
                    # ParallelLoader records worker errors instead of raising
                    # them in the cell. A rejected request must still fail the run.
                    if len(self.failures) != failure_before:
                        raise RuntimeError(
                            f"{name}: background native query failed; see {self.logs / (name + '.log')}")
            finally:
                client = shell.user_ns.get("client")
                if client is not None:
                    client.close()
                os.chdir(previous)
        print(f"PASS {name}: {self.queries - before} native transactions", flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebooks", nargs="*", choices=NOTEBOOKS)
    parser.add_argument("--port", type=int, help="Native port of an empty disposable local server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin")
    parser.add_argument("--log-dir", type=Path,
                        help="Keep per-notebook logs here (default: a temporary directory)")
    parser.add_argument("--pdf-text-fixture", type=Path,
                        help="Optional text extracted locally from ButterChicken.pdf; otherwise pypdf is required")
    args = parser.parse_args(argv)
    if args.port is not None:
        if not 1 <= args.port <= 65535:
            parser.error("--port must be between 1 and 65535")
        config = dict(host=args.host, port=args.port, username=args.username,
                      password=args.password, use_ssl=False)
    else:
        try:
            config = json.loads(os.environ["APERTUREDB_JSON"])
        except (KeyError, ValueError):
            parser.error("Provide --port or APERTUREDB_JSON for an explicit disposable native server")
    if not isinstance(config, dict):
        parser.error("APERTUREDB_JSON must be a configuration object")
    if config.get("use_rest"):
        parser.error("This harness requires a native TCP endpoint (use_rest=false)")
    if args.pdf_text_fixture is not None and not args.pdf_text_fixture.is_file():
        parser.error("--pdf-text-fixture must name an existing local text file")
    selected = args.notebooks or NOTEBOOKS
    if "PDF" in selected and args.pdf_text_fixture is None and importlib.util.find_spec("pypdf") is None:
        parser.error("Install pypdf, or pass --pdf-text-fixture with locally extracted fixture text")
    logs = args.log_dir or Path(tempfile.mkdtemp(prefix="cookbook-v1-logs-"))
    logs.mkdir(parents=True, exist_ok=True)
    os.environ.pop("APERTUREDB_KEY", None)
    os.environ["APERTUREDB_JSON"] = json.dumps(config)
    os.environ["ADB_LOG_FILE"] = ""
    runner = NotebookRunner(SOURCE, logs.resolve(), args.pdf_text_fixture)
    print("Notebook logs:", logs.resolve(), flush=True)
    with runner.offline_providers():
        for name in selected:
            if name == "SPARQL":
                with runner.sparql_fixture():
                    runner.run_notebook(name)
            else:
                runner.run_notebook(name)
    print(f"Completed {len(selected)} native-server notebook runs", flush=True)


if __name__ == "__main__":
    main()
