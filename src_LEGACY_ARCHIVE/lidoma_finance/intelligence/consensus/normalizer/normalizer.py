class ResponseNormalizer:
    """
    Converts provider responses
    into canonical format.
    """


    def normalize(
        self,
        responses: list[dict],
    ) -> list[dict]:

        normalized = []


        for response in responses:

            normalized.append(

                {

                    "provider":
                        response.get(
                            "provider"
                        ),

                    "content":
                        response.get(
                            "content",
                            ""
                        ),

                }

            )


        return normalized