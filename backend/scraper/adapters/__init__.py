from .gold_nutrition import GoldNutritionAdapter
from .myprotein import MyproteinAdapter
from .prozis import ProzisAdapter

ADAPTERS = {adapter.slug: adapter for adapter in [ProzisAdapter, MyproteinAdapter, GoldNutritionAdapter]}
