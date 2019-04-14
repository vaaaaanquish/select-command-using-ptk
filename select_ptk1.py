# -*- coding: utf-8 -*-
# ptk 1.x ver
from prompt_toolkit.application import Application
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.filters import IsDone
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.containers import ConditionalContainer
from prompt_toolkit.layout.containers import ScrollOffsets
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout.controls import TokenListControl
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.mouse_events import MouseEventTypes
from prompt_toolkit.shortcuts import create_eventloop
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token
import subprocess

choices = ['ls', 'ifconfig', 'pwd', 'who']
string_query = ' Command Select '
inst = ' (Use arrow keys)'


def selected_item(text):
    res = subprocess.call(text)
    print(res)


class InquirerControl(TokenListControl):
    selected_option_index = 0
    answered = False

    def __init__(self, choices, **kwargs):
        self.choices = choices
        super(InquirerControl, self).__init__(self._get_choice_tokens, **kwargs)

    @property
    def choice_count(self):
        return len(self.choices)

    def _get_choice_tokens(self, cli):
        tokens = []
        T = Token

        def append(index, label):
            selected = (index == self.selected_option_index)

            def select_item(cli, mouse_event):
                self.selected_option_index = index
                self.answered = True

            token = T.Selected if selected else T
            tokens.append((T.Selected if selected else T, ' > ' if selected else '   '))
            if selected:
                tokens.append((Token.SetCursorPosition, ''))
            tokens.append((T.Selected if selected else T, '%-24s' % label, select_item))
            tokens.append((T, '\n'))

        for i, choice in enumerate(self.choices):
            append(i, choice)
        tokens.pop()
        return tokens

    def get_selection(self):
        return self.choices[self.selected_option_index]

ic = InquirerControl(choices)


def get_prompt_tokens(cli):
    tokens = []
    T = Token
    tokens.append((Token.QuestionMark, '?'))
    tokens.append((Token.Question, string_query))
    if ic.answered:
        tokens.append((Token.Answer, ' ' + ic.get_selection()))
        selected_item(ic.get_selection())
    else:
        tokens.append((Token.Instruction, inst))
    return tokens

layout = HSplit([
    Window(height=D.exact(1),
           content=TokenListControl(get_prompt_tokens, align_center=False)),
    ConditionalContainer(
        Window(
            ic,
            width=D.exact(43),
            height=D(min=3),
            scroll_offsets=ScrollOffsets(top=1, bottom=1)
        ),
        filter=~IsDone())])


manager = KeyBindingManager.for_prompt()
@manager.registry.add_binding(Keys.ControlQ, eager=True)
@manager.registry.add_binding(Keys.ControlC, eager=True)
def _(event):
    event.cli.set_return_value(None)
@manager.registry.add_binding(Keys.Down, eager=True)
def move_cursor_down(event):
    ic.selected_option_index = (
        (ic.selected_option_index + 1) % ic.choice_count)
@manager.registry.add_binding(Keys.Up, eager=True)
def move_cursor_up(event):
    ic.selected_option_index = (
        (ic.selected_option_index - 1) % ic.choice_count)
@manager.registry.add_binding(Keys.Enter, eager=True)
def set_answer(event):
    ic.answered = True
    event.cli.set_return_value(None)


inquirer_style = style_from_dict({
    Token.QuestionMark: '#5F819D',
    Token.Selected: '#FF9D00',
    Token.Instruction: '',
    Token.Answer: '#FF9D00 bold',
    Token.Question: 'bold',
})


app = Application(
    layout=layout,
    key_bindings_registry=manager.registry,
    mouse_support=False,
    style=inquirer_style
)


eventloop = create_eventloop()
try:
    cli = CommandLineInterface(application=app, eventloop=eventloop)
    cli.run(reset_current_buffer=False)
finally:
    eventloop.close()
