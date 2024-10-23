import abc
import asyncio
from collections import namedtuple
from io import BytesIO
from typing import TypeVar
from PIL import Image, ImageDraw


Coordinates2D = namedtuple('Coordinates2D', 'x y')


# class Coordinates2D(_Coordinates2DNT):
#     pass


class BaseDrawingTemplate:

    async def _load_autocomplete_values(self):
        pass

    async def generate(self) -> BytesIO:
        self._init_assets()
        await self._load_autocomplete_values()
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func=self._generate)

    @abc.abstractmethod
    def _generate(self) -> BytesIO:
        raise NotImplementedError

    @abc.abstractmethod
    def _init_assets(self):
        self._init_fonts()

    @abc.abstractmethod
    def _init_fonts(self):
        pass


class DrawingTemplate(BaseDrawingTemplate):

    def __init__(self, background_image_path: str):
        self._image = Image.open(background_image_path)
        self._drawer = ImageDraw.Draw(self._image)


TicketTemplateT = TypeVar('TicketTemplateT', bound=BaseDrawingTemplate)


class MultipleImageDrawingTemplate(BaseDrawingTemplate):

    async def generate(self) -> list[BytesIO]:
        return await super().generate()  # type:ignore

    def _generate(self) -> list[BytesIO]:
        raise NotImplemented

    def _init_assets(self):
        super()._init_assets()
        self._init_images()
        self._init_drawers()

    def _init_drawers(self):
        """
        Init ImageDraw instances here
        :return:
        """
        raise NotImplemented

    def _init_images(self):
        """
        Init Image instances here
        :return:
        """
        raise NotImplemented
