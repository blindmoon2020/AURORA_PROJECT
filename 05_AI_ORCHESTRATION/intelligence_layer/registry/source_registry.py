class SourceRegistry:


    def __init__(self):

        self.sources = {}



    def register(
        self,
        name,
        category,
        weight
    ):

        self.sources[name] = {

            "category": category,
            "weight": weight,
            "status": "ACTIVE"

        }



    def get(self,name):

        return self.sources.get(name)



    def list_sources(self):

        return self.sources