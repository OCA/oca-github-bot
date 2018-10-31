# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).


class EventMock:
    __slots__ = ["data"]

    def __init__(self, data):
        self.data = data
