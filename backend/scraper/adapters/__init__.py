from .prozis import ProzisAdapter

ADAPTERS = {adapter.slug: adapter for adapter in [ProzisAdapter]}
