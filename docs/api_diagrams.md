# API Diagrams

## 1) API Route Map

```mermaid
flowchart TD
    A[Client] --> B[GET /]
    A --> C[GET /api/pairs]
    A --> D[GET /api/pairs/{product_id}]
    A --> E[GET /api/als/recommendations/{user_id}?top_k=12]
    A --> F[POST /api/als/refresh?top_k=12]
    A --> G[GET /db/isconnect]

    C -. read transactions .-> P[(Postgres)]
    D -. read transactions .-> P
    E -. read interactions on cache miss .-> P
    F -. force full rebuild from DB .-> P
    G --> P
```

## 2) Sequence: /api/pairs

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI main.py
    participant REDIS as RedisCacheService
    participant ARL as AssociationRulesMiner
    participant FILE as JsonFileCacheService
    participant REPO as ArlRepository
    participant PG as Postgres DB

    Client->>API: GET /api/pairs
    API->>REDIS: load(pairs_result)

    alt Redis cache exists
        REDIS-->>API: cached pairs
    else Redis cache miss
        API->>ARL: get_pairs()
        alt In-memory cache exists
            ARL-->>API: pairs
        else No in-memory cache
            ARL->>FILE: load_many(cache_paths)
            alt File cache exists
                ARL-->>API: pairs from file cache
            else No file cache
            ARL->>ARL: multiprocessing Pool over partitions
            loop each partition
                ARL->>REPO: get_transactions(postfix)
                REPO->>PG: SELECT ... FROM transactions_YYYY_MM
                PG-->>REPO: rows
                REPO-->>ARL: transactions
                ARL->>ARL: run apriori
                ARL->>FILE: save(partition_pairs_with_metrics)
            end
            ARL->>FILE: load_many(cache_paths)
            ARL->>ARL: deduplicate pairs (A,B)==(B,A)
            ARL-->>API: pairs
            end
        end
        API->>REDIS: save(pairs_result)
    end

    API-->>Client: status/message/data(unique pairs)
```

## 3) Sequence: /api/als/recommendations/{user_id}

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI main.py
    participant REDIS as RedisCacheService
    participant ALS as AlternatingLeastSquaresService
    participant REPO as AlsRepository
    participant PG as Postgres DB

    Client->>API: GET /api/als/recommendations/{user_id}?top_k
    API->>REDIS: load(als_user_id)

    alt Redis user cache exists
        REDIS-->>API: cached user recommendations
    else Redis user cache miss
        API->>ALS: get_recommendations(top_k)
        ALS->>ALS: check model artifacts (model/mappings/user_items)
        alt Artifacts exist
            ALS->>ALS: load artifacts
            ALS->>ALS: build recommendations from artifacts
            ALS-->>API: recommendations
        else Artifacts absent
            ALS->>ALS: validate GPU configuration
            alt GPU unavailable
                ALS-->>API: RuntimeError
                API-->>Client: error (gpu_unavailable)
            else GPU available
                ALS->>ALS: multiprocessing fetch by partitions
                loop each partition
                    ALS->>REPO: get_user_item_interactions(postfix)
                    REPO->>PG: SELECT ... FROM transactions_YYYY_MM
                    PG-->>REPO: rows
                    REPO-->>ALS: rows
                    ALS->>ALS: convert rows to DataFrame chunk
                end
                ALS->>ALS: build unified DataFrame
                ALS->>ALS: train ALS model
                ALS->>ALS: save artifacts
                ALS->>ALS: generate recommendations
                ALS-->>API: recommendations
            end
        end
    end

    API->>API: find target user_id in recommendations
    alt user found
        API->>REDIS: save(als_user_id)
        API-->>Client: success + user recommendations
    else user not found
        API-->>Client: error (user_not_found)
    end
```

## 4) Sequence: /api/als/refresh

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI main.py
    participant ALS as AlternatingLeastSquaresService

    Client->>API: POST /api/als/refresh?top_k
    API->>ALS: refresh_recommendations(top_k)
    ALS->>ALS: delete model artifacts
    ALS->>ALS: recompute full pipeline
    ALS-->>API: refreshed users_count
    API-->>Client: success + users_count
```

## 5) Sequence: /db/isconnect

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI main.py
    participant SVC as DbConnectionService
    participant REPO as DbInfoRepository
    participant DB as Postgres

    Client->>API: GET /db/isconnect
    API->>SVC: check_connection()
    SVC->>REPO: is_connected()
    REPO->>DB: open connection
    alt connection ok
        DB-->>REPO: success
        REPO-->>SVC: (True, message)
        SVC-->>API: payload
        API-->>Client: success
    else connection failed
        DB-->>REPO: exception
        REPO-->>SVC: (False, error)
        SVC-->>API: payload
        API-->>Client: error
    end
```
