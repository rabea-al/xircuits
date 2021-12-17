from xai_components.base import InArg, OutArg, InCompArg, Component

class HelloHyperparameter(Component):
    input_str: InArg[str]

    def __init__(self):
        self.done = False
        self.input_str = InArg.empty()

    def execute(self) -> None:
        input_str = self.input_str.value
        print("Hello, " + str(input_str))
        self.done = True

class CompulsoryHyperparameter(Component):
    input_str: InArg[str]
    comp_str: InCompArg[str]
    comp_int: InCompArg[int]

    def __init__(self):
        self.done = False
        self.input_str = InArg.empty()
        self.comp_str = InCompArg.empty()
        self.comp_int = InCompArg.empty()

    def execute(self) -> None:
        input_str = self.input_str.value
        comp_str = self.comp_str.value
        comp_int = self.comp_int.value
        print("Hello, " + str(input_str))
        print("I'm " + str(comp_str))
        print("Me " + str(comp_int))
        self.done = True

class HelloListTupleDict(Component):
    input_list: InArg[list]
    input_tuple: InArg[tuple]
    input_dict: InArg[dict]

    def __init__(self):
        self.done = False
        self.input_tuple = InArg.empty()
        self.input_list = InArg.empty()
        self.input_dict = InArg.empty()

    def execute(self) -> None:
        input_list = self.input_list.value if self.input_list.value else ""
        input_tuple = self.input_tuple.value if self.input_tuple.value else ""
        input_dict = self.input_dict.value if self.input_dict.value else ""
        
        print( "\nDisplaying List: ")
        print(input_list) 
        print("\nDisplaying Tuple: ")
        print(input_tuple)
        print("\nDisplaying Dict: ")
        print(input_dict)

        self.done = True