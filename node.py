import enum
import json
import time
import datetime


class NodeTimestamps:
    """Represents the timestamps associated with a :class:`TopLevelNode`."""

    TZ_FMT = "%a %b %d %H:%M:%S UTC %Y"

    def __init__(self, create_time: float | None = None) -> None:
        """Construct a timestamps container"""
        if create_time is None:
            create_time = time.time()

        self._created = self.int_to_dt(create_time)
        self._updated = self.int_to_dt(create_time)
        self._edited = None
        self._deleted = None

    def _load(self, raw: dict) -> None:
        self._created = self.str_to_dt(raw["createdTime"])
        self._updated = self.str_to_dt(raw["updatedTime"])
    
    def load(self, raw: dict) -> None:
    
        self._load(raw)

    def save(self, clean: bool = True) -> dict:
        """Save the timestamps container"""
        ret = super().save(clean)
        ret["created"] = self.dt_to_str(self._created)
        if self._deleted is not None:
            ret["deleted"] = self.dt_to_str(self._deleted)
        if self._trashed is not None:
            ret["trashed"] = self.dt_to_str(self._trashed)
        ret["updated"] = self.dt_to_str(self._updated)
        if self._edited is not None:
            ret["userEdited"] = self.dt_to_str(self._edited)
        return ret

    @classmethod
    def str_to_dt(cls, tzs: str) -> datetime.datetime:
        """Convert a datetime string into an object.

        Params:
            tsz: Datetime string.

        Returns:
            Datetime.
        """
        return datetime.datetime.strptime(tzs, cls.TZ_FMT).replace(
            tzinfo=datetime.timezone.utc
        )

    @classmethod
    def int_to_dt(cls, tz: float) -> datetime.datetime:
        """Convert a unix timestamp into an object.

        Params:
            ts: Unix timestamp.

        Returns:
            Datetime.
        """
        return datetime.datetime.fromtimestamp(tz, tz=datetime.timezone.utc)

    @classmethod
    def dt_to_str(cls, dt: datetime.datetime) -> str:
        """Convert a datetime to a str.

        Params:
            dt: Datetime.

        Returns:
            Datetime string.
        """
        return dt.strftime(cls.TZ_FMT)

    @classmethod
    def int_to_str(cls, tz: int) -> str:
        """Convert a unix timestamp to a str.

        Returns:
            Datetime string.
        """
        return cls.dt_to_str(cls.int_to_dt(tz))

    @property
    def created(self) -> datetime.datetime:
        """Get the creation datetime.

        Returns:
            Datetime.
        """
        return self._created

    @created.setter
    def created(self, value: datetime.datetime) -> None:
        self._created = value
        self._dirty = True
    
    @property
    def edited(self) -> datetime.datetime:
        """Get the user edited datetime.

        Returns:
            Datetime.
        """
        return self._edited

    @edited.setter
    def edited(self, value: datetime.datetime) -> None:
        self._edited = value
        self._dirty = True

    @property
    def deleted(self) -> datetime.datetime | None:
        """Get the deletion datetime.

        Returns:
            Datetime.
        """
        return self._deleted

    @deleted.setter
    def deleted(self, value: datetime.datetime) -> None:
        self._deleted = value
        self._dirty = True

    @property
    def updated(self) -> datetime.datetime:
        """Get the updated datetime.

        Returns:
            Datetime.
        """
        return self._updated

    @updated.setter
    def updated(self, value: datetime.datetime) -> None:
        self._updated = value
        self._dirty = True


class TimeStampsUpdater:
    """A mixin to add methods for updating timestamps."""

    def __init__(self) -> None:
        """Instantiate mixin"""
        self.timestamps: NodeTimestamps

    def touch(self, edited: bool = False) -> None:
        """Mark the node as dirty.

        Args:
            edited: Whether to set the edited time.
        """
        self._dirty = True
        dt = datetime.datetime.now(tz=datetime.timezone.utc)
        # self.timestamps.updated = dt
        if edited:
            self.timestamps.edited = dt

    @property
    def deleted(self) -> bool:
        """Get the deleted state.

        Returns:
            Whether this item is deleted.
        """
        return (
            self.timestamps.deleted is not None
            and self.timestamps.deleted > NodeTimestamps.int_to_dt(0)
        )

    def delete(self) -> None:
        """Mark the item as deleted."""
        self.timestamps.deleted = datetime.datetime.now(tz=datetime.timezone.utc)

    def undelete(self) -> None:
        """Mark the item as undeleted."""
        self.timestamps.deleted = None

class Node(TimeStampsUpdater):
    def __init__(self) -> None:
        create_time = time.time()
        self.list_id = None
        self._type = None
        self._version =""
        self._text = ""
        self.timestamps = NodeTimestamps(create_time)
    
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
    def __init__(self):
        super().__init__()
        self._checked = False
        self._text = ""
        self._item_id = ""
        self._href_url = ""
    
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
        #TODOlist id/ parent?????
        #TODOdecide on href
        self.timestamps.load(raw)
        self._href_url = raw["href"] + "??????"
        self.list_id = self.list_id if self.list_id else self._extract_list_id(raw["href"])
        self.item_id = raw["id"]
        # self.createdTime = raw["createdTime"]
        # self.updatedTime = raw["updatedTime"]
        self._text = raw["value"]
        self._version = raw["version"]
        #TODOplacement in list???
    
    def _extract_list_id(self, href):
        return href.split("/")[3]
    
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
    
    @property
    def dirty(self) -> bool:  # noqa: D102
        return super().dirty or self.labels.dirty or self.collaborators.dirty

if __name__ == "__main__":
    obj = ListItem()

    with open("misc_DONOTPUSH/alexa_shopping_list_items.json", "r") as file:
        temp = json.load(file)
    
    for item in temp["items"]:
        obj.load(item)
        break

    print()