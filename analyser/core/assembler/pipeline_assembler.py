from __future__ import annotations
from analyser.core.deconstructor import PipelineDeconstructor, BACKTRACKING_EVENT, NEW_NODE_EVENT
from analyser.core.pipes import FillingPipe
from analyser.core.qa_rule import ExecutionContext
from analyser.logger.logger import LOG
from collections import deque
from .pipe_factory import PipeFactory
from typing import Deque, Dict
import typing

if typing.TYPE_CHECKING:
    from analyser.core import Pipe

class PipelineAssembler():
    """
        Get deconstruction informations from the 
        pipeline deconstructor and assembles the final pipeline.
    """
    def __init__(self, pipeline_specification: Dict, rule_name: str) -> None:
        self.rule_name = rule_name
        self.deconstructor: PipelineDeconstructor = PipelineDeconstructor(pipeline_specification, rule_name)
        self.deconstructor.subscribe_event(NEW_NODE_EVENT, self.on_new_node)
        self.deconstructor.subscribe_event(BACKTRACKING_EVENT, self.on_backtrack)
        self.first_pipe: Pipe = FillingPipe(None, None)
        self.nodes_history: Deque[Pipe] = deque()
        self.exec_context: ExecutionContext = ExecutionContext()
        self.exec_context.rule_name = rule_name

    def on_new_node(self, node: dict) -> None:
        """
            Raised by the deconstructor when a new node
            is reached.
        """
        if node['type'] ==  'ROOT_NODE':
            self.nodes_history.append(self.first_pipe)
        else:
            self.assemble_sub_pipeline_if_needed(node)
            pipe = PipeFactory.assemble_pipe(node, self.exec_context)
            #Plug the new pipe to the current last pipe of the deque
            self.nodes_history[-1].plug_pipe(pipe)
            LOG.info("Rule <%s> : Assembler -> %s plugged to %s", self.rule_name, pipe, self.nodes_history[-1])
            self.nodes_history.append(pipe)

    def assemble_sub_pipeline_if_needed(self, node_data: dict):
        """
            If the node_data contains a key starting with /SP\
            a sub pipeline is assembled with the data of this field.
        """
        for k in list(node_data):
            if k.startswith('/SP\\'):
                new_k = k[4:] #Remove the /SP\ prefix
                pipeline_specification = node_data.pop(k)
                node_data[new_k] = PipelineAssembler(pipeline_specification, self.rule_name).assemble()

    def on_backtrack(self, backtrack_amount: int) -> None:
        """
            Raised by the deconstructor when backtrack is
            processed through the tree.
        """
        for _ in range(backtrack_amount):
            if self.nodes_history:
                self.nodes_history.pop()

    def assemble(self) -> Pipe:
        """
            Assembles the full pipeline.
        """
        self.deconstructor.deconstruct()
        return self.first_pipe