#!/usr/bin/env python3

# a node is something on a scene that can display itself
# all sprites, windows, icons, images and so forth
# are kinds of nodes.

import pygame

from wargame.loader import Resources
from wargame.events import MessageType

import logging
logger = logging.getLogger(__name__)


class BaseNode:
    def __init__(self, rect):
        self.rect = rect
        # what messages to listen for?
        self.messages = []
        self.displayable = False
        self.image = None

    @property
    def minimium_size(self):
        """
        Basenodes have no image and thus no size
        """
        return [0, 0]

    def update(self, time_delta):
        pass

    def handle(self, message):
        # return False - we did not consume the event
        return False


class ImageNode(BaseNode):
    def __init__(self, rect, image):
        # rect gives the position and size
        super().__init__(rect)
        self.image = image
        self.tween = None
        self.tween_result = None
        self.visible = True
        self.displayable = True

    def update(self, time_delta):
        # needs to return the dirty rects
        self.tween_result = None
        if self.tween is None:
            return []
        self.tween_result = self.tween.update(self, time_delta)
        if self.tween_result.finished:
            # remove the tween
            self.tween = None
        return self.tween_result.dirty_rects

    def draw_dirty(self, rect, screen):
        if not self.visible:
            return
        # so first we say are we over that rect?
        # given a rect and a screen, update the screen
        rect = rect.clip(self.rect)
        if rect.size != 0:
            # we have a collision
            # work out what to copy from OUR image
            offset = pygame.Rect(rect.x - self.rect.x,
                                 rect.y - self.rect.y,
                                 rect.width,
                                 rect.height)
            screen.blit(self.image, rect, offset)

    @staticmethod
    def from_image(xpos, ypos, image):
        image = Resources.get_image(image)
        rect = pygame.Rect(xpos, ypos, image.get_width(), image.get_height())
        return ImageNode(rect, image)

    @staticmethod
    def from_surface(xpos, ypos, surface):
        rect = pygame.Rect(xpos, ypos, surface.get_width(), surface.get_height())
        return ImageNode(rect, surface)

    @staticmethod
    def from_colour(width, height, colour):
        image = Resources.colour_surface(width, height, colour)
        return ImageNode.from_surface(0, 0, image)


class ListenerNode(BaseNode):
    def __init__(self, messages, callback):
        # no image and no size
        super().__init__(pygame.Rect(0, 0, 0, 0))
        self.messages = messages
        self.callback = callback

    def handle(self, message):
        # return true to kill the signal
        return self.callback(message)


class TimerNode(BaseNode):
    def __init__(self, delay):
        """
        Set delay in milliseconds
        """
        BaseNode.__init__(self, pygame.Rect(0, 0, 0, 0))
        self.delay = delay
        self.timer_index = MessageType.get_index()
        # start the pygame timer
        self.timer = self.timer_index
        pygame.time.set_timer(self.timer, delay)

    def reset(self):
        """
        Turn off the timer
        """
        pygame.timer.set_timer(self.timer, 0)
        MessageType.release(self.timer_index)


class RegularEvent(TimerNode, ListenerNode):
    def __init__(self, delay, callback):
        TimerNode.__init__(self, delay)
        ListenerNode.__init__(self, [self.timer], callback)
