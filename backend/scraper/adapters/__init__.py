from .gold_nutrition import GoldNutritionAdapter
from .myprotein import MyproteinAdapter
from .prozis import ProzisAdapter
from .zumub import ZumubAdapter

ADAPTERS = {adapter.slug: adapter for adapter in [ProzisAdapter, MyproteinAdapter, ZumubAdapter, GoldNutritionAdapter]}
