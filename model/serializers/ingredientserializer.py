import json
try:
    from lipgloss.core_data import Ingredient
except:
    from ..lipgloss.core_data import Ingredient
#import lipgloss
##from ..lipgloss.core_data import CoreData

class IngredientSerializer(object):
    """A class to support serializing/deserializing of a single ingredient and dictionaries of ingredients.  Needs improvement"""

    @staticmethod
    def get_serializable_ingredient(ingredient):
        """A serializable ingredient is one that can be serialized to JSON using the python json encoder."""
        serializable_ingredient = {}
        serializable_ingredient["name"] = ingredient.name
        serializable_ingredient["notes"] = ingredient.notes
        serializable_ingredient["analysis"] = ingredient.analysis
        serializable_ingredient["attributes"] = ingredient.attributes
        serializable_ingredient["glaze_calculator_ids"] = ingredient.glaze_calculator_ids
        return serializable_ingredient

    @staticmethod
    def serialize(ingredient):   # Not used
        """Serialize a single ingredient object to JSON."""
        return json.dumps(ingredientSerializer.get_serializable_ingredient(ingredient), indent=4)

    @staticmethod
    def serialize_dict(ingredient_dict):
        """Serialize a dict containing ingredient objects indexed by ID keys to JSON."""
        serializable_dict = {};
        for i in ingredient_dict:
            serializable_dict[i] = IngredientSerializer.get_serializable_ingredient(ingredient_dict[i])
        return serializable_dict  #json.dumps(serializable_dict, indent=4)

    @staticmethod
    def get_ingredient(serialized_ingredient_dict):
        """Convert a dict returned by the JSON decoder into a ingredient object."""
        ingredient = Ingredient(serialized_ingredient_dict["name"], 
                            serialized_ingredient_dict["notes"],
                            serialized_ingredient_dict["analysis"],
                            serialized_ingredient_dict["attributes"],
                            serialized_ingredient_dict["glaze_calculator_ids"]) 
        return ingredient
        
    @staticmethod
    def deserialize(json_str): # Not used
        """Deserialize a single ingredient from JSON to a ingredient object."""
        serialized_ingredient_dict = json.loads(json_str)
        return IngredientSerializer.get_ingredient(serialized_ingredient_dict)

    @staticmethod
    #def deserialize_dict(json_str):
    def deserialize_dict(serialized_ingredient_dict):
        """Deserialize a number of ingredients from JSON to a dict containing ingredient objects, indexed by ingredient ID."""
        ingredient_dict = {}
        #serialized_ingredients = json.loads(json_str)
        for i, serialized_ingredient in serialized_ingredient_dict.items():
            ingredient_dict[i] = IngredientSerializer.get_ingredient(serialized_ingredient)                           
        return ingredient_dict

    @staticmethod
    def get_ingredient_dict(path):
        """Return the dictionary of ingredients encoded in the JSON file at path"""
        with open(path) as json_file:
            return IngredientSerializer.deserialize_dict(json.load(json_file))

