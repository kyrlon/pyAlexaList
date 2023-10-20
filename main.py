from datetime import datetime
from copy import deepcopy

class AlexaLists:

    def __init__(self):

        self.alexa_api = AlexaAPI()
        self.lists_and_items = {}
        self.initial_sync = True

    def getCurrentListsItems(self):
        if self.initial_sync:
            api_response = self.alexa_api.getListMetadata()
            for _list in api_response["lists"]:
                name_of_list = _list["name"] #TODO check if already in dict??
                list_id = _list["listId"]
                self.lists_and_items[name_of_list] = {"LIST_ID": list_id}
            for name_of_list in self.lists_and_items:
                _id = self.lists_and_items[name_of_list]["LIST_ID"]
                api_response = self.alexa_api.getList(_id)
                item_list = {
                    item["value"].capitalize(): {
                        "id": item["id"],
                        "status": item["status"],
                        "createdTime": item["createdTime"],
                        "updatedTime": item["updatedTime"],
                        "version" : item["version"]
                    }
                    for item in api_response["items"]
                }
                self.lists_and_items[name_of_list]["CURRENT_ITEMS_METADATA"] = item_list #TODO check if matches prev items??
                # self.lists_and_items[name_of_list]["ITEMS"] = {str(num):{"item_name":k.capitalize().strip(), "isDONE":v["status"]=="completed", "timestamp":datetime.strptime(v["createdTime"], "%a %b %d %H:%M:%S %Z %Y")} for num, (k,v) in enumerate(item_list.items()) }
                self.lists_and_items[name_of_list]["ITEMS"] = [{"item_name":k.capitalize().strip(), "isDONE":v["status"]=="completed", "timestamp":datetime.strptime(v["createdTime"], "%a %b %d %H:%M:%S %Z %Y"), "id":v["id"]} for num, (k,v) in enumerate(item_list.items())]
        else:
            for name_of_list in self.lists_and_items:
                _id = self.lists_and_items[name_of_list]["LIST_ID"]
                api_response = self.alexa_api.getList(_id)
                item_list = {
                    item["value"].capitalize(): {
                        "id": item["id"],
                        "status": item["status"],
                        "createdTime": item["createdTime"],
                        "updatedTime": item["updatedTime"],
                        "version" : item["version"]
                    }
                    for item in api_response["items"]
                }
                self.lists_and_items[name_of_list]["CURRENT_ITEMS_METADATA"] = item_list #TODO check if matches prev items??
                # self.lists_and_items[key]["ITEMS_METADATA"] = item_list #TODO check if matches prev items??
                # self.lists_and_items[key]["ITEMS"] = {str(num):{"item_name":k.capitalize().strip(), "isDONE":v["status"]=="completed", "timestamp":datetime.strptime(v["createdTime"], "%a %b %d %H:%M:%S %Z %Y")} for num, (k,v) in enumerate(item_list.items()) }
                _items = [{"item_name":k.capitalize().strip(), "isDONE":v["status"]=="completed", "timestamp":datetime.strptime(v["createdTime"], "%a %b %d %H:%M:%S %Z %Y"), "id":v["id"]} for num, (k,v) in enumerate(item_list.items())]


                a = iter(self.lists_and_items[name_of_list]["ITEMS"])
                b = iter(_items)

                item_a = next(a)
                item_b = next(b)
                done_looping = False
                while not done_looping:
                    try:
                        if item_a["item_name"] != item_b["item_name"]:
                            if any(item_b["item_name"] in d.values() for d in self.lists_and_items[name_of_list]["ITEMS"]):
                                _index = [i for i,v in enumerate(self.lists_and_items[name_of_list]["ITEMS"]) if v["item_name"] == item_b["item_name"]][0]
                                _a_item = self.lists_and_items[name_of_list]["ITEMS"][_index]
                                if _a_item["isDONE"] != item_b["isDONE"] and _a_item["timestamp"] < item_b["timestamp"]:
                                        self.lists_and_items[name_of_list]["ITEMS"][_index] = item_b
                            else:
                                if any(item_b["id"] in d.values() for d in self.lists_and_items[name_of_list]["ITEMS"]):
                                    _index = [i for i,v in enumerate(self.lists_and_items[name_of_list]["ITEMS"]) if v["id"] == item_b["id"]][0]
                                    _a_item = self.lists_and_items[name_of_list]["ITEMS"][_index]
                                    if _a_item["timestamp"] < item_b["timestamp"]:
                                        item_b["sync_id"] = self.lists_and_items[name_of_list]["ITEMS"][_index]["sync_id"]
                                        self.lists_and_items[name_of_list]["ITEMS"][_index] = item_b
                            item_b = next(b)
                        else:
                            if item_a["isDONE"] != item_b["isDONE"] and item_a["timestamp"] < item_b["timestamp"]:
                                _index = [i for i,v in enumerate(self.lists_and_items[name_of_list]["ITEMS"]) if v["item_name"] == item_b["item_name"]][0]
                                item_b["sync_id"] = self.lists_and_items[name_of_list]["ITEMS"][_index]["sync_id"]
                                self.lists_and_items[name_of_list]["ITEMS"][_index] = item_b
                            item_a = next(a)
                            item_b = next(b)
                    except StopIteration as e:
                        #good point that either one will cause this exception
                        done_looping = True
            print()


    def removeListEntry(self, name_of_list: str, item_txt: str):
        item_txt = item_txt.capitalize()
        list_id = self.lists_and_items[name_of_list]["LIST_ID"]
        item_id = self.lists_and_items[name_of_list]["ITEMS"][item_txt.capitalize()]["id"]
        version_num = self.lists_and_items[name_of_list]["ITEMS"][item_txt.capitalize()]["version"]

        item_info = self.alexa_api.updateListItem(list_id, item_id, item_txt, version_num)
        self.lists_and_items[name_of_list]["ITEMS"].pop(item_txt, None)
        self.lists_and_items[name_of_list]["CURRENT_LISTOBJECT_OF_ITEMS"]["UNCHECKED"].remove(item_txt.capitalize())
        self.lists_and_items[name_of_list]["CURRENT_LISTOBJECT_OF_ITEMS"]["CHECKED"].append(item_txt)

        self.lists_and_items[name_of_list]["ITEMS"].update(
            {
                item_info["value"].capitalize(): {
                    "id": item_info["id"],
                    "status": item_info["status"],
                    "createdTime": item_info["createdTime"],
                    "updatedTime": item_info["updatedTime"],
                    "version" : item_info["version"]
                }
            }
        )

    def addListEntry(self, name_of_list: str, item_txt: str):
        list_id = self.lists_and_items[name_of_list]["LIST_ID"]
        item_info = self.alexa_api.createListItem(list_id, item_txt)
        self.lists_and_items[name_of_list]["ITEMS"].update(
            {
                item_info["value"].capitalize(): {
                    "id": item_info["id"],
                    "status": item_info["status"],
                    "createdTime": item_info["createdTime"],
                    "updatedTime": item_info["updatedTime"],
                    "version" : item_info["version"]
                }
            }
        )
        self.lists_and_items[name_of_list]["CURRENT_LISTOBJECT_OF_ITEMS"]["UNCHECKED"].append(item_txt.capitalize())

    def syncList(self, name_of_list: str, incoming_items):
        _incoming_items = deepcopy(incoming_items)
        # self.initial_sync = initial_sync
        if self.initial_sync:
            self.lists_and_items[name_of_list]["ITEMS_PRV"] = {"list":self.lists_and_items[name_of_list]["ITEMS"] , "metadata": self.lists_and_items[name_of_list]["CURRENT_ITEMS_METADATA"]}
            self.clearList(name_of_list)
            list_id = self.lists_and_items[name_of_list]["LIST_ID"]
            for item in _incoming_items:
                _item_info = self.alexa_api.createListItem(list_id, item)
                # item["unique_id"][1] = _item_info["id"]
            self.lists_and_items[name_of_list]["ITEMS"] = _incoming_items
        else:
            self.lists_and_items[name_of_list]["ITEMS_PRV"] = self.lists_and_items[name_of_list]["ITEMS"] 
            # self.clearList(name_of_list)

            a = iter(self.lists_and_items[name_of_list]["ITEMS"])
            b = iter(incoming_items)

            item_a = next(a)
            item_b = next(b)
            done_looping = False
            list_id = self.lists_and_items[name_of_list]["LIST_ID"]
            while not done_looping:
                try:
                    if item_a["item_name"] != item_b["item_name"]:
                        if any(item_b["item_name"] in d.values() for d in self.lists_and_items[name_of_list]["ITEMS"]):
                            _index = [i for i,v in enumerate(self.lists_and_items[name_of_list]["ITEMS"]) if v["item_name"] == item_b["item_name"]][0]
                            _a_item = self.lists_and_items[name_of_list]["ITEMS"][_index]
                            if _a_item["isDONE"] != item_b["isDONE"] and _a_item["timestamp"] < item_b["timestamp"]:
                                    item_b["id"] = _a_item["id"]
                                    item_b["sync_id"] = self.lists_and_items[name_of_list]["ITEMS"][_index]["sync_id"]
                                    r_id = self.lists_and_items[name_of_list]["CURRENT_ITEMS_METADATA"][_a_item["item_name"]]["id"]
                                    r_version = self.lists_and_items[name_of_list]["CURRENT_ITEMS_METADATA"][_a_item["item_name"]]["version"]
                                    r_item_name = item_b["item_name"]


                                

                                    self.lists_and_items[name_of_list]["ITEMS"][_index] = item_b
                                    self.alexa_api.updateListItem(list_id, r_id, r_item_name, r_version)
                                    print("break_point_here11111111111")
                        else:
                            if any(item_b["id"] in d.values() for d in self.lists_and_items[name_of_list]["ITEMS"]):
                                _index = [i for i,v in enumerate(self.lists_and_items[name_of_list]["ITEMS"]) if v["id"] == item_b["id"]][0]
                                _a_item = self.lists_and_items[name_of_list]["ITEMS"][_index]
                                if _a_item["timestamp"] < item_b["timestamp"]:
                                    item_b["sync_id"] = self.lists_and_items[name_of_list]["ITEMS"][_index]["sync_id"]
                                    self.lists_and_items[name_of_list]["ITEMS"][_index] = item_b
                                    r_id = self.lists_and_items[name_of_list]["CURRENT_ITEMS_METADATA"][_a_item["item_name"]]["id"]
                                    r_version = self.lists_and_items[name_of_list]["CURRENT_ITEMS_METADATA"][_a_item["item_name"]]["version"]
                                    r_item_name = item_b["item_name"]


                                

                                    self.lists_and_items[name_of_list]["ITEMS"][_index] = item_b
                                    self.alexa_api.updateListItem(list_id, r_id, r_item_name, r_version)
                                    print("break_point_here22222")
                            else:
                                print("somethinf here...")

                        item_b = next(b)
                    else:
                        if item_a["isDONE"] != item_b["isDONE"] and item_a["timestamp"] < item_b["timestamp"]:
                            _index = [i for i,v in enumerate(self.lists_and_items[name_of_list]["ITEMS"]) if v["item_name"] == item_b["item_name"]][0]
                            item_b["sync_id"] = self.lists_and_items[name_of_list]["ITEMS"][_index]["sync_id"]
                            r_id = self.lists_and_items[name_of_list]["CURRENT_ITEMS_METADATA"][_a_item["item_name"]]["id"]
                            r_version = self.lists_and_items[name_of_list]["CURRENT_ITEMS_METADATA"][_a_item["item_name"]]["version"]
                            r_item_name = item_b["item_name"]


                        

                            self.lists_and_items[name_of_list]["ITEMS"][_index] = item_b
                            self.alexa_api.updateListItem(list_id, r_id, r_item_name, r_version)
                        item_a = next(a)
                        item_b = next(b)
                except StopIteration as e:
                    #good point that either one will cause this exception
                    done_looping = True
         


            

    def clearDoneCompleted(self, name_of_list: str):
        items_to_remove = []
        list_id = self.lists_and_items[name_of_list]["LIST_ID"]
        for item_name, item_info in self.lists_and_items[name_of_list]["ITEMS"].items():
            if item_info["status"] == "completed":
                self.alexa_api.deleteListItem(list_id, item_info["id"])
                items_to_remove.append(item_name)
        
        for k in items_to_remove:
            self.lists_and_items[name_of_list]["ITEMS"].pop(k, None)
        self.lists_and_items[name_of_list]["CURRENT_LISTOBJECT_OF_ITEMS"]["CHECKED"] = []

    def clearList(self, name_of_list: str):
        self.lists_and_items[name_of_list]["ITEMS"]
        list_id = self.lists_and_items[name_of_list]["LIST_ID"]
        for item_info in self.lists_and_items[name_of_list]["ITEMS"]:
                self.alexa_api.deleteListItem(list_id, item_info["id"])
