import enum

class NodeType(enum.Enum):
    """Valid List types."""

    List = "LIST"
    """A List"""

    ListItem = "LIST_ITEM"
    """A List item"""


class Node:
    def __init__(self) -> None:
        self.parent
        self.id
        self.server_id
        self.parent_id
        self.type
        self._version
        self.text
        self.timestamp
        
        
    ...
    
class TopNode:
    ...

class ListItem:
    ...

class List:
    def add(self):
        ...
    
    def items(self):
        ...

    def checked(self):
        ...
    
    def unchecked(self):
        ...
    

    

