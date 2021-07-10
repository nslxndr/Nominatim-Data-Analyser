from __future__ import annotations
from analyser.logger.logger import LOG
from analyser.logger.timer import Timer
from analyser.core.yaml_logic.complex_value_parser import parse_complex_value
from typing import List
from analyser.core import Pipe
from geojson import Feature
import typing

if typing.TYPE_CHECKING:
    from analyser.core.qa_rule import ExecutionContext

class GeoJSONFeatureConverter(Pipe):
    """
        Handle the conversion of generic data class
        to geojson features.
    """
    def __init__(self, exec_context: ExecutionContext, properties_pattern: dict = None) -> None:
        super().__init__(exec_context)
        self.properties_pattern = properties_pattern

    def convert_to_geojson_feature(self, elements: dict, id: int) -> Feature:
        """
            Convert a query result to a geojson feature.
        """
        properties = dict()
        #If a custom propertie with the '$' syntax is used
        #find the corresponding name into the data record.
        if self.properties_pattern:
            for item in self.properties_pattern.items():
                parsed_value = parse_complex_value(item, elements)
                #A dictionnary is returned if there was a /?nwr?/ condition
                #else the tuple is returned.
                if isinstance(parsed_value, dict):
                    for k, v in parsed_value.items():
                        if k == 'Layer':
                            print(k)
                        properties[k] = v
                else:
                    properties[parsed_value[0]] = parsed_value[1]
        return elements.pop(0).to_geojson_feature(id, properties)

    def process(self, all_elements: List[dict]) -> List[Feature]:
        """
            Convert multiple elements
            to a list of features.
        """
        timer = Timer().start_timer()
        features = list()
        for i, elements in enumerate(all_elements):
            features.append(self.convert_to_geojson_feature(elements, i))
        LOG.info('Feature conversion executed in %s mins %s secs', *timer.get_elapsed())
        return features
    
    @staticmethod
    def create_from_node_data(data: dict, exec_context: ExecutionContext) -> GeoJSONFeatureConverter:
        """
            Assembles the pipe with the given node data.
        """
        properties = data['properties'] if 'properties' in data else None
        return GeoJSONFeatureConverter(exec_context, properties)