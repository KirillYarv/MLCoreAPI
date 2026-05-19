import glob
import json
import logging
from multiprocessing import Pool
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from implicit.als import AlternatingLeastSquares
from implicit.evaluation import mean_average_precision_at_k
from scipy.sparse import coo_matrix

from src.repository.AlsRepository import AlsRepository

logging.basicConfig(
    level=logging.INFO,
    filename="py_log.log",
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class AlternatingLeastSquaresService:
    """ALS-based recommendation service with file cache and multiprocessing."""

    def __init__(
        self,
        als_repo: AlsRepository,
        cache_dir: str = "",
        cache_prefix: str = "data_for_als",
        factors: int = 40,
        regularization: float = 0.01,
        iterations: int = 20,
        pool_processes: int = 3,
        use_gpu: bool = True,
    ) -> None:
        """Initialize ALS service with repository, cache and model hyperparameters.

        Args:
            als_repo: Repository for reading interaction data.
            cache_dir: Relative/absolute directory for JSON cache files.
            cache_prefix: Prefix for cache file names.
            factors: Number of latent factors in ALS model.
            regularization: L2 regularization coefficient.
            iterations: Number of ALS optimization iterations.
            pool_processes: Number of worker processes for DB reads.
            use_gpu: Enable GPU backend for ALS training.
        """
        self.als_repo = als_repo
        self.cache_dir = cache_dir
        self.cache_prefix = cache_prefix
        self.factors = factors
        self.regularization = regularization
        self.iterations = iterations
        self.pool_processes = pool_processes
        self.use_gpu = use_gpu
        self._cached_recommendations: List[Dict[str, Any]] = []
        self._last_map_at_k: float | None = None

        self.all_users_count: int = self.als_repo.get_count("customers", "customer_id")
        self.all_items_count: int = self.als_repo.get_count("articles", "article_id")

    def get_recommendations(self, top_k: int = 12) -> List[Dict[str, Any]]:
        """Return recommendations, using cache files when available.

        Args:
            top_k: Number of recommended items per user.

        Returns:
            List[Dict[str, Any]]: Recommendation records.
        """
        cache_paths = list(
            glob.glob(f"{self.cache_dir}{self.cache_prefix}_results*.json")
        )
        if not self._cached_recommendations:
            self._cached_recommendations = self._load_or_calculate(cache_paths, top_k)
        return self._cached_recommendations

    def _load_or_calculate(
        self, cache_paths: List[str], top_k: int
    ) -> List[Dict[str, Any]]:
        cached = self._load_cached_data(cache_paths)
        if cached:
            return cached
        return self._calculate_recommendations(top_k=top_k)

    def _load_cached_data(self, cache_paths: List[str]) -> List[Dict[str, Any]]:
        data: List[Dict[str, Any]] = []
        for cache_path in cache_paths:
            path = Path(cache_path)
            if not path.exists():
                continue
            try:
                with open(path, "r", encoding="utf-8") as file:
                    data.extend(json.load(file))
            except json.JSONDecodeError:
                continue
        return data

    def _get_repository_data(self, transactions_postfix: str) -> None:
        """Load interactions for one partition and persist them to cache.

        Args:
            transactions_postfix: Transactions table postfix, e.g. ``_2019_03``.
        """
        data = self.als_repo.get_user_item_interactions(transactions_postfix)
        self._save_to_cache(data, f"{self.cache_prefix}{transactions_postfix}.json")

    def _calculate_recommendations(self, top_k: int) -> List[Dict[str, Any]]:
        """Fetch interactions in parallel, then train ALS in one synchronized flow.

        Data loading is parallelized per partition with multiprocessing.
        Model training and recommendation generation are executed in a single process.

        Args:
            top_k: Number of recommendations per user.

        Returns:
            List[Dict[str, Any]]: Final recommendation payload.
        """
        self._validate_gpu_configuration()

        table_postfixes = [
            "_2019_11",
            "_2020_03",
            "_2020_05",
        ]

        with Pool(processes=self.pool_processes) as pool:
            fetch_start = perf_counter()
            pool.map(self._get_repository_data, table_postfixes)
            fetch_end = perf_counter()
            logging.info(
                "ALS data fetch multiprocessing completed in %.3f sec",
                fetch_end - fetch_start,
            )

        interactions_df = self._build_interactions_dataframe_from_cache(table_postfixes)
        if interactions_df.empty:
            self._save_to_cache([], f"{self.cache_prefix}_results.json")
            return []

        logging.info(f"built interactions_df shape: {interactions_df.shape}")

        interactions_df = self._filter_data(
            interactions_df, user_count=10, item_count=20
        )
        logging.info(f"filtered interactions_df shape: {interactions_df.shape}")

        recs = self._train_single_model(interactions_df=interactions_df, top_k=top_k)
        self._save_to_cache(recs, f"{self.cache_prefix}_results_all.json")

        return recs

    def _build_interactions_dataframe_from_cache(
        self,
        table_postfixes: List[str],
    ) -> pd.DataFrame:
        """Read cached partition files and build a single interactions DataFrame.

        Args:
            table_postfixes: List of table postfixes that define cache filenames.

        Returns:
            pd.DataFrame: Unified DataFrame with columns
                ``t_dat``, ``customer_id``, ``article_id``.
        """
        unified_df = pd.DataFrame(columns=["t_dat", "customer_id", "article_id"])
        unified_df["t_dat"] = pd.to_datetime(unified_df["t_dat"])

        for postfix in table_postfixes:
            path = Path(f"{self.cache_dir}{self.cache_prefix}{postfix}.json")
            if not path.exists():
                continue
            try:
                logging.info(f"reading cache file: {path}")
                with open(path, "r", encoding="utf-8") as file:
                    rows = json.load(file)
            except json.JSONDecodeError:
                continue

            logging.info("make dataframe")

            chunk_df = pd.DataFrame(
                rows,
                columns=["t_dat", "customer_id", "article_id"],
            )
            logging.info("change type dataframe")
            chunk_df["t_dat"] = pd.to_datetime(chunk_df["t_dat"])

            if chunk_df.empty:
                continue

            unified_df = pd.concat([unified_df, chunk_df], ignore_index=True)
            logging.info(f"cache file {path} loaded")

        logging.info("returning unified interactions_df shape: %s", unified_df.shape)
        return unified_df

    def _filter_data(
        self, df: pd.DataFrame, user_count=10, item_count=20
    ) -> pd.DataFrame:
        item_counts = df.groupby("article_id")["customer_id"].count()
        pop_items = item_counts[item_counts >= item_count]
        df = df[df["article_id"].isin(pop_items.index)]

        user_counts = df.groupby("customer_id")["article_id"].count()
        pop_users = user_counts[user_counts >= user_count]
        df = df[df["customer_id"].isin(pop_users.index)].copy()
        return df

    def _train_single_model(
        self,
        interactions_df: pd.DataFrame,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Train one ALS model on all synchronized interactions and produce recs.

        Args:
            interactions_df: Flattened interactions from all DB partitions.
            top_k: Number of recommendations per user.

        Returns:
            List[Dict[str, Any]]: Recommendation records per user.
        """
        logging.info("training single ALS model")
        train_start = perf_counter()

        model = AlternatingLeastSquares(
            factors=self.factors,
            regularization=self.regularization,
            iterations=self.iterations,
            use_gpu=self.use_gpu,
        )

        logging.info("codes interactions_df")

        user_codes = interactions_df["customer_id"].unique().tolist()
        item_codes = interactions_df["article_id"].unique().tolist()
        user_dict = dict(list(enumerate(user_codes)))
        item_dict = dict(list(enumerate(item_codes)))

        user_map = {u: idx for idx, u in user_dict.items()}
        item_map = {i: idx for idx, i in item_dict.items()}

        interactions_df["user_idx"] = interactions_df["customer_id"].map(user_map)
        interactions_df["item_idx"] = interactions_df["article_id"].map(item_map)

        matrix = self._to_user_item_coo(interactions_df).tocsr()

        logging.info("matrix shape: %s", matrix.shape)

        model.fit(matrix)
        logging.info("model fitted")

        self._last_map_at_k = self._evaluate_map_at_k(
            model=model,
            interactions_df=interactions_df,
            k=top_k,
        )
        logging.info("ALS MAP@%d: %.6f", top_k, self._last_map_at_k)

        logging.info("getting recommendations")

        test_users = (
            interactions_df["user_idx"].drop_duplicates().to_numpy(dtype=np.int32)
        )

        item_indices, scores = model.recommend(
            test_users,
            matrix[test_users],
            N=top_k,
            filter_already_liked_items=True,
        )

        recs_df = pd.DataFrame(
            {
                "user_idx": test_users,
                "item_idx": item_indices.tolist(),
                "score": scores.tolist(),
            }
        ).explode(["item_idx", "score"])

        user_idx_to_customer_id = {idx: user_id for idx, user_id in user_dict.items()}
        item_idx_to_article_id = {idx: item_id for idx, item_id in item_dict.items()}

        recs_df["customer_id"] = recs_df["user_idx"].map(user_idx_to_customer_id)
        recs_df["article_id"] = recs_df["item_idx"].map(item_idx_to_article_id)
        recs_df["score"] = recs_df["score"].astype(float)

        recs_by_user: List[Dict[str, Any]] = []
        for customer_id, group in recs_df.groupby("customer_id"):
            recommendations = [
                {
                    "article_id": int(row["article_id"]),
                    "score": float(row["score"]),
                }
                for _, row in group.iterrows()
                if pd.notna(row["article_id"])
            ]
            recs_by_user.append(
                {
                    "customer_id": customer_id,
                    "recommendations": recommendations,
                }
            )

        train_end = perf_counter()
        logging.info(
            "ALS single-process train/recommend completed in %.3f sec",
            train_end - train_start,
        )
        return recs_by_user

    def _evaluate_map_at_k(
        self,
        model: AlternatingLeastSquares,
        interactions_df: pd.DataFrame,
        k: int,
    ) -> float:
        """Compute MAP@K with per-user holdout split.

        For each user with at least 2 interactions, one item is sampled into test,
        the rest remain in train.
        """
        logging.info("MAP@K evaluation started")

        df_train, df_test = self._train_test_split_over(interactions_df)

        coo_train = self._to_user_item_coo(df_train)
        coo_test = self._to_user_item_coo(df_test)

        csr_train = coo_train.tocsr()
        csr_test = coo_test.tocsr()

        return float(
            mean_average_precision_at_k(
                model,
                csr_train,
                csr_test,
                K=k,
                show_progress=False,
            )
        )

    def _to_user_item_coo(self, df: pd.DataFrame) -> coo_matrix:
        """Turn a dataframe with transactions into a COO sparse items x users matrix"""
        row = df["user_idx"].values
        col = df["item_idx"].values
        data = np.ones(df.shape[0])

        coo = coo_matrix(
            (data, (row, col)), shape=(self.all_users_count, self.all_items_count)
        )
        return coo

    def _train_test_split_over(
        self,
        clickstream_df: pd.DataFrame,
        test_quantile: float = 0.8,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split clickstream by date.
        """
        clickstream_df = clickstream_df.sort_values(["customer_id", "t_dat"])

        test_timepoint = (
            clickstream_df["t_dat"]
            .drop_duplicates()
            .quantile(q=test_quantile, interpolation="nearest")
        )

        test = clickstream_df.query(f"{'t_dat'} >= @test_timepoint")
        train = clickstream_df.drop(test.index)

        test = test[test["customer_id"].isin(train["customer_id"])]
        test = test[test["article_id"].isin(train["article_id"])]

        test.reset_index(drop=True, inplace=True)
        train.reset_index(drop=True, inplace=True)

        return train, test

    def _validate_gpu_configuration(self) -> None:
        """Validate that GPU backend is available when GPU mode is enabled.

        Raises:
            RuntimeError: If GPU mode is requested but CUDA backend is unavailable.
        """
        if not self.use_gpu:
            return

        try:
            from implicit import gpu as implicit_gpu
        except Exception as error:
            raise RuntimeError(
                "GPU check failed: implicit GPU module is unavailable. "
                "Install CUDA-enabled dependencies and run container with GPU access."
            ) from error

        has_cuda = bool(getattr(implicit_gpu, "HAS_CUDA", False))
        if not has_cuda:
            raise RuntimeError(
                "GPU is required for ALS, but CUDA is not available. "
                "Install NVIDIA driver + CUDA runtime and start container with '--gpus all'."
            )

    def _save_to_cache(self, data: Any, file_name: str) -> None:
        """Persist recommendation data to JSON cache file."""
        path = Path(f"{self.cache_dir}{file_name}")
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, default=str)
