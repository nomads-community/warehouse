from pathlib import Path
from .exceptions import InventoryError


class InventoryUpdater:
    """
    Load an inventory file and update from command line

    """

    def __init__(self, inventory_path: str):
        self.path = Path(inventory_path)
        self.dt = None
        self._load()

    def _load(self, verbose: bool = True) -> None:
        """
        Load the inventory

        """

        if not self.path.exists():
            raise InventoryError(f"Cannot find inventory at {self.path}.")

        self.dt = {}
        with open(self.path, "r") as inventory:
            for line in inventory:
                fields = line.split("\t")

                if not len(fields) == 2:
                    raise InventoryError(
                        f"Inventory must contain tab-separated fields. For inventory at {self.path}, failing to parse this line: {line}."
                    )

                name, description = fields
                self.dt[name] = description.strip()

        if verbose:
            print(f"  Found {len(self.dt)} item(s) in inventory.")

    def _write(self) -> None:
        """
        Write the inventory

        """

        with open(self.path, "w") as inventory:
            for name, descrip in self.dt.items():
                inventory.write(f"{name}\t{descrip}\n")

    def _already_included(self, entry_id: str) -> bool:
        """
        Is this entry already included in the inventory?

        """

        return entry_id in self.dt

    def _user_add(self, entry_id: str, verbose: bool = True) -> None:
        """
        Add an entry to the inventory based on the users input

        """

        entry_descrip = input(
            f"  Please provide a description for the inventory entry '{entry_id}': "
        )
        self.dt[entry_id] = entry_descrip

        if verbose:
            print("  Added the following row to the inventory:")
            print(f"  {entry_id}\t{entry_descrip}")

    def update(self, entry_id, verbose: bool = True) -> None:
        """
        Update the inventory with a new entry

        """

        assert self.dt is not None, "Must load inventory before updating."

        if self._already_included(entry_id):
            if verbose:
                print(f"  Found {entry_id} in inventory already.")
            return

        print(f"  Did not find {entry_id} in inventory.")
        self._user_add(entry_id)

        self._write()
