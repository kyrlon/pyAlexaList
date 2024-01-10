import enum
import json

class NodeType(enum.Enum):
    """Valid List types."""

    List = "LIST"
    """A List"""

    ListItem = "LIST_ITEM"
    """A List item"""


class Node:
    def __init__(self) -> None:
        create_time = time.time()
        self.parent
        self.id
        self.server_id
        self.parent_id
        self.type
        self._version
        self.text
        self.timestamp = "??????????????"
    
    @property
    def text(self) -> str:
        """Get the text value.

        Returns:
            Text value.
        """
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """Set the text value.

        Args:
            value: Text value.
        """
        self._text = value
        self.timestamps.edited = datetime.datetime.now(tz=datetime.timezone.utc) #way to check change????
        self.touch(True)
        
    # save???
        
    @property
    def version(self) -> int:
        """Get the node version.

        Returns:
            Version.
        """
        return self._version
    
    @property
    def new(self) -> bool:
        """Get whether this node has been persisted to the server.

        Returns:
            True if node is new.
        """
        return self.server_id is None

    @property
    def dirty(self) -> bool:  # noqa: D102 maybe vall modified???
        return (
            super().dirty
            or self.timestamps.dirty
            or self.annotations.dirty
            or self.settings.dirty
            or any(node.dirty for node in self.children)
        )

class ListItem(Node):
    ...
    def __init__(self):
        super().__init__()
        self._checked = False
        self.list_id = None
        self._text = ""
    
    @property
    def checked(self) -> bool:
        """Get the checked state.

        Returns:
            Whether this item is checked.
        """
        return self._checked

    @checked.setter
    def checked(self, value: bool) -> None:
        self._checked = value
        self.touch(True)

    
    def load(self, raw: dict) -> None:
        #list id/ parent?????
        self.list_id = self.list_id if not None else self._extract_list_id(raw["href"])
        self.id = raw["id"]
        self.createdTime = raw["createdTime"]
        self.updatedTime = raw["updatedTime"]
        self._text = raw["value"]
        self.version = raw["version"]
        #placement in list???
    
    def _extract_list_id(self, href):
        ...
    
    # def save???

    def __str__(self) -> str:
        return "{} {}".format(
            "☑" if self.checked else "☐",
            self.text,
        )
class List:
    def add(self):
        ...
    

    @property
    def children(self):
        ...

    @property
    def text(self) -> str:  # noqa: D102
        return "\n".join(str(node) for node in self.items)
    

    @property
    def version(self) -> int:
        """Get the node version.

        Returns:
            Version.
        """
        return self._version
    
    #sort number or placement

    def get(self, node_id: str) -> "Node | None":
        """Get child node with the given ID.

        Args:
            node_id: The node ID.

        Returns:
            Child node.
        """
        return self._children.get(node_id)
    

    def append(self, node: "Node", dirty: bool = True) -> "Node":
        """Add a new child node.

        Args:
            node: Node to add.
            dirty: Whether this node should be marked dirty.
        """
        self._children[node.id] = node
        node.parent = self
        if dirty:
            self.touch()

        return node

    def remove(self, node: "Node", dirty: bool = True) -> None:
        """Remove the given child node.

        Args:
            node: Node to remove.
            dirty: Whether this node should be marked dirty.
        """
        if node.id in self._children:
            self._children[node.id].parent = None
            del self._children[node.id]
        if dirty:
            self.touch()
    
    def load(self):
        ...

    @property
    def items(self) -> list[ListItem]:
        """Get all listitems.

        Returns:
            List items.
        """
        return self.sorted_items(self._items())

    @property
    def checked(self) -> list[ListItem]:
        """Get all checked listitems.

        Returns:
            List items.
        """
        return self.sorted_items(self._items(True))

    @property
    def unchecked(self) -> list[ListItem]:
        """Get all unchecked listitems.

        Returns:
            List items.
        """
        return self.sorted_items(self._items(False))


    
    @property
    def title(self) -> str:
        """Get the title.

        Returns:
            Title.
        """
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._title = value
        self.touch(True)
    
    @property
    def archived(self) -> bool:
        """Get the archive state.

        Returns:
            Whether this node is archived.
        """
        return self._archived

    @archived.setter
    def archived(self, value: bool) -> None:
        self._archived = value
        self.touch(True)

if __name__ == "__main__":
    obj = ListItem()

    with open("alexa_shopping_list_items.json", "r") as file:
        temp = json.load(file)
    
    for item in temp["items"]:
        obj.load(item)
        break

    print()