from prompt_toolkit import Application, CommandLineInterface, HTML, AbortAction
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import HSplit, VSplit, Window, FormattedTextControl
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.processors import PasswordProcessor
from prompt_toolkit.widgets import Box, TextArea, Frame

class ChatApp:
    def __init__(self):
        # Create input buffer
        self.input_buffer = Buffer()

        # Create chat display buffer
        self.chat_buffer = Buffer()

        # Create layout
        self.layout = HSplit([
            VSplit([
                Window(FormattedTextControl(self.get_chat_content), height=10, wrap_lines=True, scroll_offset=1),
                Window(FormattedTextControl(''), height=1),
                Frame(body=TextArea(buffer=self.input_buffer, wrap_lines=False),
                      footer=Box(body=FormattedTextControl('Press [Enter] to send')),
                      height=3)
            ], height=15),
        ])

        # Create application
        self.app = Application(
            layout=self.layout,
            buffers=[self.input_buffer, self.chat_buffer],
            key_bindings=self.key_bindings,
            mouse_support=True,
            full_screen=True,
        )

    def get_chat_content(self):
        return HTML(self.chat_buffer.text)

    def key_bindings(self, keys):
        if keys == '\n':
            # Enter key pressed, handle the message
            message = self.input_buffer.text
            self.chat_buffer.text += HTML(f'<b>You:</b> {message}<br>')
            self.input_buffer.text = ''
        return NotImplemented  # Return NotImplemented to pass the event to the next key binding

    def run(self):
        cli = CommandLineInterface(application=self.app, eventloop=self.app.eventloop)
        try:
            cli.run()
        except KeyboardInterrupt:
            pass

def main():
    chat_app = ChatApp()
    chat_app.run()

if __name__ == "__main__":
    main()
